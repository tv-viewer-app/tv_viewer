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
import sys

from core.channel_manager import ChannelManager
from utils.helpers import format_age_rating
from utils.thumbnail import capture_thumbnail_async, get_thumbnail_path, thumbnail_exists
from utils.favorites import FavoritesManager
from utils.history import WatchHistory
from utils.channel_descriptions import get_description
from utils.logger import get_logger
from .player_window import PlayerWindow
from .scan_animation import ScanProgressFrame
from .map_window import MapWindow
from .feedback_dialog import show_feedback_dialog
from .constants import FluentColorsDark as FluentColors, FluentSpacing, FluentTypography
from .tooltip import add_tooltip
from .toast import ToastManager
from utils.telemetry import track_channel_play, track_feature, track_scan_complete
from utils.parental import ParentalControls
from utils.epg import epg_service
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
        self.root.grid_columnconfigure(0, minsize=420)
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
        
        # Watch history (recently played)
        self.watch_history = WatchHistory()
        
        # Parental controls
        self.parental_controls = ParentalControls()
        
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
        
        # Session analytics counters
        import time
        self._app_start_time = time.time()
        self._channels_played_count = 0
        self._channels_failed_count = 0
        
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
        
        # Toast notification manager (must be after UI creation)
        self.toast = ToastManager(self.root)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Global keyboard shortcuts
        self.root.bind_all("<Control-f>", lambda e: self._focus_search())
        self.root.bind_all("<Control-F>", lambda e: self._focus_search())
        self.root.bind_all("<F5>", lambda e: self._start_scan())
        self.root.bind_all("<Control-comma>", lambda e: self._show_settings_dialog())
        self.root.bind_all("<Escape>", lambda e: self._clear_search())
        
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
        self.sidebar = ttk.Frame(self.root, width=460)
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
        
        # Scan status label — single line, readable
        self.scan_label = ttk.Label(
            self.scan_frame,
            text="Ready",
            font=("Segoe UI", 10),
            anchor="w"
        )
        self.scan_label.pack(padx=10, pady=(4, 2), fill="x")
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.scan_frame,
            variable=self.progress_var,
            mode='determinate',
            bootstyle="info"
        )
        self.progress_bar.pack(padx=10, pady=(0, 2), fill="x")
        
        # Stats label below progress bar
        self.stats_label = ttk.Label(
            self.scan_frame,
            text="",
            font=("Segoe UI", 9),
            anchor="w"
        )
        self.stats_label.pack(padx=10, pady=(0, 4), fill="x")
        
        # Keep animation reference for API compatibility but don't display it
        self.scan_animation = ScanProgressFrame(self.scan_frame)
        # Hidden — pixel art canvas was causing text overlap issues
        # self.scan_animation.pack()
    
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
        self._search_placeholder = "🔍 Search (try country:US or working:)"
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
        add_tooltip(self.search_entry, "Search channels — try country:US or category:news (Ctrl+F)")
        
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
        
        # Row 2: Favorites only toggle
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
        button_frame.grid_columnconfigure(2, weight=1)
        
        # Scan toggle button (full width, top)
        self.scan_btn = ttk.Button(
            button_frame,
            text="▶ Start Scan",
            command=self._toggle_scan,
            bootstyle="primary"
        )
        self.scan_btn.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))
        
        # Export M3U button
        self.export_btn = ttk.Button(
            button_frame,
            text="📥 Export",
            command=self._export_m3u,
            bootstyle="secondary"
        )
        self.export_btn.grid(row=1, column=0, sticky="ew", padx=(0, 3))
        
        # World Map button
        self.map_btn = ttk.Button(
            button_frame,
            text="🗺️ Map",
            command=self._open_map,
            bootstyle="secondary"
        )
        self.map_btn.grid(row=1, column=1, sticky="ew", padx=3)
        
        # Settings button
        self.settings_btn = ttk.Button(
            button_frame,
            text="⚙️ Settings",
            command=self._edit_channel_config,
            bootstyle="secondary"
        )
        self.settings_btn.grid(row=1, column=2, sticky="ew", padx=(3, 0))
        
        # Feedback button
        self.feedback_btn = ttk.Button(
            button_frame,
            text="💬 Feedback",
            command=self._show_feedback,
            bootstyle="secondary"
        )
        self.feedback_btn.grid(row=2, column=0, sticky="ew", padx=(0, 3), pady=(5, 0))
        
        # About button
        self.about_btn = ttk.Button(
            button_frame,
            text="ℹ️ About",
            command=self._show_about,
            bootstyle="secondary"
        )
        self.about_btn.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(3, 0), pady=(5, 0))

        # Add Channel (contribute) button
        self.contribute_btn = ttk.Button(
            button_frame,
            text="➕ Add Channel",
            command=self._show_contribute_dialog,
            bootstyle="success-outline"
        )
        self.contribute_btn.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(5, 0))

        # Tooltips
        add_tooltip(self.scan_btn, "Scan all channels to check which are online (F5)")
        add_tooltip(self.export_btn, "Export working channels to M3U playlist file")
        add_tooltip(self.map_btn, "Show channels on a world map by country")
        add_tooltip(self.settings_btn, "Open settings (Ctrl+,)")
        add_tooltip(self.contribute_btn, "Submit a new channel to the shared database")
    
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
            font=('Segoe UI', 12),
            rowheight=48
        )
        style.configure(
            "Material.Treeview.Heading",
            background=colors.dark,
            foreground=colors.fg,
            borderwidth=0,
            font=('Segoe UI', 10, 'bold'),
            padding=(10, 8)
        )
        style.map(
            "Material.Treeview",
            background=[('selected', colors.primary)],
            foreground=[('selected', FluentColors.BG_CARD)]
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
        
        # Fast mouse-wheel scrolling (5 lines per tick instead of default 1)
        def _fast_scroll(event):
            self.channel_tree.yview_scroll(int(-5 * (event.delta / 120)), "units")
            return "break"
        self.channel_tree.bind("<MouseWheel>", _fast_scroll)
        
        # Configure fav column (star) — fixed narrow width
        self.channel_tree.heading('fav', text='★', command=lambda: self._sort_by_column('fav'))
        self.channel_tree.column('fav', width=40, minwidth=40, anchor='center', stretch=False)
        
        # Configure remaining columns with wider spacing
        columns_config = {
            'name': ('Channel Name', 280),
            'category': ('Category', 120),
            'status': ('Status', 90),
            'last_checked': ('Checked', 80),
            'age': ('Age', 50),
            'country': ('Country', 100)
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
        
        # EPG Now/Next labels
        self.epg_frame = ttk.Frame(info_frame)
        self.epg_frame.pack(anchor="w", fill="x", pady=(4, 0))
        
        self.epg_now_label = ttk.Label(
            self.epg_frame,
            text="",
            font=("Segoe UI", 10),
            foreground=FluentColors.ACCENT,
            anchor="w"
        )
        self.epg_now_label.pack(anchor="w")
        
        self.epg_next_label = ttk.Label(
            self.epg_frame,
            text="",
            font=("Segoe UI", 9),
            foreground=FluentColors.TEXT_SECONDARY,
            anchor="w"
        )
        self.epg_next_label.pack(anchor="w")
        
        # EPG progress bar (shows current program progress)
        self.epg_progress_var = tk.DoubleVar(value=0)
        self.epg_progress_bar = ttk.Progressbar(
            self.epg_frame,
            variable=self.epg_progress_var,
            mode='determinate',
            bootstyle="info",
            length=200,
        )
        self.epg_progress_bar.pack(anchor="w", pady=(2, 0))
        self.epg_progress_bar.pack_forget()  # Hidden until EPG data available
        
        # Play button
        self.play_btn = ttk.Button(
            preview_frame,
            text="▶ Play",
            command=self._play_selected_channel,
            bootstyle="success",
            width=15
        )
        self.play_btn.pack(side="right", padx=20)
        add_tooltip(self.play_btn, "Play the selected channel (double-click also works)")
    
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
        
        # Recently Played section (top of group list, filtered by parental controls)
        recent_channels = self.watch_history.get_recent(limit=10)
        filtered_recent = [
            entry for entry in recent_channels
            if not self.parental_controls.is_channel_blocked(entry)
        ][:5]
        if filtered_recent:
            recent_header = ttk.Label(
                self.category_scroll,
                text="⏱ Recently Played",
                font=("Segoe UI", 11, "bold"),
                anchor="w",
            )
            recent_header.pack(fill="x", pady=(2, 4), padx=5)
            self.category_buttons.append(recent_header)
            
            for entry in filtered_recent:
                ch_name = entry.get("name", "Unknown")
                ch_url = entry.get("url", "")
                display = f"  ▸ {ch_name}"
                btn = ttk.Button(
                    self.category_scroll,
                    text=display,
                    command=lambda u=ch_url, e=entry: self._play_recent_channel(e),
                    bootstyle="link",
                )
                btn.pack(fill="x", pady=0)
                self.category_buttons.append(btn)
            
            # "Show all" button → selects the __recently_played__ virtual group
            show_all_btn = ttk.Button(
                self.category_scroll,
                text="  ⏱ Show all recent…",
                command=lambda: self._select_group('__recently_played__'),
                bootstyle="link",
            )
            show_all_btn.pack(fill="x", pady=(0, 2))
            self.category_buttons.append(show_all_btn)
            self._group_button_map['__recently_played__'] = show_all_btn
            
            sep2 = ttk.Separator(self.category_scroll, orient='horizontal')
            sep2.pack(fill="x", pady=8)
            self.category_buttons.append(sep2)
        
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
        """Handle group selection. Boosts scan priority for selected country."""
        self.current_group = group
        
        if group == '__all__':
            self.channel_header.configure(text="All Channels")
            channels = self.channel_manager.get_all_channels()
        elif group == '__recently_played__':
            self.channel_header.configure(text="⏱ Recently Played")
            recent = self.watch_history.get_recent(limit=40)
            # Build channel dicts, filtered by parental controls
            channels = []
            for entry in recent:
                if self.parental_controls.is_channel_blocked(entry):
                    continue
                url = entry.get('url', '')
                full_ch = self._find_channel_by_url(url)
                if full_ch:
                    channels.append(full_ch)
                else:
                    channels.append(entry)
                if len(channels) >= 20:
                    break
        else:
            self.channel_header.configure(text=group)
            channels = self.channel_manager.get_channels_by_group(group)
            # Boost scan priority for this group (may be a country)
            self.channel_manager.stream_checker.boost_country(group)
        
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
        # URL-based index for stable O(1) lookups (avoids duplicate name collisions)
        self._displayed_channel_urls = {ch.get('url', ''): ch for ch in filtered_channels if ch.get('url')}
        
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
            tree.tag_configure('no_results', foreground=FluentColors.TEXT_DISABLED)
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
            urls = channel.get('urls', [])
            if len(urls) > 1:
                name = f"{name}  [{len(urls)} sources]"
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
        _adult_keywords = {'xxx', 'adult', 'porn', 'nsfw'}
        for ch in channels:
            is_working = ch.get('is_working')
            
            if self.hide_checking_var.get() and is_working is None:
                continue
            if self.hide_failed_var.get() and is_working is False:
                continue
            if show_favorites_only and not self.favorites_manager.is_favorite(ch.get('url', '')):
                continue
            # Hide adult channels unless user confirmed over-18
            if not self.parental_controls.is_over_18:
                cat = (ch.get('category') or '').lower()
                name = (ch.get('name') or '').lower()
                if cat in _adult_keywords or any(kw in name for kw in _adult_keywords):
                    continue
            # Parental controls filtering
            if self.parental_controls.is_channel_blocked(ch):
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
    
    def _focus_search(self):
        """Focus the search entry (Ctrl+F shortcut)."""
        self.search_entry.focus_set()
        if self.search_var.get() == self._search_placeholder:
            self.search_var.set("")
    
    def _clear_search(self):
        """Clear search and restore channel list (Escape shortcut)."""
        if self._search_has_focus or (self.search_var.get() and self.search_var.get() != self._search_placeholder):
            self.search_var.set("")
            self.search_entry.delete(0, tk.END)
            self.root.focus_set()
            # Restore current group view
            if self.current_group:
                self._select_group(self.current_group)
    
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
            self.preview_status_label.configure(text='✓ Working', foreground=FluentColors.SUCCESS)
        elif is_working is False:
            self.preview_status_label.configure(text='✗ Offline', foreground=FluentColors.ERROR)
        else:
            self.preview_status_label.configure(text='◌ Checking...', foreground=FluentColors.WARNING)
        
        # Show thumbnail
        self._show_channel_thumbnail(channel)
        
        # Update EPG Now/Next info
        self._update_epg_display(channel.get('name', ''))
    
    def _find_channel_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a channel by name using O(1) index lookup."""
        # Strip source count suffix from display name (e.g. "BBC One  [3 sources]")
        import re
        clean_name = re.sub(r'\s+\[\d+ sources\]$', '', name)
        
        # Use name index for O(1) lookup
        if clean_name in self._displayed_channel_names:
            return self._displayed_channel_names[clean_name]
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
            if ch.get('name') == clean_name or ch.get('name') == name:
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
                self.thumbnail_label.configure(image=None, text="📷 No Preview")
        else:
            if channel.get('is_working'):
                self.thumbnail_label.configure(image=None, text="⏳ Capturing preview...")
                capture_thumbnail_async(url, self._on_thumbnail_captured)
            elif channel.get('is_working') is False:
                self.thumbnail_label.configure(image=None, text="📷 No preview available")
            else:
                self.thumbnail_label.configure(image=None, text="📷 Preview")
    
    def _on_thumbnail_captured(self, url: str, path: Optional[str]):
        """Callback when thumbnail captured.
        
        Bug #73: This is called from a background thread. Schedule ALL work
        on the main thread via after() to avoid tkinter segfaults.
        """
        if not path:
            return
        def _update():
            try:
                if not self.root.winfo_exists():
                    return
                selection = self.channel_tree.selection()
                if selection:
                    item = self.channel_tree.item(selection[0])
                    channel = self._find_channel_by_name(item['values'][1])
                    if channel and channel.get('url') == url:
                        self._show_channel_thumbnail(channel)
            except (tk.TclError, Exception):
                pass
        self.root.after(0, _update)
    
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
            is_fav = self.favorites_manager.is_favorite(url)
            new_star = '★' if is_fav else ''
            values = list(item['values'])
            values[0] = new_star
            self.channel_tree.item(row_id, values=values)
            # Track favorite event
            track_feature(f"favorite_{'add' if is_fav else 'remove'}")
    
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
        
        # Source selector option
        urls = channel.get('urls', [])
        if len(urls) > 1:
            menu.add_separator()
            source_menu = tk.Menu(menu, tearoff=0)
            for i, src_url in enumerate(urls):
                # Show truncated URL
                label = f"Source #{i+1}: {src_url[:60]}..."
                source_menu.add_command(
                    label=label,
                    command=lambda ch=channel, idx=i: self._play_channel_with_source(ch, idx)
                )
            menu.add_cascade(label=f"📡 Sources ({len(urls)})", menu=source_menu)
        
        # Channel info/description option
        description = get_description(str(channel_name))
        if description:
            menu.add_separator()
            menu.add_command(
                label="ℹ Channel Info",
                command=lambda d=description, n=channel_name: self._show_channel_info(str(n), d),
            )
        
        # Report broken channel option
        menu.add_separator()
        menu.add_command(
            label="Report Broken 🔴",
            command=lambda ch=channel: self._report_broken_channel(ch),
        )
        menu.add_command(
            label="Wrong Info 🏷️",
            command=lambda ch=channel: self._report_misclassified(ch),
        )
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _toggle_favorite_from_menu(self, url: str, row_id: str):
        """Toggle favorite from context menu and update the row in-place."""
        self.favorites_manager.toggle_favorite(url)
        is_fav = self.favorites_manager.is_favorite(url)
        new_star = '★' if is_fav else ''
        item = self.channel_tree.item(row_id)
        values = list(item['values'])
        values[0] = new_star
        self.channel_tree.item(row_id, values=values)
        track_feature(f"favorite_{'add' if is_fav else 'remove'}")

    def _show_channel_info(self, channel_name: str, description: str):
        """Show channel description in an info messagebox."""
        messagebox.showinfo(
            f"Channel Info — {channel_name}",
            description,
        )

    def _report_broken_channel(self, channel: Dict[str, Any]):
        """Report a channel as broken via Supabase (runs in background thread)."""
        import hashlib as _hashlib

        url = channel.get('url', '')
        name = channel.get('name', 'Unknown')
        if not url:
            messagebox.showwarning(
                "Cannot Report",
                "This channel has no URL to report.",
            )
            return

        url_hash = _hashlib.sha256(url.encode('utf-8')).hexdigest()

        def _run():
            success = False
            error_msg = ""
            try:
                import asyncio as _aio
                from utils.supabase_channels import report_channel, is_configured
                if not is_configured():
                    error_msg = (
                        "Channel reporting is not available right now.\n"
                        "Supabase is not configured."
                    )
                else:
                    loop = _aio.new_event_loop()
                    _aio.set_event_loop(loop)
                    try:
                        success = loop.run_until_complete(report_channel(url_hash))
                    finally:
                        loop.close()
            except Exception as exc:
                logger.warning(f"Report broken channel failed: {exc}")
                error_msg = (
                    "Could not report the channel.\n"
                    "Please check your internet connection."
                )

            # Schedule UI feedback on the main thread
            def _show_result():
                if error_msg:
                    messagebox.showerror("Report Failed", error_msg)
                elif success:
                    self.toast.show_success(f"Reported \"{name}\" as broken")
                    track_feature("channel_reported_broken")
                else:
                    messagebox.showinfo(
                        "Report",
                        "The channel could not be reported.\n"
                        "It may not exist in the shared database yet.",
                    )

            self.root.after(0, _show_result)

        import threading as _thr
        _thr.Thread(target=_run, daemon=True).start()

    def _report_misclassified(self, channel: Dict[str, Any]):
        """Show a dialog to report wrong channel info, then open GitHub issue."""
        import webbrowser
        from urllib.parse import quote

        name = channel.get('name', 'Unknown')
        country = channel.get('country', 'Unknown')
        category = channel.get('category', 'Unknown')

        dlg = tk.Toplevel(self.root)
        dlg.title(f"Report Wrong Info — {name}")
        dlg.geometry("420x340")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        frame = ttk.Frame(dlg, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=name, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(frame, text="What's wrong with this channel?",
                  font=("Segoe UI", 10)).pack(anchor="w", pady=(8, 4))

        field_var = tk.StringVar(value="Country")
        fields = ["Country", "Category", "Name", "Language", "Other"]
        field_frame = ttk.Frame(frame)
        field_frame.pack(anchor="w", pady=4)
        for f in fields:
            ttk.Radiobutton(field_frame, text=f, variable=field_var, value=f).pack(
                side="left", padx=(0, 8))

        current_lbl = ttk.Label(frame, text=f"Current: {country}", font=("Segoe UI", 9))
        current_lbl.pack(anchor="w", pady=(4, 0))

        def _update_current(*_args):
            val = field_var.get()
            current = {"Country": country, "Category": category,
                        "Name": name, "Language": channel.get('language', 'Unknown'),
                        "Other": ""}.get(val, "")
            current_lbl.configure(text=f"Current: {current}" if current else "")
        field_var.trace_add("write", _update_current)

        ttk.Label(frame, text="Correct value (optional):",
                  font=("Segoe UI", 10)).pack(anchor="w", pady=(12, 4))
        correction_var = tk.StringVar()
        correction_entry = ttk.Entry(frame, textvariable=correction_var, width=50)
        correction_entry.pack(anchor="w")
        ttk.Label(frame, text="Leave blank for \"doesn't belong to this field\"",
                  font=("Segoe UI", 8), foreground="#8b949e").pack(anchor="w")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(anchor="e", pady=(16, 0))

        def _submit():
            field = field_var.get()
            correction = correction_var.get().strip()
            current_map = {"Country": country, "Category": category,
                           "Name": name, "Language": channel.get('language', 'Unknown'),
                           "Other": "N/A"}
            current_val = current_map.get(field, "")
            correction_text = correction if correction else f"doesn't belong to this {field}"

            title = quote(f"[Channel] {name} — wrong {field}")
            body = quote(
                f"### Issue type\n\nChannel name or category is wrong\n\n"
                f"### Channel name\n\n{name}\n\n"
                f"### Country / Region\n\n{country}\n\n"
                f"### Additional details\n\n"
                f"**Field:** {field}\n"
                f"**Current value:** {current_val}\n"
                f"**Suggested correction:** {correction_text}\n\n"
                f"_Reported from TV Viewer desktop app_"
            )
            url = (f"https://github.com/tv-viewer-app/tv_viewer/issues/new"
                   f"?title={title}&body={body}&labels=channel-issue,community")
            webbrowser.open(url)
            dlg.destroy()
            self.toast.show_success(f"Opening GitHub to report \"{name}\"")
            track_feature("channel_reported_misclassified")

        ttk.Button(btn_frame, text="Cancel", command=dlg.destroy).pack(side="left", padx=4)
        tk.Button(btn_frame, text="📝 Submit Report", font=("Segoe UI", 10, "bold"),
                  bg="#F59E0B", fg="#1E1E1E", relief="flat", cursor="hand2",
                  padx=12, pady=4, command=_submit).pack(side="left", padx=4)

    def _show_contribute_dialog(self):
        """Open the channel contribution dialog."""
        try:
            from .contribute_dialog import show_contribute_dialog
            show_contribute_dialog(self.root)
            track_feature("contribute_dialog_opened")
            logger.info("Contribute dialog opened")
        except Exception as e:
            logger.error(f"Failed to open contribute dialog: {e}")
            messagebox.showerror(
                "Error",
                "Could not open the contribution dialog.\n"
                "Please try again later.",
            )

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
            # Find index in displayed list for next/prev navigation
            idx = None
            for i, ch in enumerate(self._displayed_channels):
                if ch.get('url') == channel.get('url') and ch.get('name') == channel.get('name'):
                    idx = i
                    break
            self._play_channel(channel, channel_index=idx)
    
    def _play_channel(self, channel: Dict[str, Any], channel_index: Optional[int] = None):
        """Open player for channel. Boosts scan priority for channel's country."""
        # Block playback if parental controls are active and channel is blocked
        if self.parental_controls.is_channel_blocked(channel):
            self._show_pin_entry_dialog(
                title="🔒 Channel Locked",
                message="This channel is restricted by parental controls.\nEnter PIN to watch:",
                on_success=lambda: self._play_channel_unlocked(channel, channel_index),
            )
            return
        self._play_channel_unlocked(channel, channel_index)

    def _play_channel_unlocked(self, channel: Dict[str, Any], channel_index: Optional[int] = None):
        """Actually play the channel (post-PIN-check)."""
        # Bug #98: Check URL before opening player; show error if empty
        url = channel.get('url', '').strip()
        if not url:
            self.toast.show_error("Cannot play: channel has no stream URL")
            logger.warning(f"Blocked playback for '{channel.get('name', '?')}' — empty URL")
            return
        track_channel_play(channel)
        self._channels_played_count += 1
        self.watch_history.record_play(channel)
        # Boost scan priority for this channel's country and URL
        country = channel.get('country', '')
        url = channel.get('url', '')
        if country:
            self.channel_manager.stream_checker.boost_country(country)
        if url:
            self.channel_manager.stream_checker.boost_channel(url)
        
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
            self.player_window = PlayerWindow(
                self.root, channel,
                channel_list=self._displayed_channels if self._displayed_channels else None,
                channel_index=channel_index,
            )
            self.player_window.on_playback_confirmed = _on_playback_confirmed
    
    def _play_channel_with_source(self, channel: Dict[str, Any], source_index: int):
        """Play channel using a specific source URL."""
        urls = channel.get('urls', [])
        if 0 <= source_index < len(urls):
            channel['working_url_index'] = source_index
            channel['url'] = urls[source_index]
        idx = None
        for i, ch in enumerate(self._displayed_channels):
            if ch.get('url') == channel.get('url') and ch.get('name') == channel.get('name'):
                idx = i
                break
        self._play_channel(channel, channel_index=idx)
    
    def _on_channels_loaded(self, count: int):
        """Callback when channels loaded."""
        try:
            if not self.root.winfo_exists():
                return
        except (tk.TclError, RuntimeError):
            return
        self.root.after(0, lambda: self._update_groups())
        self.root.after(0, lambda: self._set_status(f"Loaded {count} channels, validating..."))
    
    def _on_channel_validated(self, channel: Dict[str, Any], current: int, total: int):
        """Callback when channel validated — runs on background thread.
        
        CRITICAL FIX (Issue #32): This callback is invoked from background thread.
        We only update lightweight counters here (thread-safe int ops).
        The actual UI update is driven by a polling timer (_poll_scan_progress)
        to avoid flooding the main thread event queue with root.after(0) calls.
        
        Bug #76: Skip if shutting down.
        """
        if getattr(self.channel_manager, '_shutting_down', False):
            return
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
        
        try:
            if not self.root.winfo_exists():
                self._scan_poll_timer = None
                return
        except (tk.TclError, RuntimeError):
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
            except (tk.TclError, Exception) as e:
                logger.debug(f"Group button update skipped: {e}")
    
    def _on_validation_complete(self):
        """Callback when validation complete."""
        def _complete():
            try:
                if not self.root.winfo_exists():
                    return
            except (tk.TclError, RuntimeError):
                return
            # Stop polling timer
            if hasattr(self, '_scan_poll_timer') and self._scan_poll_timer:
                self.root.after_cancel(self._scan_poll_timer)
                self._scan_poll_timer = None
            
            self.progress_var.set(100)
            working = len(self.channel_manager.get_working_channels())
            total = len(self.channel_manager.channels)
            self._set_status(f"Ready - {working}/{total} channels working")
            self.scan_label.configure(text="Scan complete")
            self.toast.show_info(f"Scan complete: {working} working, {total - working} failed")
            self._update_groups()
            if self.current_group:
                self._select_group(self.current_group)
            self.scan_animation.set_complete(working, total)
            
            # Track scan telemetry
            duration = time.time() - getattr(self, '_scan_start_time', time.time())
            track_scan_complete(total, working, duration)
            
            self.scan_working_count = 0
            self.scan_failed_count = 0
            self._scan_running = False
            self.scan_btn.configure(text="▶ Start Scan")
        
        try:
            if not self.root.winfo_exists():
                return
        except (tk.TclError, RuntimeError):
            return
        self.root.after(0, _complete)
    
    def _on_fetch_progress(self, current: int, total: int):
        """Callback for fetch progress."""
        try:
            if not self.root.winfo_exists():
                return
        except (tk.TclError, RuntimeError):
            return
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
            self.toast.show_warning("Scan stopped by user")
            # Mark animation as stopped (Issue #34)
            self.scan_animation.set_stopped()
        else:
            self._scan_running = True
            self._scan_start_time = time.time()
            track_feature('scan_start')
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

    def _open_map(self):
        """Open the World Map window."""
        track_feature('map_open')
        try:
            MapWindow(
                parent=self.root,
                channel_manager=self.channel_manager,
                favorites_manager=self.favorites_manager,
                on_play_channel=self._play_channel_from_map,
            )
        except Exception as e:
            logger.error(f"Failed to open map: {e}", exc_info=True)
            self.toast.show_error(f"Could not open map: {e}")

    def _play_channel_from_map(self, channel: dict):
        """Play a channel selected from the map."""
        self._play_channel(channel)

    def _play_recent_channel(self, entry: dict):
        """Play a channel from the recently played list."""
        url = entry.get('url', '')
        full_ch = self._find_channel_by_url(url)
        channel = full_ch if full_ch else entry
        self._play_channel(channel)

    def _find_channel_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Find a full channel object by URL from the channel manager."""
        if not url:
            return None
        for ch in self.channel_manager.channels:
            if ch.get('url') == url:
                return ch
        return None

    # ── Settings Dialog (extracted to ui/settings_dialog.py) ────────────
    def _show_settings_dialog(self):
        """Show a proper Settings dialog with stream, repo, and display options."""
        from .settings_dialog import show_settings_dialog
        show_settings_dialog(self)
    
    # ------------------------------------------------------------------
    # Parental Controls — PIN dialogs (extracted to ui/pin_dialogs.py)
    # ------------------------------------------------------------------

    def _show_pin_entry_dialog(self, *args, **kwargs):
        """Show a modal PIN entry dialog with 4 auto-advancing digit fields."""
        from .pin_dialogs import show_pin_entry_dialog
        return show_pin_entry_dialog(self, *args, **kwargs)

    def _show_set_pin_dialog(self, *args, **kwargs):
        """Show a dialog to set a new 4-digit PIN (first time setup)."""
        from .pin_dialogs import show_set_pin_dialog
        return show_set_pin_dialog(self, *args, **kwargs)

    def _show_change_pin_dialog(self, *args, **kwargs):
        """Show dialog to change PIN (old PIN → new PIN → confirm)."""
        from .pin_dialogs import show_change_pin_dialog
        return show_change_pin_dialog(self, *args, **kwargs)

    def _export_m3u(self):
        """Export all channels as M3U playlist file."""
        from .export_manager import export_m3u
        export_m3u(self)
    
    def _show_feedback(self):
        """Show feedback dialog."""
        try:
            show_feedback_dialog(self.root)
            track_feature("feedback_dialog_opened")
            logger.info("Feedback dialog opened")
        except Exception as e:
            logger.error(f"Failed to open feedback dialog: {e}")
            messagebox.showerror(
                "Error",
                "Could not open feedback dialog.\n\n"
                "Please report issues at: https://github.com/tv-viewer-app/tv_viewer/issues"
            )
    
    def _show_about(self):
        """Show about dialog with IPTV information."""
        dialog = tk.Toplevel(self.root)
        dialog.title("About")
        dialog.geometry("620x720")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 620) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 720) // 2
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
        
        # Support the project section
        import webbrowser as _webbrowser
        _AMBER = "#F59E0B"
        _AMBER_DARK = "#D97706"
        _GOLD = "#FBBF24"

        ttk.Label(
            scroll_frame,
            text="🍺 Support the Project",
            font=("Segoe UI", 16, "bold"),
            foreground=_GOLD,
            anchor="w"
        ).pack(fill="x", pady=(10, 5))

        ttk.Label(
            scroll_frame,
            text="If you enjoy TV Viewer, consider supporting the developer!",
            font=("Segoe UI", 11),
            foreground=FluentColors.TEXT_SECONDARY,
            wraplength=560,
            justify="left"
        ).pack(fill="x", pady=(0, 10))

        about_support_frame = ttk.Frame(scroll_frame)
        about_support_frame.pack(fill="x", pady=(0, 15))

        beer_btn = tk.Button(
            about_support_frame,
            text="🍺 Buy Me a Beer",
            font=("Segoe UI", 11, "bold"),
            bg=_AMBER, fg="#1E1E1E",
            activebackground=_AMBER_DARK, activeforeground="#FFFFFF",
            relief="flat", borderwidth=0, cursor="hand2",
            padx=14, pady=6,
            command=lambda: _webbrowser.open("https://buymeacoffee.com/tvviewer"),
        )
        beer_btn.pack(side="left")

        # Close button
        ttk.Button(
            dialog,
            text="Close",
            command=dialog.destroy,
            bootstyle="primary",
            width=15
        ).pack(pady=15)
    
    # ------------------------------------------------------------------
    # Telemetry consent (Issues #65, #79, #114)
    # ------------------------------------------------------------------

    def _get_telemetry_consent_path(self) -> str:
        """Return the path to the persistent telemetry consent file."""
        if sys.platform == 'win32':
            consent_dir = os.path.join(
                os.environ.get('APPDATA', os.path.expanduser('~')), 'TVViewer')
        else:
            consent_dir = os.path.join(
                os.path.expanduser('~'), '.config', 'tvviewer')
        os.makedirs(consent_dir, exist_ok=True)
        return os.path.join(consent_dir, 'telemetry_consent.json')

    def _check_telemetry_consent(self):
        """Show first-run telemetry consent dialog (GDPR / Issue #79).

        If the user has already answered, load their preference from disk.
        Otherwise present a one-time opt-in dialog.  The result is written
        to ``config.TELEMETRY_ENABLED`` so all analytics modules respect it.
        """
        import json

        consent_file = self._get_telemetry_consent_path()

        # ── Returning user — load stored preference ──────────────────────
        if os.path.exists(consent_file):
            try:
                with open(consent_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                config.TELEMETRY_ENABLED = data.get('enabled', False)
                return
            except Exception:
                pass

        # ── First run — ask the user ─────────────────────────────────────
        result = messagebox.askyesno(
            "📊 Anonymous Usage Data",
            "TV Viewer can collect anonymous usage statistics to help "
            "improve the app.\n\n"
            "Data collected (all anonymous):\n"
            "• App version and platform\n"
            "• Feature usage (which features are popular)\n"
            "• Error reports (to fix crashes)\n\n"
            "No personal information, channel names, or URLs are collected.\n"
            "You can change this anytime in Settings → Privacy.\n\n"
            "Allow anonymous usage data?",
            parent=self.root,
        )

        config.TELEMETRY_ENABLED = result
        try:
            with open(consent_file, 'w', encoding='utf-8') as f:
                json.dump({'enabled': result, 'timestamp': time.time()}, f)
        except Exception:
            pass

    def _save_telemetry_preference(self, enabled: bool):
        """Persist a telemetry opt-in / opt-out choice to disk and config."""
        import json

        config.TELEMETRY_ENABLED = enabled
        consent_file = self._get_telemetry_consent_path()
        try:
            with open(consent_file, 'w', encoding='utf-8') as f:
                json.dump({'enabled': enabled, 'timestamp': time.time()}, f)
        except Exception:
            pass

    def _initialize(self):
        """Initialize on startup."""
        # Ask for telemetry consent before any analytics code runs
        self._check_telemetry_consent()
        
        self._set_status("Loading cached channels...")
        self.scan_label.configure(text="Loading...")
        
        has_cache = self.channel_manager.load_cached_channels()
        
        # Show welcome dialog on first run
        if not has_cache:
            self.root.after(200, self._show_welcome_dialog)
        
        # Start EPG fetch in background (non-blocking)
        self._start_epg_refresh()
        
        if has_cache:
            self._update_groups()
            cached_count = len(self.channel_manager.channels)
            working = len(self.channel_manager.get_working_channels())
            
            # Select "All Channels" to show content immediately
            self.root.after(100, lambda: self._select_group('__all__'))
            
            self._set_status(f"Loaded {cached_count} cached channels ({working} working)")
            self.toast.show_success(f"Loaded {cached_count} channels ({working} working)")
            
            # Validation will be triggered by fetch_channels_async after fetch completes
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
    
    # ── First Run ─────────────────────────────────────────────────────────
    
    def _show_welcome_dialog(self):
        """Show a welcome dialog on first launch."""
        dlg = tk.Toplevel(self.root)
        dlg.title(f"Welcome to {config.APP_NAME}")
        dlg.geometry("480x360")
        dlg.resizable(False, False)
        dlg.configure(bg="#1b1a1f")
        dlg.transient(self.root)
        dlg.grab_set()
        
        # Center on parent
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 480) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 360) // 2
        dlg.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dlg)
        frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        ttk.Label(frame, text="📺", font=("Segoe UI Emoji", 36)).pack(pady=(10, 5))
        ttk.Label(
            frame, text=f"Welcome to {config.APP_NAME}!",
            font=("Segoe UI", 18, "bold"), foreground=FluentColors.ACCENT
        ).pack()
        ttk.Label(
            frame, text=f"v{config.APP_VERSION} — Free IPTV Streaming",
            font=("Segoe UI", 11), foreground=FluentColors.TEXT_SECONDARY
        ).pack(pady=(2, 15))
        
        tips = (
            "🔍  Search with filters: country:US, category:news, working:\n"
            "⌨️  Shortcuts: Ctrl+F search, F5 refresh, Ctrl+, settings\n"
            "📺  EPG guide shows Now/Next for supported channels\n"
            "🔒  Set up Parental Controls in Settings (Ctrl+,)\n"
            "⏱  Recently played channels appear in the sidebar"
        )
        ttk.Label(
            frame, text=tips, font=("Segoe UI", 10),
            foreground=FluentColors.TEXT_SECONDARY,
            justify="left", wraplength=400
        ).pack(anchor="w", pady=(0, 15))
        
        ttk.Button(
            frame, text="Get Started →",
            command=dlg.destroy,
            bootstyle="success",
            width=20
        ).pack(pady=(5, 0))
        
        dlg.bind("<Return>", lambda e: dlg.destroy())
        dlg.bind("<Escape>", lambda e: dlg.destroy())
    
    # ── EPG Methods ──────────────────────────────────────────────────────
    
    def _start_epg_refresh(self):
        """Fetch EPG data in background thread (thread-safe)."""
        if getattr(self, '_epg_refreshing', False):
            return  # guard against overlapping refreshes
        self._epg_refreshing = True
        import threading
        def _fetch():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(epg_service.initialize())
                loop.close()
                self._epg_refresh_done = True
            except Exception as e:
                logger.warning(f"EPG refresh failed: {e}")
            finally:
                self._epg_refreshing = False
        self._epg_refresh_done = False
        threading.Thread(target=_fetch, daemon=True).start()
        # Poll for completion from the main thread (Tk-safe)
        self._poll_epg_refresh()
        # Schedule periodic EPG refresh every 2 hours
        self.root.after(2 * 60 * 60 * 1000, self._start_epg_refresh)
    
    def _poll_epg_refresh(self):
        """Poll EPG refresh completion from the main thread (Tk-safe)."""
        if getattr(self, '_epg_refresh_done', False):
            self._set_status("EPG guide loaded")
            self._epg_refresh_done = False
        elif getattr(self, '_epg_refreshing', False):
            self.root.after(500, self._poll_epg_refresh)
    
    def _update_epg_display(self, channel_name: str):
        """Update the EPG Now/Next labels for a channel."""
        try:
            now_prog, next_prog = epg_service.get_now_next(channel_name=channel_name)
            if now_prog:
                start_str = now_prog.start.strftime("%H:%M") if now_prog.start else ""
                end_str = now_prog.end.strftime("%H:%M") if now_prog.end else ""
                self.epg_now_label.configure(
                    text=f"▶ Now: {now_prog.title}  ({start_str}–{end_str})"
                )
                progress = now_prog.progress_percent
                if progress is not None:
                    self.epg_progress_var.set(progress)
                    self.epg_progress_bar.pack(anchor="w", pady=(2, 0))
                else:
                    self.epg_progress_bar.pack_forget()
                
                if next_prog:
                    next_start = next_prog.start.strftime("%H:%M") if next_prog.start else ""
                    self.epg_next_label.configure(
                        text=f"⏭ Next: {next_prog.title}  ({next_start})"
                    )
                else:
                    self.epg_next_label.configure(text="")
            else:
                self.epg_now_label.configure(text="")
                self.epg_next_label.configure(text="")
                self.epg_progress_bar.pack_forget()
        except Exception:
            self.epg_now_label.configure(text="")
            self.epg_next_label.configure(text="")
            self.epg_progress_bar.pack_forget()

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
        
        # Track session end and flush analytics (best-effort with timeout)
        try:
            import asyncio, time, concurrent.futures
            from utils.analytics import analytics
            duration = int(time.time() - self._app_start_time) if hasattr(self, '_app_start_time') else 0

            def _flush_analytics():
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(analytics.track_session_end(
                        session_duration_s=duration,
                        channels_played=getattr(self, '_channels_played_count', 0),
                        channels_failed=getattr(self, '_channels_failed_count', 0),
                    ))
                    loop.run_until_complete(analytics.flush())
                finally:
                    loop.close()

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(_flush_analytics)
                try:
                    future.result(timeout=3)
                except (concurrent.futures.TimeoutError, Exception):
                    logger.debug("Analytics flush timed out or failed on shutdown")
        except Exception:
            pass
        
        self.channel_manager.stop()
        
        # Flush watch history to disk before exit
        if hasattr(self, 'watch_history'):
            self.watch_history.flush()
        
        if self.player_window and self.player_window.winfo_exists():
            self.player_window._on_close()
            self.player_window = None
        
        gc.collect()
        self.root.destroy()
    
    def run(self):
        """Start the app."""
        self.root.mainloop()
