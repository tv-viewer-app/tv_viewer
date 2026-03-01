"""Main application window with Windows 11 Fluent Design UI using ttkbootstrap."""

import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledFrame
from tkinter import ttk, messagebox
import tkinter as tk
from typing import Optional, Dict, Any, List
import gc
import time
import os

from core.channel_manager import ChannelManager
from utils.helpers import format_age_rating
from utils.thumbnail import capture_thumbnail_async, get_thumbnail_path, thumbnail_exists
from utils.favorites import FavoritesManager
from utils.logger import get_logger
from .player_window import PlayerWindow
from .scan_animation import ScanProgressFrame
from .constants import FluentColorsDark as FluentColors, FluentSpacing, FluentTypography
import config

# Get logger for this module
logger = get_logger(__name__)

# Try to import icon module
try:
    from icon import set_window_icon
except ImportError:
    set_window_icon = None

# Try to import PIL for thumbnail display
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class MainWindow:
    """Main application window with Windows 11 Fluent Design."""
    
    def __init__(self):
        # Initialize ttkbootstrap window with dark theme
        self.root = ttk_bs.Window(themename="darkly")
        self.root.title(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.root.minsize(800, 500)
        
        # Windows: debounce resize to prevent lag during drag
        self._resize_timer = None
        self.root.bind('<Configure>', self._on_resize)
        
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, minsize=280)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Set window icon
        if set_window_icon:
            set_window_icon(self.root)
        
        # Configure custom styles
        self.style = ttk_bs.Style()
        self.style.configure("TButton", font=("Segoe UI", 11))
        self.style.configure("TLabel", font=("Segoe UI", 11))
        self.style.configure("TCheckbutton", font=("Segoe UI", 10))
        
        # Channel manager
        self.channel_manager = ChannelManager()
        self._setup_callbacks()
        
        # Favorites manager
        self.favorites_manager = FavoritesManager()
        
        # Player window reference
        self.player_window: Optional[PlayerWindow] = None
        
        # Currently selected group and grouping mode
        self.current_group: Optional[str] = None
        self.group_by_mode = 'category'
        
        # Filter options
        self.hide_checking = False
        self.hide_failed = True  # Hide dead channels by default
        
        # Sort options — working channels first
        self._sort_column = 'status'
        self._sort_reverse = False
        
        # Scan tracking
        self.scan_working_count = 0
        self.scan_failed_count = 0
        self.scan_total_count = 0
        self._scan_running = False
        
        # Thumbnail images cache (with size limit)
        self._thumbnail_images = {}
        self._thumbnail_cache_limit = 100
        self._current_thumbnail = None
        
        # Track displayed channels for click handling (with name index for O(1) lookup)
        self._displayed_channels: List[Dict[str, Any]] = []
        self._displayed_channel_names: Dict[str, Dict[str, Any]] = {}
        
        # UI update debouncing and batching
        self._pending_group_update = None
        self._pending_channel_update = None
        self._last_ui_refresh = 0
        self._ui_update_queue = []
        self._ui_batch_timer = None
        self._min_update_interval = 50
        
        # Create UI
        self._create_sidebar()
        self._create_main_content()
        self._create_status_bar()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Show loading indicator
        logger.info("TV Viewer starting up...")
        
        # Load channels on startup
        self.root.after(100, self._initialize)
    
    def _setup_callbacks(self):
        """Set up callbacks for channel manager events."""
        self.channel_manager.on_channels_loaded = self._on_channels_loaded
        self.channel_manager.on_channel_validated = self._on_channel_validated
        self.channel_manager.on_validation_complete = self._on_validation_complete
        self.channel_manager.on_fetch_progress = self._on_fetch_progress
    
    def _on_resize(self, event):
        """Debounce resize events to prevent lag during window drag."""
        # Only handle root window resize, not child widgets
        if event.widget is not self.root:
            return
        if self._resize_timer:
            self.root.after_cancel(self._resize_timer)
        self._resize_timer = self.root.after(150, self._do_resize)
    
    def _do_resize(self):
        """Actual resize handler — runs after drag stops."""
        self._resize_timer = None
    
    def _create_sidebar(self):
        """Create the left sidebar with Windows 11 Fluent Design."""
        # Sidebar frame
        self.sidebar = ttk.Frame(self.root, width=340)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        # Row 6 = category scroll (expandable)
        self.sidebar.grid_rowconfigure(6, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_propagate(False)
        
        # App title with version on same line
        title_frame = ttk.Frame(self.sidebar)
        title_frame.grid(row=0, column=0, padx=12, pady=(10, 5), sticky="ew")
        
        self.title_label = ttk.Label(
            title_frame,
            text=f"📺 {config.APP_NAME}",
            font=("Segoe UI", 16, "bold"),
            foreground=FluentColors.ACCENT
        )
        self.title_label.pack(side="left")
        
        self.version_label = ttk.Label(
            title_frame,
            text=f"v{config.APP_VERSION}",
            font=("Segoe UI", 10)
        )
        self.version_label.pack(side="right", padx=5)
        
        # Search box
        self._create_search_box()
        
        # Group by and media type selectors
        self._create_compact_selectors()
        
        # Filter toggles
        self._create_filter_toggles()
        
        # Category list (now at row 5 - expandable)
        self._create_category_list()
        
        # Scan indicator (compact)
        self._create_scan_indicator()
        
        # Action buttons at bottom
        self._create_action_buttons()
    
    def _create_scan_indicator(self):
        """Create scan progress indicator with animation."""
        # Container frame
        self.scan_frame = ttk.Frame(self.sidebar)
        self.scan_frame.grid(row=7, column=0, padx=10, pady=(5, 2), sticky="ew")
        
        # Scan animation widget (pixel art) — compact
        self.scan_animation = ScanProgressFrame(self.scan_frame)
        self.scan_animation.pack(padx=5, pady=2)
        
        # Scan status label
        self.scan_label = ttk.Label(
            self.scan_frame,
            text="Ready",
            font=("Segoe UI", 10)
        )
        self.scan_label.pack(padx=10, pady=(0, 2))
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.scan_frame,
            variable=self.progress_var,
            mode='determinate',
            bootstyle="info",
            length=280
        )
        self.progress_bar.pack(padx=10, pady=(0, 2), fill="x")
        
        # Stats label
        self.stats_label = ttk.Label(
            self.scan_frame,
            text="",
            font=("Segoe UI", 9)
        )
        self.stats_label.pack(padx=10, pady=(0, 2))
    
    def _create_search_box(self):
        """Create search box."""
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            self.sidebar,
            textvariable=self.search_var,
            font=("Segoe UI", 11)
        )
        self.search_entry.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        
        # Add placeholder text using a trace (ttk doesn't have native placeholder support)
        self._search_placeholder = "🔍 Search channels..."
        self._search_has_focus = False
        
        def on_search_focus_in(event):
            if self.search_var.get() == self._search_placeholder:
                self.search_var.set("")
            self._search_has_focus = True
        
        def on_search_focus_out(event):
            if not self.search_var.get():
                self.search_var.set(self._search_placeholder)
            self._search_has_focus = False
        
        self.search_entry.bind("<FocusIn>", on_search_focus_in)
        self.search_entry.bind("<FocusOut>", on_search_focus_out)
        self.search_var.set(self._search_placeholder)
        
        self.search_var.trace('w', self._on_search)
    
    def _create_compact_selectors(self):
        """Create group by and media type selectors."""
        # Group by selector
        group_frame = ttk.Frame(self.sidebar)
        group_frame.grid(row=2, column=0, padx=15, pady=3, sticky="ew")
        
        ttk.Label(
            group_frame,
            text="Group:",
            font=("Segoe UI", 11)
        ).pack(side="left")
        
        # Create segmented button replacement with radiobuttons
        self.group_by_var = tk.StringVar(value="Category")
        seg_frame = ttk.Frame(group_frame)
        seg_frame.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        ttk.Radiobutton(
            seg_frame,
            text="Category",
            variable=self.group_by_var,
            value="Category",
            command=lambda: self._on_group_by_change("Category"),
            bootstyle="primary-toolbutton"
        ).pack(side="left", expand=True, fill="x")
        
        ttk.Radiobutton(
            seg_frame,
            text="Country",
            variable=self.group_by_var,
            value="Country",
            command=lambda: self._on_group_by_change("Country"),
            bootstyle="primary-toolbutton"
        ).pack(side="left", expand=True, fill="x")
        
        # Media type selector
        media_frame = ttk.Frame(self.sidebar)
        media_frame.grid(row=3, column=0, padx=15, pady=3, sticky="ew")
        
        ttk.Label(
            media_frame,
            text="Type:",
            font=("Segoe UI", 11)
        ).pack(side="left")
        
        self.media_type_var = tk.StringVar(value="All")
        media_seg_frame = ttk.Frame(media_frame)
        media_seg_frame.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        for media_type in ["All", "TV", "Radio"]:
            ttk.Radiobutton(
                media_seg_frame,
                text=media_type,
                variable=self.media_type_var,
                value=media_type,
                command=lambda mt=media_type: self._on_media_type_change(mt),
                bootstyle="primary-toolbutton"
            ).pack(side="left", expand=True, fill="x")
    
    def _create_filter_toggles(self):
        """Create filter toggle switches - compact layout."""
        # Filter options in a compact frame
        filter_frame = ttk.Frame(self.sidebar)
        filter_frame.grid(row=4, column=0, padx=15, pady=3, sticky="ew")
        
        # Row 1: Hide checking + Hide failed
        row1 = ttk.Frame(filter_frame)
        row1.pack(fill="x", pady=1)
        
        self.hide_checking_var = tk.BooleanVar(value=False)
        self.hide_checking_switch = ttk.Checkbutton(
            row1,
            text="Hide checking",
            variable=self.hide_checking_var,
            command=self._apply_filters,
            bootstyle="round-toggle"
        )
        self.hide_checking_switch.pack(side="left")
        
        self.hide_failed_var = tk.BooleanVar(value=True)
        self.hide_failed_switch = ttk.Checkbutton(
            row1,
            text="Hide failed",
            variable=self.hide_failed_var,
            command=self._apply_filters,
            bootstyle="round-toggle"
        )
        self.hide_failed_switch.pack(side="right")
        
        # Row 2: Share toggle
        from utils.privatebin import is_enabled, set_enabled
        
        row2 = ttk.Frame(filter_frame)
        row2.pack(fill="x", pady=1)
        
        self.privatebin_var = tk.BooleanVar(value=is_enabled())
        self.privatebin_switch = ttk.Checkbutton(
            row2,
            text="Share scan results",
            variable=self.privatebin_var,
            command=lambda: set_enabled(self.privatebin_var.get()),
            bootstyle="round-toggle"
        )
        self.privatebin_switch.pack(side="left")
        
        # Row 3: Favorites only toggle
        row3 = ttk.Frame(filter_frame)
        row3.pack(fill="x", pady=1)
        
        self.show_favorites_var = tk.BooleanVar(value=False)
        self.show_favorites_switch = ttk.Checkbutton(
            row3,
            text="★ Favorites only",
            variable=self.show_favorites_var,
            command=self._apply_filters,
            bootstyle="round-toggle"
        )
        self.show_favorites_switch.pack(side="left")
    
    def _create_category_list(self):
        """Create the category/country scrollable list."""
        # Header
        self.group_header = ttk.Label(
            self.sidebar,
            text="📂 Categories",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        self.group_header.grid(row=5, column=0, padx=15, pady=(8, 3), sticky="w")
        
        # Scrollable frame for categories (row 6 has weight=1, so it expands)
        self.category_scroll = ScrolledFrame(self.sidebar, autohide=True)
        self.category_scroll.grid(row=6, column=0, padx=10, pady=3, sticky="nsew")
        
        # Store category buttons and name->button map for in-place updates
        self.category_buttons = []
        self._group_button_map = {}
    
    def _create_action_buttons(self):
        """Create action buttons at bottom of sidebar."""
        button_frame = ttk.Frame(self.sidebar)
        button_frame.grid(row=8, column=0, padx=10, pady=(5, 10), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Scan toggle button (full width, top)
        self.scan_btn = ttk.Button(
            button_frame,
            text="▶ Start Scan",
            command=self._toggle_scan,
            bootstyle="primary"
        )
        self.scan_btn.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        # Export M3U button
        self.export_btn = ttk.Button(
            button_frame,
            text="📥 Export",
            command=self._export_m3u,
            bootstyle="secondary"
        )
        self.export_btn.grid(row=1, column=0, sticky="ew", padx=(0, 3))
        
        # Settings button
        self.settings_btn = ttk.Button(
            button_frame,
            text="⚙️ Settings",
            command=self._edit_channel_config,
            bootstyle="secondary"
        )
        self.settings_btn.grid(row=1, column=1, sticky="ew", padx=(3, 0))
    
    def _create_main_content(self):
        """Create the main content area with channel list."""
        # Main content frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Header with channel info
        self._create_content_header()
        
        # Channel list (using ttk.Treeview with custom styling)
        self._create_channel_list()
        
        # Preview panel
        self._create_preview_panel()
    
    def _create_content_header(self):
        """Create the content header."""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        
        # Title
        self.channel_header = ttk.Label(
            header_frame,
            text="Select a category",
            font=("Segoe UI", 18, "bold")
        )
        self.channel_header.pack(side="left", padx=20, pady=15)
        
        # Count label
        self.channel_count_label = ttk.Label(
            header_frame,
            text="",
            font=("Segoe UI", 12)
        )
        self.channel_count_label.pack(side="right", padx=20, pady=15)
    
    def _create_channel_list(self):
        """Create the channel list with custom styling."""
        # Container frame
        list_container = ttk.Frame(self.main_frame)
        list_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        list_container.grid_rowconfigure(0, weight=1)
        list_container.grid_columnconfigure(0, weight=1)
        
        # Style the Treeview for dark theme — use ttkbootstrap's native colors
        style = self.root.style
        colors = style.colors
        
        style.configure(
            "Material.Treeview",
            background=colors.inputbg,
            foreground=colors.inputfg,
            fieldbackground=colors.inputbg,
            borderwidth=0,
            font=('Segoe UI', 14),
            rowheight=44
        )
        style.configure(
            "Material.Treeview.Heading",
            background=colors.dark,
            foreground=colors.fg,
            borderwidth=0,
            font=('Segoe UI', 11, 'bold'),
            padding=(10, 6)
        )
        style.map(
            "Material.Treeview",
            background=[('selected', colors.primary)],
            foreground=[('selected', '#ffffff')]
        )
        style.map(
            "Material.Treeview.Heading",
            background=[('active', colors.secondary)]
        )
        
        # Scrollbar styling
        style.configure(
            "Material.Vertical.TScrollbar",
            background=colors.secondary,
            troughcolor=colors.bg,
            borderwidth=0,
            arrowsize=0
        )
        
        # Create Treeview
        tree_frame = ttk.Frame(list_container)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.channel_scrollbar = ttk.Scrollbar(tree_frame, style="Material.Vertical.TScrollbar")
        self.channel_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        
        self.channel_tree = ttk.Treeview(
            tree_frame,
            columns=('fav', 'name', 'category', 'status', 'last_checked', 'age', 'country'),
            show='headings',
            yscrollcommand=self.channel_scrollbar.set,
            selectmode='browse',
            style="Material.Treeview"
        )
        self.channel_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.channel_scrollbar.config(command=self.channel_tree.yview)
        
        # Configure fav column (star) — fixed narrow width
        self.channel_tree.heading('fav', text='★', command=lambda: self._sort_by_column('fav'))
        self.channel_tree.column('fav', width=30, minwidth=30, anchor='center', stretch=False)
        
        # Configure remaining columns with wider spacing
        columns_config = {
            'name': ('Channel Name', 300),
            'category': ('Category', 110),
            'status': ('Status', 100),
            'last_checked': ('Checked', 75),
            'age': ('Age', 55),
            'country': ('Country', 90)
        }
        
        for col, (title, width) in columns_config.items():
            self.channel_tree.heading(col, text=title, command=lambda c=col: self._sort_by_column(c))
            self.channel_tree.column(col, width=width, minwidth=50)
        
        # Configure tags for status colors
        self.channel_tree.tag_configure('working', foreground=colors.success)
        self.channel_tree.tag_configure('not_working', foreground=colors.danger)
        self.channel_tree.tag_configure('checking', foreground=colors.warning)
        self.channel_tree.tag_configure('favorite', foreground=FluentColors.FAVORITE_STAR)
        
        # Bindings
        self.channel_tree.bind('<Double-1>', self._on_channel_double_click)
        self.channel_tree.bind('<Return>', self._on_channel_double_click)
        self.channel_tree.bind('<<TreeviewSelect>>', self._on_channel_select)
        self.channel_tree.bind('<Button-1>', self._on_tree_click)
        self.channel_tree.bind('<Button-3>', self._on_tree_right_click)
    
    def _create_preview_panel(self):
        """Create the preview panel."""
        preview_frame = ttk.Frame(self.main_frame)
        preview_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Thumbnail container
        thumb_container = ttk.Frame(preview_frame, width=128, height=72)
        thumb_container.pack(side="left", padx=15, pady=14)
        thumb_container.pack_propagate(False)
        
        self.thumbnail_label = ttk.Label(
            thumb_container,
            text="No preview",
            font=("Segoe UI", 11)
        )
        self.thumbnail_label.pack(expand=True)
        
        # Info container
        info_frame = ttk.Frame(preview_frame)
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=14)
        
        self.preview_name_label = ttk.Label(
            info_frame,
            text="Select a channel",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        self.preview_name_label.pack(anchor="w")
        
        self.preview_url_label = ttk.Label(
            info_frame,
            text="",
            font=("Segoe UI", 11),
            anchor="w"
        )
        self.preview_url_label.pack(anchor="w", pady=(2, 0))
        
        self.preview_status_label = ttk.Label(
            info_frame,
            text="",
            font=("Segoe UI", 11),
            anchor="w"
        )
        self.preview_status_label.pack(anchor="w", pady=(2, 0))
        
        # Play button
        self.play_btn = ttk.Button(
            preview_frame,
            text="▶ Play",
            command=self._play_selected_channel,
            bootstyle="success",
            width=15
        )
        self.play_btn.pack(side="right", padx=20)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="Starting...",
            font=("Segoe UI", 11)
        )
        self.status_label.pack(side="left", padx=15, pady=5)
    
    def _update_groups(self):
        """Update the category/country list - optimized for responsiveness."""
        # Clear existing buttons efficiently
        for btn in self.category_buttons:
            btn.destroy()
        self.category_buttons.clear()
        self._group_button_map = {}
        
        # Get all channels - use cached reference
        all_channels = self.channel_manager.channels
        all_working = sum(1 for c in all_channels if c.get('is_working', False))
        
        # Add "All Channels" button
        all_btn = ttk.Button(
            self.category_scroll,
            text=f"📺 All Channels  ({all_working}/{len(all_channels)})",
            command=lambda: self._select_group('__all__'),
            bootstyle="link"
        )
        all_btn.pack(fill="x", pady=2)
        self.category_buttons.append(all_btn)
        self._group_button_map['__all__'] = all_btn
        
        # Separator
        sep = ttk.Separator(self.category_scroll, orient='horizontal')
        sep.pack(fill="x", pady=8)
        self.category_buttons.append(sep)
        
        # Get groups and create buttons in batches via after() to avoid segfault
        groups = self.channel_manager.get_groups()
        self._pending_groups = list(groups)
        self._create_group_buttons_batch(0)

    def _create_group_buttons_batch(self, start_idx):
        """Create group buttons in batches to avoid tkinter segfault."""
        BATCH = 30
        groups = self._pending_groups
        end_idx = min(start_idx + BATCH, len(groups))

        for i in range(start_idx, end_idx):
            group = groups[i]
            try:
                channels = self.channel_manager.get_channels_by_group(group)
                if len(channels) == 0:
                    continue
                working = sum(1 for c in channels if c.get('is_working', False))
                icon = self._get_group_icon(group)

                btn = ttk.Button(
                    self.category_scroll,
                    text=f"{icon} {group}  ({working}/{len(channels)})",
                    command=lambda g=group: self._select_group(g),
                    bootstyle="link"
                )
                btn.pack(fill="x", pady=1)
                self.category_buttons.append(btn)
                self._group_button_map[group] = btn
            except Exception as e:
                logger.debug(f"Error creating button for {group}: {e}")

        # Schedule next batch if more remain
        if end_idx < len(groups):
            self.root.after(10, lambda: self._create_group_buttons_batch(end_idx))
    
    def _get_group_icon(self, group: str) -> str:
        """Get an icon for a group."""
        icons = {
            'News': '📰', 'Sports': '⚽', 'Entertainment': '🎬', 'Movies': '🎥',
            'Music': '🎵', 'Kids': '👶', 'Documentary': '📚', 'Education': '🎓',
            'Comedy': '😂', 'Classic': '📺', 'Lifestyle': '🏠', 'Religious': '⛪',
            'Adult': '🔞', 'Radio': '📻', 'General': '📡', 'Other': '📁',
            'United States': '🇺🇸', 'United Kingdom': '🇬🇧', 'Germany': '🇩🇪',
            'France': '🇫🇷', 'Spain': '🇪🇸', 'Italy': '🇮🇹', 'Canada': '🇨🇦',
            'Israel': '🇮🇱', 'Russia': '🇷🇺', 'Japan': '🇯🇵', 'China': '🇨🇳',
        }
        return icons.get(group, '📁')
    
    def _select_group(self, group: str):
        """Handle group selection."""
        self.current_group = group
        
        if group == '__all__':
            self.channel_header.configure(text="All Channels")
            channels = self.channel_manager.get_all_channels()
        else:
            self.channel_header.configure(text=group)
            channels = self.channel_manager.get_channels_by_group(group)
        
        self._update_channel_list(channels)
    
    def _update_channel_list(self, channels: List[Dict[str, Any]]):
        """Update the channel treeview — capped at 500 items for fast rendering.
        
        Uses grid_remove/grid to hide the treeview during bulk operations,
        preventing flicker and improving insert speed.
        """
        # Apply filters
        filtered_channels = self._filter_channels(channels)
        
        # Sort channels
        filtered_channels = self._sort_channels(filtered_channels)
        
        # Store ALL filtered channels for click handling
        self._displayed_channels = filtered_channels
        self._displayed_channel_names = {ch.get('name', ''): ch for ch in filtered_channels}
        
        # Hide treeview during bulk update to prevent flicker
        tree = self.channel_tree
        tree.pack_forget()
        
        # Clear existing items
        tree.delete(*tree.get_children())
        
        # Show "no results" message if empty
        if not filtered_channels:
            tree.insert('', tk.END, 
                values=("", "No channels found", "", "", "", "", ""),
                tags=('no_results',))
            tree.tag_configure('no_results', foreground='#888888')
            self.channel_count_label.configure(
                text=f"No channels match current filters"
            )
            tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            return
        
        # Cap visible items for fast rendering — Treeview bogs down past ~500 rows
        MAX_VISIBLE = 500
        visible_channels = filtered_channels[:MAX_VISIBLE]
        
        # Bulk insert — build values list first, then insert
        for channel in visible_channels:
            name = channel.get('name', 'Unknown')
            category = channel.get('category', 'Other')
            country = channel.get('country', '')
            min_age = channel.get('min_age', 7)
            age_rating = format_age_rating(min_age)
            
            is_working = channel.get('is_working')
            if is_working is True:
                status = '✓ Working'
                tag = 'working'
            elif is_working is False:
                status = '✗ Offline'
                tag = 'not_working'
            else:
                status = '◌ Checking'
                tag = 'checking'
            
            last_scanned = channel.get('last_scanned', '')
            last_checked = last_scanned[11:16] if last_scanned else ''
            
            # Favorite star
            url = channel.get('url', '')
            fav_star = '★' if self.favorites_manager.is_favorite(url) else ''
            
            tree.insert('', tk.END, 
                values=(fav_star, name, category, status, last_checked, age_rating, country),
                tags=(tag,))
        
        # Show treeview again and process pending draw events
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Update count — show cap notice if truncated
        working = sum(1 for c in channels if c.get('is_working', False))
        if len(filtered_channels) > MAX_VISIBLE:
            self.channel_count_label.configure(
                text=f"{working} working / showing {MAX_VISIBLE} of {len(filtered_channels)} / {len(channels)} total — use search to narrow"
            )
        else:
            self.channel_count_label.configure(
                text=f"{working} working / {len(filtered_channels)} shown / {len(channels)} total"
            )
    
    def _filter_channels(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter channels based on current filter settings."""
        show_favorites_only = self.show_favorites_var.get()
        result = []
        for ch in channels:
            is_working = ch.get('is_working')
            
            if self.hide_checking_var.get() and is_working is None:
                continue
            if self.hide_failed_var.get() and is_working is False:
                continue
            if show_favorites_only and not self.favorites_manager.is_favorite(ch.get('url', '')):
                continue
            
            result.append(ch)
        return result
    
    def _sort_channels(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort channels by current sort column."""
        col = self._sort_column
        reverse = self._sort_reverse
        
        def get_sort_key(ch):
            if col == 'fav':
                # Favorites first (True=0, False=1 for ascending)
                return 0 if self.favorites_manager.is_favorite(ch.get('url', '')) else 1
            elif col == 'name':
                return ch.get('name', '').lower()
            elif col == 'category':
                return ch.get('category', '').lower()
            elif col == 'status':
                is_working = ch.get('is_working')
                if is_working is True:
                    return 0
                elif is_working is None:
                    return 1
                else:
                    return 2
            elif col == 'last_checked':
                return ch.get('last_scanned', '')
            elif col == 'age':
                return ch.get('min_age', 7)
            elif col == 'country':
                return ch.get('country', '').lower()
            return ''
        
        return sorted(channels, key=get_sort_key, reverse=reverse)
    
    def _sort_by_column(self, col: str):
        """Sort by a column."""
        if self._sort_column == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = col
            self._sort_reverse = False
        
        # Update headers
        columns_config = {
            'fav': '★', 'name': 'Channel Name', 'category': 'Category', 'status': 'Status',
            'last_checked': 'Checked', 'age': 'Age', 'country': 'Country'
        }
        for c, title in columns_config.items():
            indicator = ''
            if c == col:
                indicator = ' ▼' if self._sort_reverse else ' ▲'
            self.channel_tree.heading(c, text=title + indicator)
        
        # Refresh list
        if self.current_group:
            self._select_group(self.current_group)
    
    def _apply_filters(self):
        """Apply current filters."""
        if self.current_group:
            self._select_group(self.current_group)
    
    def _on_group_by_change(self, value):
        """Handle group by mode change."""
        mode = value.lower()
        self.group_by_mode = mode
        self.channel_manager.set_group_by(mode)
        
        if mode == 'category':
            self.group_header.configure(text="📂 Categories")
        else:
            self.group_header.configure(text="🌍 Countries")
        
        self.current_group = None
        self._update_groups()
        self.channel_header.configure(text="Select a group")
        self.channel_tree.delete(*self.channel_tree.get_children())
        self.channel_count_label.configure(text="")
    
    def _on_media_type_change(self, value):
        """Handle media type filter change (All/TV/Radio)."""
        self.channel_manager.set_media_type(value)
        self._update_groups()
        if self.current_group:
            self._select_group(self.current_group)
    
    def _on_search(self, *args):
        """Handle search with 300ms debounce to avoid rebuilding on every keystroke."""
        # Cancel pending search
        if hasattr(self, '_search_timer') and self._search_timer:
            self.root.after_cancel(self._search_timer)
        self._search_timer = self.root.after(300, self._do_search)
    
    def _do_search(self):
        """Execute the actual search after debounce delay."""
        self._search_timer = None
        query = self.search_var.get()
        # Ignore placeholder text
        if query and query != self._search_placeholder:
            channels = self.channel_manager.search_channels(query)
            self.channel_header.configure(text=f"Search: {query}")
            self._update_channel_list(channels)
    
    def _on_channel_select(self, event):
        """Handle channel selection."""
        selection = self.channel_tree.selection()
        if not selection:
            return
        
        item = self.channel_tree.item(selection[0])
        channel_name = item['values'][1]
        channel = self._find_channel_by_name(channel_name)
        
        if not channel:
            return
        
        # Update preview
        self.preview_name_label.configure(text=channel.get('name', 'Unknown'))
        
        url = channel.get('url', '')
        display_url = url[:60] + '...' if len(url) > 60 else url
        self.preview_url_label.configure(text=display_url)
        
        is_working = channel.get('is_working')
        if is_working is True:
            self.preview_status_label.configure(text='✓ Working', foreground='#00bc8c')
        elif is_working is False:
            self.preview_status_label.configure(text='✗ Offline', foreground='#e74c3c')
        else:
            self.preview_status_label.configure(text='◌ Checking...', foreground='#f39c12')
        
        # Show thumbnail
        self._show_channel_thumbnail(channel)
    
    def _find_channel_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a channel by name using O(1) index lookup."""
        # Use name index for O(1) lookup
        if name in self._displayed_channel_names:
            return self._displayed_channel_names[name]
        
        # Fallback to full search if not in displayed channels
        if self.current_group == '__all__':
            channels = self.channel_manager.get_all_channels()
        elif self.current_group:
            channels = self.channel_manager.get_channels_by_group(self.current_group)
        else:
            channels = self.channel_manager.channels
        
        for ch in channels:
            if ch.get('name') == name:
                return ch
        return None
    
    def _show_channel_thumbnail(self, channel: Dict[str, Any]):
        """Show thumbnail for channel."""
        if not PIL_AVAILABLE:
            self.thumbnail_label.configure(image=None, text="N/A")
            return
        
        url = channel.get('url', '')
        if not url:
            self.thumbnail_label.configure(image=None, text="No URL")
            return
        
        if thumbnail_exists(url):
            try:
                img = Image.open(get_thumbnail_path(url))
                img = img.resize((128, 72), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._current_thumbnail = photo
                self.thumbnail_label.configure(image=photo, text='')
            except (IOError, OSError) as e:
                logger.debug(f"Thumbnail load error: {e}")
                self.thumbnail_label.configure(image=None, text="Error")
        else:
            if channel.get('is_working'):
                self.thumbnail_label.configure(image=None, text="Loading...")
                capture_thumbnail_async(url, self._on_thumbnail_captured)
            else:
                self.thumbnail_label.configure(image=None, text="No preview")
    
    def _on_thumbnail_captured(self, url: str, path: Optional[str]):
        """Callback when thumbnail captured."""
        if path:
            selection = self.channel_tree.selection()
            if selection:
                item = self.channel_tree.item(selection[0])
                channel = self._find_channel_by_name(item['values'][1])
                if channel and channel.get('url') == url:
                    self.root.after(0, lambda: self._show_channel_thumbnail(channel))
    
    def _on_tree_click(self, event):
        """Handle single click on treeview — toggle favorite when clicking star column.
        
        Uses a short delay to avoid double-toggling on double-click (tkinter fires
        two <Button-1> events before <Double-1>).
        """
        region = self.channel_tree.identify_region(event.x, event.y)
        if region != 'cell':
            return
        
        col_id = self.channel_tree.identify_column(event.x)
        # '#1' is the first column (fav)
        if col_id != '#1':
            return
        
        row_id = self.channel_tree.identify_row(event.y)
        if not row_id:
            return
        
        # Cancel any pending star toggle (prevents double-toggle on double-click)
        if hasattr(self, '_fav_toggle_timer') and self._fav_toggle_timer:
            self.root.after_cancel(self._fav_toggle_timer)
        
        self._fav_toggle_timer = self.root.after(300, lambda: self._do_toggle_fav(row_id))
    
    def _do_toggle_fav(self, row_id: str):
        """Actually toggle favorite for a treeview row (called after debounce)."""
        self._fav_toggle_timer = None
        try:
            item = self.channel_tree.item(row_id)
        except tk.TclError:
            return  # Row no longer exists
        
        channel_name = item['values'][1]
        channel = self._find_channel_by_name(channel_name)
        if not channel:
            return
        
        url = channel.get('url', '')
        if url:
            self.favorites_manager.toggle_favorite(url)
            new_star = '★' if self.favorites_manager.is_favorite(url) else ''
            values = list(item['values'])
            values[0] = new_star
            self.channel_tree.item(row_id, values=values)
    
    def _on_tree_right_click(self, event):
        """Handle right-click context menu on treeview."""
        row_id = self.channel_tree.identify_row(event.y)
        if not row_id:
            return
        
        # Select the row under cursor
        self.channel_tree.selection_set(row_id)
        
        item = self.channel_tree.item(row_id)
        channel_name = item['values'][1]
        channel = self._find_channel_by_name(channel_name)
        if not channel:
            return
        
        url = channel.get('url', '')
        is_fav = self.favorites_manager.is_favorite(url)
        
        # Build context menu
        menu = tk.Menu(self.root, tearoff=0)
        fav_label = "☆ Remove Favorite" if is_fav else "★ Add Favorite"
        menu.add_command(label=fav_label, command=lambda: self._toggle_favorite_from_menu(url, row_id))
        menu.add_separator()
        menu.add_command(label="▶ Play", command=self._play_selected_channel)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _toggle_favorite_from_menu(self, url: str, row_id: str):
        """Toggle favorite from context menu and update the row in-place."""
        self.favorites_manager.toggle_favorite(url)
        new_star = '★' if self.favorites_manager.is_favorite(url) else ''
        item = self.channel_tree.item(row_id)
        values = list(item['values'])
        values[0] = new_star
        self.channel_tree.item(row_id, values=values)

    def _on_channel_double_click(self, event):
        """Handle double-click to play (skip if clicking on star column)."""
        # Cancel pending fav toggle — the double-click supersedes it
        if hasattr(self, '_fav_toggle_timer') and self._fav_toggle_timer:
            self.root.after_cancel(self._fav_toggle_timer)
            self._fav_toggle_timer = None
        
        col_id = self.channel_tree.identify_column(event.x)
        if col_id == '#1':
            # Star column — do nothing on double-click
            return
        self._play_selected_channel()
    
    def _play_selected_channel(self):
        """Play the selected channel."""
        selection = self.channel_tree.selection()
        if not selection:
            return
        
        item = self.channel_tree.item(selection[0])
        channel = self._find_channel_by_name(item['values'][1])
        
        if channel:
            self._play_channel(channel)
    
    def _play_channel(self, channel: Dict[str, Any]):
        """Open player for channel. Health status updated only after confirmed playback."""
        def _on_playback_confirmed(ch: Dict[str, Any]):
            """Called by PlayerWindow when VLC confirms video is playing."""
            if not ch.get('is_working'):
                ch['is_working'] = True
                ch['scan_status'] = 'scanned'
                self.channel_manager.save_channels()
                if self.current_group:
                    self.root.after(500, lambda: self._select_group(self.current_group))
        
        if self.player_window and self.player_window.winfo_exists():
            self.player_window.on_playback_confirmed = _on_playback_confirmed
            self.player_window.set_channel(channel)
        else:
            self.player_window = PlayerWindow(self.root, channel)
            self.player_window.on_playback_confirmed = _on_playback_confirmed
    
    def _on_channels_loaded(self, count: int):
        """Callback when channels loaded."""
        self.root.after(0, lambda: self._update_groups())
        self.root.after(0, lambda: self._set_status(f"Loaded {count} channels, validating..."))
    
    def _on_channel_validated(self, channel: Dict[str, Any], current: int, total: int):
        """Callback when channel validated — runs on background thread.
        
        CRITICAL FIX (Issue #32): This callback is invoked from background thread.
        We only update lightweight counters here (thread-safe int ops).
        The actual UI update is driven by a polling timer (_poll_scan_progress)
        to avoid flooding the main thread event queue with root.after(0) calls.
        """
        # Thread-safe counter updates (simple int assignment is atomic in CPython)
        if channel.get('is_working'):
            self.scan_working_count += 1
        else:
            self.scan_failed_count += 1
        self.scan_total_count = total
        self._scan_current = current
    
    def _batch_ui_update(self, progress: float, current: int, total: int):
        """Perform batched UI updates - minimal work only."""
        try:
            # ttkbootstrap progressbar expects 0-100 value
            self.progress_var.set(progress * 100)
            self.scan_label.configure(text=f"Scanning {current}/{total}")
            self.stats_label.configure(
                text=f"{self.scan_working_count} ok • {self.scan_failed_count} fail"
            )
            # Update scan animation widget
            self.scan_animation.update_progress(current, total, self.scan_working_count, self.scan_failed_count)
        except tk.TclError:
            pass  # Window closed during update
    
    def _start_scan_polling(self):
        """Start a 500ms polling timer that reads scan counters and updates UI.
        
        This replaces the per-channel root.after(0) pattern which flooded the
        event queue with 18K+ callbacks. A single timer is much lighter.
        """
        self._scan_current = 0
        self._scan_poll_timer = None
        self._last_poll_current = -1
        self._last_group_refresh = 0
        self._poll_scan_progress()
    
    def _poll_scan_progress(self):
        """Periodic scan progress UI update — runs on main thread via after()."""
        if not self._scan_running:
            self._scan_poll_timer = None
            return
        
        current = getattr(self, '_scan_current', 0)
        total = self.scan_total_count or 1
        
        # Only update UI if progress actually changed
        if current != self._last_poll_current:
            self._last_poll_current = current
            progress = current / total if total > 0 else 0
            self._batch_ui_update(progress, current, total)
            
            # Refresh group counts every ~2000 channels
            if current - self._last_group_refresh >= 2000 or current == total:
                self._last_group_refresh = current
                self._update_group_counts()
        
        # Reschedule
        self._scan_poll_timer = self.root.after(500, self._poll_scan_progress)
    
    def _debounced_refresh(self):
        """Debounced UI refresh."""
        self._pending_group_update = None
        self._update_groups()
        if self.current_group:
            self._select_group(self.current_group)
    
    def _update_group_counts(self):
        """Update group button text with current working/total counts in-place.
        
        Much faster than _update_groups() which destroys and recreates all buttons.
        Used during scan progress to keep counts fresh without layout thrash.
        """
        if not hasattr(self, '_group_button_map'):
            return
        
        all_channels = self.channel_manager.channels
        all_working = sum(1 for c in all_channels if c.get('is_working', False))
        
        # Update "All Channels" button if present
        if '__all__' in self._group_button_map:
            btn = self._group_button_map['__all__']
            try:
                btn.configure(text=f"📺 All Channels  ({all_working}/{len(all_channels)})")
            except tk.TclError:
                pass
        
        # Update each group button
        for group, btn in self._group_button_map.items():
            if group == '__all__':
                continue
            try:
                channels = self.channel_manager.get_channels_by_group(group)
                working = sum(1 for c in channels if c.get('is_working', False))
                icon = self._get_group_icon(group)
                btn.configure(text=f"{icon} {group}  ({working}/{len(channels)})")
            except (tk.TclError, Exception):
                pass
    
    def _on_validation_complete(self):
        """Callback when validation complete."""
        def _complete():
            # Stop polling timer
            if hasattr(self, '_scan_poll_timer') and self._scan_poll_timer:
                self.root.after_cancel(self._scan_poll_timer)
                self._scan_poll_timer = None
            
            self.progress_var.set(100)
            working = len(self.channel_manager.get_working_channels())
            total = len(self.channel_manager.channels)
            self._set_status(f"Ready - {working}/{total} channels working")
            self.scan_label.configure(text="Scan complete")
            self._update_groups()
            if self.current_group:
                self._select_group(self.current_group)
            self.scan_animation.set_complete(working, total)
            
            # Upload results to PrivateBin if enabled
            try:
                from utils.privatebin import is_enabled, upload_scan_results
                if is_enabled():
                    self.root.after(1000, lambda: upload_scan_results(self.channel_manager.channels))
            except ImportError:
                pass
            
            self.scan_working_count = 0
            self.scan_failed_count = 0
            self._scan_running = False
            self.scan_btn.configure(text="▶ Start Scan")
        
        self.root.after(0, _complete)
    
    def _on_fetch_progress(self, current: int, total: int):
        """Callback for fetch progress."""
        self.root.after(0, lambda: self._set_status(f"Fetching repository {current}/{total}..."))
    
    def _set_status(self, message: str):
        """Update status bar."""
        self.status_label.configure(text=message)
    
    def _toggle_scan(self):
        """Toggle scanning."""
        if self._scan_running:
            self.channel_manager.stream_checker.stop()
            self._scan_running = False
            if hasattr(self, '_scan_poll_timer') and self._scan_poll_timer:
                self.root.after_cancel(self._scan_poll_timer)
                self._scan_poll_timer = None
            self.scan_btn.configure(text="▶ Start Scan")
            self._set_status("Scan stopped")
            self.scan_label.configure(text="Stopped")
            # Mark animation as stopped (Issue #34)
            self.scan_animation.set_stopped()
        else:
            self._scan_running = True
            self.scan_btn.configure(text="⏹ Stop Scan")
            self._set_status("Starting scan...")
            self.scan_label.configure(text="Starting...")
            self.scan_working_count = 0
            self.scan_failed_count = 0
            self._start_scan_polling()
            self.channel_manager.validate_channels_async(rescan_all=False)
    
    def _edit_channel_config(self):
        """Open the Settings dialog (replaces old notepad-based config editing)."""
        self._show_settings_dialog()

    # ── Settings Dialog ──────────────────────────────────────────────────
    def _show_settings_dialog(self):
        """Show a proper Settings dialog with stream, repo, and display options."""
        import json as _json

        # Prevent multiple dialogs
        if hasattr(self, '_settings_win') and self._settings_win is not None:
            try:
                self._settings_win.focus_set()
                return
            except tk.TclError:
                self._settings_win = None

        C = FluentColors  # alias for dark colors used below
        CD = FluentColors
        try:
            from .constants import FluentColorsDark
            CD = FluentColorsDark
        except Exception:
            pass

        FONT = ("Segoe UI", 11)
        FONT_BOLD = ("Segoe UI", 11, "bold")
        FONT_SECTION = ("Segoe UI", 13, "bold")
        FONT_SMALL = ("Segoe UI", 10)

        # ── Load current values ──────────────────────────────────────────
        cur_stream_timeout = getattr(config, 'STREAM_CHECK_TIMEOUT', 5)
        cur_max_concurrent = getattr(config, 'MAX_CONCURRENT_CHECKS', 30)
        cur_request_timeout = getattr(config, 'REQUEST_TIMEOUT', 15)
        cur_batch_size = getattr(config, 'SCAN_BATCH_SIZE', 200)
        cur_scan_delay = getattr(config, 'SCAN_REQUEST_DELAY', 0.005)

        # Load repos from channels_config.json
        config_path = config.CHANNELS_CONFIG_FILE
        cfg_data = {}
        repos_list: list = []
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg_data = _json.load(f)
                repos_list = list(cfg_data.get('repositories', []))
        except Exception as e:
            logger.error(f"Settings: failed to read config JSON: {e}")

        # Default repos for Reset
        default_repos = [
            "https://iptv-org.github.io/iptv/index.m3u",
            "https://iptv-org.github.io/iptv/index.country.m3u",
        ]

        # ── Create dialog window ─────────────────────────────────────────
        dlg = ttk_bs.Toplevel(self.root)
        dlg.title("Settings")
        dlg.resizable(False, False)
        dlg.grab_set()
        self._settings_win = dlg

        # Size & center on parent
        dw, dh = 520, 560
        rx = self.root.winfo_rootx() + (self.root.winfo_width() - dw) // 2
        ry = self.root.winfo_rooty() + (self.root.winfo_height() - dh) // 2
        dlg.geometry(f"{dw}x{dh}+{rx}+{ry}")

        def _on_close():
            self._settings_win = None
            dlg.destroy()

        dlg.protocol("WM_DELETE_WINDOW", _on_close)

        # Try to set icon
        if set_window_icon:
            try:
                set_window_icon(dlg)
            except Exception:
                pass

        # ── Scrollable content ───────────────────────────────────────────
        outer = ttk.Frame(dlg)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Enable mouse-wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        content = ttk.Frame(scroll_frame, padding=18)
        content.pack(fill="both", expand=True)

        # ── Section helper ───────────────────────────────────────────────
        def _section(parent, title, row):
            lbl = ttk.Label(parent, text=title, font=FONT_SECTION,
                            foreground=CD.ACCENT)
            lbl.grid(row=row, column=0, columnspan=3, sticky="w", pady=(14, 4))
            sep = ttk.Separator(parent, orient="horizontal")
            sep.grid(row=row + 1, column=0, columnspan=3, sticky="ew", pady=(0, 6))
            return row + 2

        # ── 1. Stream Settings ───────────────────────────────────────────
        r = _section(content, "⚡  Stream Settings", 0)

        # Stream check timeout
        ttk.Label(content, text="Stream check timeout (s):", font=FONT
                  ).grid(row=r, column=0, sticky="w", padx=(0, 8))
        stream_timeout_var = tk.IntVar(value=cur_stream_timeout)
        stream_timeout_spin = ttk.Spinbox(
            content, from_=1, to=30, width=6,
            textvariable=stream_timeout_var, font=FONT
        )
        stream_timeout_spin.grid(row=r, column=1, sticky="w")
        ttk.Label(content, text="1–30", font=FONT_SMALL,
                  foreground=CD.TEXT_SECONDARY
                  ).grid(row=r, column=2, sticky="w", padx=4)
        r += 1

        # Max concurrent checks
        ttk.Label(content, text="Max concurrent checks:", font=FONT
                  ).grid(row=r, column=0, sticky="w", padx=(0, 8))
        max_concurrent_var = tk.IntVar(value=cur_max_concurrent)
        max_concurrent_spin = ttk.Spinbox(
            content, from_=1, to=100, width=6,
            textvariable=max_concurrent_var, font=FONT
        )
        max_concurrent_spin.grid(row=r, column=1, sticky="w")
        ttk.Label(content, text="1–100", font=FONT_SMALL,
                  foreground=CD.TEXT_SECONDARY
                  ).grid(row=r, column=2, sticky="w", padx=4)
        r += 1

        # Request timeout
        ttk.Label(content, text="Request timeout (s):", font=FONT
                  ).grid(row=r, column=0, sticky="w", padx=(0, 8))
        request_timeout_var = tk.IntVar(value=cur_request_timeout)
        request_timeout_spin = ttk.Spinbox(
            content, from_=5, to=60, width=6,
            textvariable=request_timeout_var, font=FONT
        )
        request_timeout_spin.grid(row=r, column=1, sticky="w")
        ttk.Label(content, text="5–60", font=FONT_SMALL,
                  foreground=CD.TEXT_SECONDARY
                  ).grid(row=r, column=2, sticky="w", padx=4)
        r += 1

        # Batch size
        ttk.Label(content, text="Scan batch size:", font=FONT
                  ).grid(row=r, column=0, sticky="w", padx=(0, 8))
        batch_size_var = tk.IntVar(value=cur_batch_size)
        batch_size_spin = ttk.Spinbox(
            content, from_=50, to=1000, increment=50, width=6,
            textvariable=batch_size_var, font=FONT
        )
        batch_size_spin.grid(row=r, column=1, sticky="w")
        ttk.Label(content, text="50–1000", font=FONT_SMALL,
                  foreground=CD.TEXT_SECONDARY
                  ).grid(row=r, column=2, sticky="w", padx=4)
        r += 1

        # ── 2. Repository Management ────────────────────────────────────
        r = _section(content, "📡  Repositories", r)

        repo_frame = ttk.Frame(content)
        repo_frame.grid(row=r, column=0, columnspan=3, sticky="nsew", pady=(0, 4))
        content.grid_rowconfigure(r, weight=1)
        content.grid_columnconfigure(0, weight=1)
        r += 1

        # Listbox + scrollbar for repos
        repo_lb_frame = ttk.Frame(repo_frame)
        repo_lb_frame.pack(fill="both", expand=True)

        repo_scrollbar = ttk.Scrollbar(repo_lb_frame, orient="vertical")
        repo_listbox = tk.Listbox(
            repo_lb_frame, height=6, selectmode=tk.EXTENDED,
            font=FONT_SMALL,
            bg=CD.BG_CARD, fg=CD.TEXT_PRIMARY,
            selectbackground=CD.ACCENT, selectforeground="#FFFFFF",
            highlightthickness=0, bd=1, relief="solid",
            yscrollcommand=repo_scrollbar.set
        )
        repo_scrollbar.configure(command=repo_listbox.yview)
        repo_listbox.pack(side="left", fill="both", expand=True)
        repo_scrollbar.pack(side="right", fill="y")

        # Populate
        for url in repos_list:
            repo_listbox.insert(tk.END, url)

        # Repo buttons
        repo_btn_frame = ttk.Frame(repo_frame)
        repo_btn_frame.pack(fill="x", pady=(4, 0))

        def _add_repo():
            add_dlg = ttk_bs.Toplevel(dlg)
            add_dlg.title("Add Repository URL")
            add_dlg.resizable(False, False)
            add_dlg.grab_set()
            adw, adh = 440, 120
            ax = dlg.winfo_rootx() + (dlg.winfo_width() - adw) // 2
            ay = dlg.winfo_rooty() + (dlg.winfo_height() - adh) // 2
            add_dlg.geometry(f"{adw}x{adh}+{ax}+{ay}")

            ttk.Label(add_dlg, text="Repository URL:", font=FONT
                      ).pack(anchor="w", padx=12, pady=(10, 2))
            url_var = tk.StringVar()
            url_entry = ttk.Entry(add_dlg, textvariable=url_var, width=52, font=FONT_SMALL)
            url_entry.pack(padx=12, fill="x")
            url_entry.focus_set()

            def _confirm(event=None):
                url = url_var.get().strip()
                if url:
                    repo_listbox.insert(tk.END, url)
                add_dlg.destroy()

            url_entry.bind("<Return>", _confirm)
            btn_fr = ttk.Frame(add_dlg)
            btn_fr.pack(pady=8)
            ttk.Button(btn_fr, text="Add", command=_confirm,
                       bootstyle="primary", width=10).pack(side="left", padx=4)
            ttk.Button(btn_fr, text="Cancel", command=add_dlg.destroy,
                       bootstyle="secondary", width=10).pack(side="left", padx=4)

        def _remove_repo():
            sel = repo_listbox.curselection()
            for idx in reversed(sel):
                repo_listbox.delete(idx)

        ttk.Button(repo_btn_frame, text="➕ Add", command=_add_repo,
                   bootstyle="success-outline", width=10
                   ).pack(side="left", padx=(0, 4))
        ttk.Button(repo_btn_frame, text="➖ Remove", command=_remove_repo,
                   bootstyle="danger-outline", width=10
                   ).pack(side="left", padx=(0, 4))

        repo_count_lbl = ttk.Label(
            repo_btn_frame, text=f"{repo_listbox.size()} repos",
            font=FONT_SMALL, foreground=CD.TEXT_SECONDARY
        )
        repo_count_lbl.pack(side="right")

        # Keep count label updated
        def _update_repo_count(*_args):
            repo_count_lbl.configure(text=f"{repo_listbox.size()} repos")

        repo_listbox.bind("<<ListboxSelect>>", _update_repo_count)

        # ── 3. Display Settings ──────────────────────────────────────────
        r = _section(content, "🎨  Display Settings", r)

        # Default group mode
        ttk.Label(content, text="Default group by:", font=FONT
                  ).grid(row=r, column=0, sticky="w", padx=(0, 8))
        group_mode_var = tk.StringVar(
            value=self.group_by_mode.capitalize()
        )
        group_combo = ttk.Combobox(
            content, textvariable=group_mode_var,
            values=["Category", "Country"],
            state="readonly", width=14, font=FONT
        )
        group_combo.grid(row=r, column=1, columnspan=2, sticky="w")
        r += 1

        # Theme selector
        ttk.Label(content, text="Theme:", font=FONT
                  ).grid(row=r, column=0, sticky="w", padx=(0, 8))
        available_themes = ["darkly", "superhero", "cyborg", "vapor", "solar"]
        current_theme = self.root.style.theme.name if hasattr(self.root.style, 'theme') else "darkly"
        theme_var = tk.StringVar(value=current_theme)
        theme_combo = ttk.Combobox(
            content, textvariable=theme_var,
            values=available_themes,
            state="readonly", width=14, font=FONT
        )
        theme_combo.grid(row=r, column=1, columnspan=2, sticky="w")
        r += 1

        # ── Bottom button bar ────────────────────────────────────────────
        btn_bar = ttk.Frame(dlg, padding=(18, 8))
        btn_bar.pack(fill="x", side="bottom")

        def _save():
            """Persist all settings and apply in-memory."""
            # -- Stream settings -- apply to config module --
            try:
                config.STREAM_CHECK_TIMEOUT = max(1, min(30, stream_timeout_var.get()))
            except (tk.TclError, ValueError):
                pass
            try:
                config.MAX_CONCURRENT_CHECKS = max(1, min(100, max_concurrent_var.get()))
            except (tk.TclError, ValueError):
                pass
            try:
                config.REQUEST_TIMEOUT = max(5, min(60, request_timeout_var.get()))
            except (tk.TclError, ValueError):
                pass
            try:
                config.SCAN_BATCH_SIZE = max(50, min(1000, batch_size_var.get()))
            except (tk.TclError, ValueError):
                pass

            # -- Repositories -- write to channels_config.json --
            new_repos = list(repo_listbox.get(0, tk.END))
            try:
                save_data = dict(cfg_data)  # preserve custom_channels etc.
                save_data['repositories'] = new_repos
                with open(config_path, 'w', encoding='utf-8') as f:
                    _json.dump(save_data, f, indent=2, ensure_ascii=False)
                # Update in-memory repos
                config.IPTV_REPOSITORIES = new_repos
                logger.info(f"Settings: saved {len(new_repos)} repos to {config_path}")
            except Exception as e:
                logger.error(f"Settings: failed to save repos: {e}")
                messagebox.showerror("Error", f"Failed to save repositories:\n{e}",
                                     parent=dlg)
                return

            # -- Display settings --
            new_group = group_mode_var.get()
            if new_group.lower() != self.group_by_mode:
                self._on_group_by_change(new_group)
                self.group_by_var.set(new_group)

            new_theme = theme_var.get()
            if new_theme != current_theme:
                try:
                    self.root.style.theme_use(new_theme)
                    logger.info(f"Settings: theme changed to {new_theme}")
                except Exception as e:
                    logger.warning(f"Settings: failed to apply theme: {e}")

            _on_close()
            logger.info("Settings saved successfully")

        def _reset():
            """Reset all fields to defaults."""
            stream_timeout_var.set(5)
            max_concurrent_var.set(30)
            request_timeout_var.set(15)
            batch_size_var.set(200)
            group_mode_var.set("Category")
            theme_var.set("darkly")
            # Reset repo list to defaults
            repo_listbox.delete(0, tk.END)
            for url in default_repos:
                repo_listbox.insert(tk.END, url)
            _update_repo_count()

        ttk.Button(btn_bar, text="Reset to Defaults", command=_reset,
                   bootstyle="warning-outline", width=16
                   ).pack(side="left")
        ttk.Button(btn_bar, text="Cancel", command=_on_close,
                   bootstyle="secondary", width=10
                   ).pack(side="right", padx=(4, 0))
        ttk.Button(btn_bar, text="Save", command=_save,
                   bootstyle="primary", width=10
                   ).pack(side="right")
    
    def _export_m3u(self):
        """Export all channels as M3U playlist file."""
        from tkinter import filedialog
        
        # Get all working channels
        channels = self.channel_manager.get_all_channels()
        working_channels = [ch for ch in channels if ch.get('is_working', False)]
        
        if not working_channels:
            messagebox.showwarning("No Channels", 
                "No working channels to export.\nRun a scan first to validate channels.")
            return
        
        # Ask for save location
        filepath = filedialog.asksaveasfilename(
            title="Export M3U Playlist",
            defaultextension=".m3u",
            filetypes=[("M3U Playlist", "*.m3u"), ("M3U8 Playlist", "*.m3u8"), ("All Files", "*.*")],
            initialfile="tv_channels.m3u"
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                f.write(f"# TV Viewer Export - {len(working_channels)} channels\n")
                f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for ch in working_channels:
                    name = ch.get('name', 'Unknown')
                    url = ch.get('url', '')
                    category = ch.get('category', 'Other')
                    logo = ch.get('logo', '')
                    country = ch.get('country', '')
                    
                    if not url:
                        continue
                    
                    # Build EXTINF line with attributes
                    extinf = f'#EXTINF:-1 tvg-name="{name}"'
                    if category:
                        extinf += f' group-title="{category}"'
                    if logo:
                        extinf += f' tvg-logo="{logo}"'
                    if country:
                        extinf += f' tvg-country="{country}"'
                    extinf += f',{name}\n'
                    
                    f.write(extinf)
                    f.write(f'{url}\n')
            
            messagebox.showinfo("Export Complete", 
                f"Exported {len(working_channels)} channels to:\n{filepath}")
            logger.info(f"Exported {len(working_channels)} channels to {filepath}")
            
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export playlist:\n{e}")
            logger.error(f"Export failed: {e}")
    
    def _show_about(self):
        """Show about dialog with IPTV information."""
        dialog = tk.Toplevel(self.root)
        dialog.title("About")
        dialog.geometry("620x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 620) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 600) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Scrollable content
        scroll_frame = ScrolledFrame(dialog, autohide=True)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # App title
        ttk.Label(
            scroll_frame,
            text=f"📺 {config.APP_NAME}",
            font=("Segoe UI", 24, "bold"),
            foreground=FluentColors.PRIMARY
        ).pack(pady=(10, 5))
        
        ttk.Label(
            scroll_frame,
            text=f"Version {config.APP_VERSION}",
            font=("Segoe UI", 14),
            foreground=FluentColors.TEXT_SECONDARY
        ).pack(pady=(0, 15))
        
        # What is IPTV section
        ttk.Label(
            scroll_frame,
            text="📡 What is IPTV?",
            font=("Segoe UI", 16, "bold"),
            foreground=FluentColors.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 5))
        
        iptv_text = (
            "IPTV (Internet Protocol Television) delivers live TV content "
            "over the internet instead of traditional cable or satellite. "
            "Streams are transmitted using HTTP, HLS, or RTSP protocols, "
            "allowing you to watch TV channels from around the world on "
            "any internet-connected device."
        )
        ttk.Label(
            scroll_frame,
            text=iptv_text,
            font=("Segoe UI", 12),
            foreground=FluentColors.TEXT_SECONDARY,
            wraplength=560,
            justify="left"
        ).pack(fill="x", pady=(0, 10))
        
        ttk.Label(
            scroll_frame,
            text="🔧 How It Works",
            font=("Segoe UI", 16, "bold"),
            foreground=FluentColors.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 5))
        
        how_text = (
            "This app discovers free, publicly available IPTV streams from "
            "open repositories. It validates each stream's availability in "
            "the background, showing you which channels are currently online. "
            "Streams use M3U/M3U8 playlists - a standard format for multimedia playlists."
        )
        ttk.Label(
            scroll_frame,
            text=how_text,
            font=("Segoe UI", 12),
            foreground=FluentColors.TEXT_SECONDARY,
            wraplength=560,
            justify="left"
        ).pack(fill="x", pady=(0, 10))
        
        # Features section
        ttk.Label(
            scroll_frame,
            text="✨ Features",
            font=("Segoe UI", 16, "bold"),
            foreground=FluentColors.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 5))
        
        features = [
            "• Auto-discover IPTV repositories worldwide",
            "• Background stream validation",
            "• Filter by category, country, or media type",
            "• Windows 11 Fluent Design interface",
            "• Embedded VLC-powered video player",
            "• Support for TV and Radio streams",
            "• Thumbnail previews for channels",
            "• Export channels to M3U playlist",
            "• No login or subscription required"
        ]
        
        for feature in features:
            ttk.Label(
                scroll_frame,
                text=feature,
                font=("Segoe UI", 12),
                foreground=FluentColors.TEXT_PRIMARY,
                anchor="w"
            ).pack(fill="x", padx=10)
        
        # Disclaimer
        ttk.Label(
            scroll_frame,
            text="⚠️ Disclaimer",
            font=("Segoe UI", 14, "bold"),
            foreground=FluentColors.ACCENT,
            anchor="w"
        ).pack(fill="x", pady=(15, 5))
        
        disclaimer_text = (
            "This app only aggregates publicly available streams. "
            "We do not host any content. Stream availability and "
            "quality depend on third-party sources."
        )
        ttk.Label(
            scroll_frame,
            text=disclaimer_text,
            font=("Segoe UI", 11),
            foreground=FluentColors.TEXT_SECONDARY,
            wraplength=560,
            justify="left"
        ).pack(fill="x", pady=(0, 15))
        
        # Close button
        ttk.Button(
            dialog,
            text="Close",
            command=dialog.destroy,
            bootstyle="primary",
            width=15
        ).pack(pady=15)
    
    def _initialize(self):
        """Initialize on startup."""
        self._set_status("Loading cached channels...")
        self.scan_label.configure(text="Loading...")
        
        # Check for shared scan results from PrivateBin
        shared_scan_data = None
        try:
            from utils.privatebin import is_enabled, get_recent_scan_results, get_non_working_urls
            if is_enabled():
                self._set_status("Checking for shared scan results...")
                shared_scan_data = get_recent_scan_results()
                if shared_scan_data:
                    non_working = get_non_working_urls(shared_scan_data)
                    if non_working:
                        logger.info(f"Found {len(non_working)} non-working channels from shared scan")
                        self.channel_manager.set_non_working_urls(non_working)
        except Exception as e:
            logger.warning(f"Could not check shared scan results: {e}")
        
        has_cache = self.channel_manager.load_cached_channels()
        if has_cache:
            self._update_groups()
            cached_count = len(self.channel_manager.channels)
            working = len(self.channel_manager.get_working_channels())
            
            # Select "All Channels" to show content immediately
            self.root.after(100, lambda: self._select_group('__all__'))
            
            if shared_scan_data:
                self._set_status(f"Loaded {cached_count} channels - scanning only failed channels")
            else:
                self._set_status(f"Loaded {cached_count} cached channels ({working} working)")
            
            self.root.after(500, lambda: self.channel_manager.validate_channels_async(rescan_all=False))
            self.root.after(2000, self.channel_manager.fetch_channels_async)
            self._scan_running = True
            self._start_scan_polling()
            self.scan_btn.configure(text="⏹ Stop Scan")
        else:
            self._set_status("No cache found. Fetching channels...")
            self.channel_manager.fetch_channels_async()
            self._scan_running = True
            self._start_scan_polling()
            self.scan_btn.configure(text="⏹ Stop Scan")
    
    def _on_close(self):
        """Handle close."""
        if self._pending_group_update:
            self.root.after_cancel(self._pending_group_update)
        if self._pending_channel_update:
            self.root.after_cancel(self._pending_channel_update)
        if hasattr(self, '_scan_poll_timer') and self._scan_poll_timer:
            self.root.after_cancel(self._scan_poll_timer)
        if hasattr(self, '_search_timer') and self._search_timer:
            self.root.after_cancel(self._search_timer)
        
        self.channel_manager.stop()
        
        if self.player_window and self.player_window.winfo_exists():
            self.player_window._on_close()
            self.player_window = None
        
        gc.collect()
        self.root.destroy()
    
    def run(self):
        """Start the app."""
        self.root.mainloop()
