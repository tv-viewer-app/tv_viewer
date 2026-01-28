"""Main application window with Windows 11 Fluent Design UI using CustomTkinter."""

import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from typing import Optional, Dict, Any, List
import gc
import time
import os

from core.channel_manager import ChannelManager
from utils.helpers import format_age_rating
from utils.thumbnail import capture_thumbnail_async, get_thumbnail_path, thumbnail_exists
from utils.logger import get_logger
from .player_window import PlayerWindow
from .scan_animation import ScanProgressFrame
from .constants import FluentColors, FluentSpacing, FluentTypography
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

# Set CustomTkinter appearance for Windows 11 Light theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class MainWindow:
    """Main application window with Windows 11 Fluent Design."""
    
    def __init__(self):
        # Initialize CustomTkinter window
        self.root = ctk.CTk()
        self.root.title(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.root.minsize(800, 500)
        
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Set window icon
        if set_window_icon:
            set_window_icon(self.root)
        
        # Channel manager
        self.channel_manager = ChannelManager()
        self._setup_callbacks()
        
        # Player window reference
        self.player_window: Optional[PlayerWindow] = None
        
        # Currently selected group and grouping mode
        self.current_group: Optional[str] = None
        self.group_by_mode = 'category'
        
        # Filter options
        self.hide_checking = False
        self.hide_failed = False
        
        # Sort options
        self._sort_column = 'name'
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
    
    def _create_sidebar(self):
        """Create the left sidebar with Windows 11 Fluent Design."""
        # Sidebar frame
        self.sidebar = ctk.CTkFrame(
            self.root,
            width=300,
            corner_radius=0,
            fg_color=FluentColors.BG_ACRYLIC
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        # Row 5 = category list (scrollable, expands)
        self.sidebar.grid_rowconfigure(5, weight=1)
        self.sidebar.grid_propagate(False)
        
        # App title with version on same line
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=12, pady=(10, 5), sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text=f"📺 {config.APP_NAME}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=FluentColors.ACCENT
        )
        self.title_label.pack(side="left")
        
        self.version_label = ctk.CTkLabel(
            title_frame,
            text=f"v{config.APP_VERSION}",
            font=ctk.CTkFont(size=10),
            text_color=FluentColors.TEXT_SECONDARY
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
        self.scan_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=FluentColors.BG_CARD,
            corner_radius=FluentSpacing.CORNER_RADIUS_SMALL,
        )
        self.scan_frame.grid(row=6, column=0, padx=10, pady=5, sticky="ew")
        
        # Scan animation widget (pixel art)
        self.scan_animation = ScanProgressFrame(self.scan_frame)
        self.scan_animation.pack(padx=5, pady=5)
        
        # Simple text labels below animation
        self.scan_label = ctk.CTkLabel(
            self.scan_frame,
            text="Ready",
            font=ctk.CTkFont(size=10),
            text_color=FluentColors.TEXT_SECONDARY
        )
        self.scan_label.pack(padx=10, pady=(0, 2))
        
        # Progress bar (backup visual)
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(
            self.scan_frame,
            variable=self.progress_var,
            progress_color=FluentColors.ACCENT,
            fg_color=FluentColors.SURFACE_VARIANT,
            height=4
        )
        self.progress_bar.pack(padx=10, pady=(0, 5), fill="x")
        
        # Stats label
        self.stats_label = ctk.CTkLabel(
            self.scan_frame,
            text="",
            font=ctk.CTkFont(size=9),
            text_color=FluentColors.TEXT_DISABLED
        )
        self.stats_label.pack(padx=10, pady=(0, 5))
    
    def _create_search_box(self):
        """Create search box."""
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self.sidebar,
            placeholder_text="🔍 Search channels...",
            textvariable=self.search_var,
            height=36,
            corner_radius=18,
            border_width=1,
            border_color=FluentColors.SURFACE_STROKE,
            fg_color=FluentColors.SURFACE
        )
        self.search_entry.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        self.search_var.trace('w', self._on_search)
    
    def _create_compact_selectors(self):
        """Create group by and media type selectors."""
        # Group by selector
        group_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        group_frame.grid(row=2, column=0, padx=15, pady=3, sticky="ew")
        
        ctk.CTkLabel(
            group_frame,
            text="Group:",
            font=ctk.CTkFont(size=11),
            text_color=FluentColors.TEXT_SECONDARY
        ).pack(side="left")
        
        self.group_segmented = ctk.CTkSegmentedButton(
            group_frame,
            values=["Category", "Country"],
            command=self._on_group_by_change,
            font=ctk.CTkFont(size=10),
            selected_color=FluentColors.PRIMARY,
            selected_hover_color=FluentColors.PRIMARY_DARK,
            height=28
        )
        self.group_segmented.set("Category")
        self.group_segmented.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # Media type selector
        media_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        media_frame.grid(row=3, column=0, padx=15, pady=3, sticky="ew")
        
        ctk.CTkLabel(
            media_frame,
            text="Type:",
            font=ctk.CTkFont(size=11),
            text_color=FluentColors.TEXT_SECONDARY
        ).pack(side="left")
        
        self.media_type_var = ctk.StringVar(value="All")
        self.media_segmented = ctk.CTkSegmentedButton(
            media_frame,
            values=["All", "TV", "Radio"],
            command=self._on_media_type_change,
            variable=self.media_type_var,
            font=ctk.CTkFont(size=10),
            selected_color=FluentColors.PRIMARY,
            selected_hover_color=FluentColors.PRIMARY_DARK,
            height=28
        )
        self.media_segmented.set("All")
        self.media_segmented.pack(side="right", fill="x", expand=True, padx=(5, 0))
    
    def _create_filter_toggles(self):
        """Create filter toggle switches - compact layout."""
        # Filter options in a compact frame
        filter_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        filter_frame.grid(row=4, column=0, padx=15, pady=3, sticky="ew")
        
        # Row 1: Hide checking + Hide failed
        row1 = ctk.CTkFrame(filter_frame, fg_color="transparent")
        row1.pack(fill="x", pady=1)
        
        self.hide_checking_var = ctk.BooleanVar(value=False)
        self.hide_checking_switch = ctk.CTkSwitch(
            row1,
            text="Hide checking",
            variable=self.hide_checking_var,
            command=self._apply_filters,
            font=ctk.CTkFont(size=10),
            width=32,
            height=18,
            progress_color=FluentColors.PRIMARY
        )
        self.hide_checking_switch.pack(side="left")
        
        self.hide_failed_var = ctk.BooleanVar(value=False)
        self.hide_failed_switch = ctk.CTkSwitch(
            row1,
            text="Hide failed",
            variable=self.hide_failed_var,
            command=self._apply_filters,
            font=ctk.CTkFont(size=10),
            width=32,
            height=18,
            progress_color=FluentColors.PRIMARY
        )
        self.hide_failed_switch.pack(side="right")
        
        # Row 2: Share toggle
        from utils.privatebin import is_enabled, set_enabled
        
        row2 = ctk.CTkFrame(filter_frame, fg_color="transparent")
        row2.pack(fill="x", pady=1)
        
        self.privatebin_var = ctk.BooleanVar(value=is_enabled())
        self.privatebin_switch = ctk.CTkSwitch(
            row2,
            text="Share scan results",
            variable=self.privatebin_var,
            command=lambda: set_enabled(self.privatebin_var.get()),
            font=ctk.CTkFont(size=10),
            width=32,
            height=18,
            progress_color=FluentColors.PRIMARY
        )
        self.privatebin_switch.pack(side="left")
    
    def _create_category_list(self):
        """Create the category/country scrollable list."""
        # Header
        self.group_header = ctk.CTkLabel(
            self.sidebar,
            text="📂 Categories",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=FluentColors.TEXT_PRIMARY,
            anchor="w"
        )
        self.group_header.grid(row=5, column=0, padx=15, pady=(8, 3), sticky="w")
        
        # Scrollable frame for categories (this is the expandable row)
        self.category_scroll = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_button_color=FluentColors.SURFACE_VARIANT,
            scrollbar_button_hover_color=FluentColors.PRIMARY
        )
        # Row 5 is set as weight=1 in _create_sidebar, so use row index that matches
        self.category_scroll.grid(row=5, column=0, padx=10, pady=3, sticky="nsew")
        
        # Store category buttons
        self.category_buttons = []
    
    def _create_action_buttons(self):
        """Create action buttons at bottom of sidebar."""
        button_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        button_frame.grid(row=7, column=0, padx=10, pady=10, sticky="ew")
        
        # Scan toggle button
        self.scan_btn = ctk.CTkButton(
            button_frame,
            text="▶ Start Scan",
            command=self._toggle_scan,
            height=36,
            corner_radius=18,
            fg_color=FluentColors.PRIMARY,
            hover_color=FluentColors.PRIMARY_DARK
        )
        self.scan_btn.pack(fill="x", pady=(0, 8))
        
        # Export M3U button
        self.export_btn = ctk.CTkButton(
            button_frame,
            text="📥 Export M3U",
            command=self._export_m3u,
            height=36,
            corner_radius=18,
            fg_color=FluentColors.SURFACE_VARIANT,
            hover_color=FluentColors.BG_ELEVATED,
            text_color=FluentColors.TEXT_PRIMARY
        )
        self.export_btn.pack(fill="x", pady=(0, 8))
        
        # Settings button
        self.settings_btn = ctk.CTkButton(
            button_frame,
            text="⚙️ Edit Config",
            command=self._edit_channel_config,
            height=36,
            corner_radius=18,
            fg_color=FluentColors.SURFACE_VARIANT,
            hover_color=FluentColors.BG_ELEVATED,
            text_color=FluentColors.TEXT_PRIMARY
        )
        self.settings_btn.pack(fill="x", pady=(0, 8))
        
        # About button
        self.about_btn = ctk.CTkButton(
            button_frame,
            text="ℹ️ About",
            command=self._show_about,
            height=36,
            corner_radius=18,
            fg_color="transparent",
            hover_color=FluentColors.SURFACE_VARIANT,
            text_color=FluentColors.TEXT_SECONDARY,
            border_width=1,
            border_color=FluentColors.SURFACE_VARIANT
        )
        self.about_btn.pack(fill="x")
    
    def _create_main_content(self):
        """Create the main content area with channel list."""
        # Main content frame
        self.main_frame = ctk.CTkFrame(
            self.root,
            fg_color=FluentColors.BG_DARK,
            corner_radius=0
        )
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
        header_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=FluentColors.BG_CARD,
            corner_radius=0,
            height=60
        )
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        
        # Title
        self.channel_header = ctk.CTkLabel(
            header_frame,
            text="Select a category",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=FluentColors.TEXT_PRIMARY
        )
        self.channel_header.pack(side="left", padx=20, pady=15)
        
        # Count label
        self.channel_count_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=FluentColors.TEXT_SECONDARY
        )
        self.channel_count_label.pack(side="right", padx=20, pady=15)
    
    def _create_channel_list(self):
        """Create the channel list with custom styling."""
        # Container frame
        list_container = ctk.CTkFrame(
            self.main_frame,
            fg_color=FluentColors.BG_DARK,
            corner_radius=0
        )
        list_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        list_container.grid_rowconfigure(0, weight=1)
        list_container.grid_columnconfigure(0, weight=1)
        
        # Style the Treeview for Material Design
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure Treeview colors
        style.configure(
            "Material.Treeview",
            background=FluentColors.BG_CARD,
            foreground=FluentColors.TEXT_PRIMARY,
            fieldbackground=FluentColors.BG_CARD,
            borderwidth=0,
            font=('Segoe UI', 11),
            rowheight=36
        )
        style.configure(
            "Material.Treeview.Heading",
            background=FluentColors.SURFACE_VARIANT,
            foreground=FluentColors.TEXT_PRIMARY,
            borderwidth=0,
            font=('Segoe UI', 11, 'bold'),
            padding=(10, 8)
        )
        style.map(
            "Material.Treeview",
            background=[('selected', FluentColors.PRIMARY)],
            foreground=[('selected', FluentColors.TEXT_PRIMARY)]
        )
        style.map(
            "Material.Treeview.Heading",
            background=[('active', FluentColors.BG_ELEVATED)]
        )
        
        # Scrollbar styling
        style.configure(
            "Material.Vertical.TScrollbar",
            background=FluentColors.SURFACE_VARIANT,
            troughcolor=FluentColors.BG_DARK,
            borderwidth=0,
            arrowsize=0
        )
        
        # Create Treeview
        tree_frame = ctk.CTkFrame(list_container, fg_color=FluentColors.BG_CARD, corner_radius=10)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.channel_scrollbar = ttk.Scrollbar(tree_frame, style="Material.Vertical.TScrollbar")
        self.channel_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        
        self.channel_tree = ttk.Treeview(
            tree_frame,
            columns=('name', 'category', 'status', 'last_checked', 'age', 'country'),
            show='headings',
            yscrollcommand=self.channel_scrollbar.set,
            selectmode='browse',
            style="Material.Treeview"
        )
        self.channel_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.channel_scrollbar.config(command=self.channel_tree.yview)
        
        # Configure columns
        columns_config = {
            'name': ('Channel Name', 250),
            'category': ('Category', 100),
            'status': ('Status', 90),
            'last_checked': ('Checked', 70),
            'age': ('Age', 50),
            'country': ('Country', 80)
        }
        
        for col, (title, width) in columns_config.items():
            self.channel_tree.heading(col, text=title, command=lambda c=col: self._sort_by_column(c))
            self.channel_tree.column(col, width=width, minwidth=50)
        
        # Configure tags for status colors
        self.channel_tree.tag_configure('working', foreground=FluentColors.SUCCESS)
        self.channel_tree.tag_configure('not_working', foreground=FluentColors.ERROR)
        self.channel_tree.tag_configure('checking', foreground=FluentColors.WARNING)
        
        # Bindings
        self.channel_tree.bind('<Double-1>', self._on_channel_double_click)
        self.channel_tree.bind('<Return>', self._on_channel_double_click)
        self.channel_tree.bind('<<TreeviewSelect>>', self._on_channel_select)
    
    def _create_preview_panel(self):
        """Create the preview panel."""
        preview_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=FluentColors.BG_CARD,
            corner_radius=10,
            height=100
        )
        preview_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        preview_frame.grid_propagate(False)
        
        # Thumbnail container
        thumb_container = ctk.CTkFrame(
            preview_frame,
            fg_color=FluentColors.BG_DARK,
            corner_radius=8,
            width=128,
            height=72
        )
        thumb_container.pack(side="left", padx=15, pady=14)
        thumb_container.pack_propagate(False)
        
        self.thumbnail_label = ctk.CTkLabel(
            thumb_container,
            text="No preview",
            font=ctk.CTkFont(size=11),
            text_color=FluentColors.TEXT_DISABLED
        )
        self.thumbnail_label.pack(expand=True)
        
        # Info container
        info_frame = ctk.CTkFrame(preview_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=14)
        
        self.preview_name_label = ctk.CTkLabel(
            info_frame,
            text="Select a channel",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=FluentColors.TEXT_PRIMARY,
            anchor="w"
        )
        self.preview_name_label.pack(anchor="w")
        
        self.preview_url_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=FluentColors.TEXT_SECONDARY,
            anchor="w"
        )
        self.preview_url_label.pack(anchor="w", pady=(2, 0))
        
        self.preview_status_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.preview_status_label.pack(anchor="w", pady=(2, 0))
        
        # Play button
        self.play_btn = ctk.CTkButton(
            preview_frame,
            text="▶ Play",
            command=self._play_selected_channel,
            width=100,
            height=40,
            corner_radius=20,
            fg_color=FluentColors.ACCENT,
            hover_color=FluentColors.ACCENT_DARK,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.play_btn.pack(side="right", padx=20)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_frame = ctk.CTkFrame(
            self.root,
            fg_color=FluentColors.SURFACE,
            corner_radius=0,
            height=30
        )
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_frame.grid_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Starting...",
            font=ctk.CTkFont(size=11),
            text_color=FluentColors.TEXT_SECONDARY
        )
        self.status_label.pack(side="left", padx=15, pady=5)
    
    def _update_groups(self):
        """Update the category/country list - optimized for responsiveness."""
        # Clear existing buttons efficiently
        for btn in self.category_buttons:
            btn.destroy()
        self.category_buttons.clear()
        
        # Allow UI to process
        self.root.update_idletasks()
        
        # Get all channels - use cached reference
        all_channels = self.channel_manager.channels
        all_working = sum(1 for c in all_channels if c.get('is_working', False))
        
        # Add "All Channels" button
        all_btn = ctk.CTkButton(
            self.category_scroll,
            text=f"📺 All Channels  ({all_working}/{len(all_channels)})",
            command=lambda: self._select_group('__all__'),
            fg_color="transparent",
            hover_color=FluentColors.SURFACE_VARIANT,
            text_color=FluentColors.TEXT_PRIMARY,
            anchor="w",
            height=36,
            corner_radius=8
        )
        all_btn.pack(fill="x", pady=2)
        self.category_buttons.append(all_btn)
        
        # Separator
        sep = ctk.CTkFrame(self.category_scroll, height=1, fg_color=FluentColors.SURFACE_VARIANT)
        sep.pack(fill="x", pady=8)
        self.category_buttons.append(sep)
        
        # Get groups and create buttons
        groups = self.channel_manager.get_groups()
        for i, group in enumerate(groups):
            channels = self.channel_manager.get_channels_by_group(group)
            if len(channels) == 0:
                continue
            working = sum(1 for c in channels if c.get('is_working', False))
            
            # Choose icon based on group name
            icon = self._get_group_icon(group)
            
            btn = ctk.CTkButton(
                self.category_scroll,
                text=f"{icon} {group}  ({working}/{len(channels)})",
                command=lambda g=group: self._select_group(g),
                fg_color="transparent",
                hover_color=FluentColors.SURFACE_VARIANT,
                text_color=FluentColors.TEXT_PRIMARY,
                anchor="w",
                height=32,
                corner_radius=8
            )
            btn.pack(fill="x", pady=1)
            self.category_buttons.append(btn)
            
            # Process UI events every 20 buttons to stay responsive
            if i % 20 == 0:
                self.root.update_idletasks()
    
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
        """Update the channel treeview."""
        # Apply filters
        filtered_channels = self._filter_channels(channels)
        
        # Sort channels
        filtered_channels = self._sort_channels(filtered_channels)
        
        # Store displayed channels for click handling with name index
        self._displayed_channels = filtered_channels
        self._displayed_channel_names = {ch.get('name', ''): ch for ch in filtered_channels}
        
        # Clear existing items
        self.channel_tree.delete(*self.channel_tree.get_children())
        
        # Show "no results" message if empty
        if not filtered_channels:
            self.channel_tree.insert('', tk.END, 
                values=("No channels found", "", "", "", "", ""),
                tags=('no_results',))
            self.channel_tree.tag_configure('no_results', foreground=FluentColors.TEXT_DISABLED)
            self.channel_count_label.configure(
                text=f"No channels match current filters"
            )
            return
        
        # Add channels
        for channel in filtered_channels:
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
            
            self.channel_tree.insert('', tk.END, 
                values=(name, category, status, last_checked, age_rating, country),
                tags=(tag,))
        
        # Update count
        working = sum(1 for c in channels if c.get('is_working', False))
        self.channel_count_label.configure(
            text=f"{working} working / {len(filtered_channels)} shown / {len(channels)} total"
        )
    
    def _filter_channels(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter channels based on current filter settings."""
        result = []
        for ch in channels:
            is_working = ch.get('is_working')
            
            if self.hide_checking_var.get() and is_working is None:
                continue
            if self.hide_failed_var.get() and is_working is False:
                continue
            
            result.append(ch)
        return result
    
    def _sort_channels(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort channels by current sort column."""
        col = self._sort_column
        reverse = self._sort_reverse
        
        def get_sort_key(ch):
            if col == 'name':
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
            'name': 'Channel Name', 'category': 'Category', 'status': 'Status',
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
        """Handle search."""
        query = self.search_var.get()
        if query:
            channels = self.channel_manager.search_channels(query)
            self.channel_header.configure(text=f"Search: {query}")
            self._update_channel_list(channels)
    
    def _on_channel_select(self, event):
        """Handle channel selection."""
        selection = self.channel_tree.selection()
        if not selection:
            return
        
        item = self.channel_tree.item(selection[0])
        channel_name = item['values'][0]
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
            self.preview_status_label.configure(text='✓ Working', text_color=FluentColors.SUCCESS)
        elif is_working is False:
            self.preview_status_label.configure(text='✗ Offline', text_color=FluentColors.ERROR)
        else:
            self.preview_status_label.configure(text='◌ Checking...', text_color=FluentColors.WARNING)
        
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
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(128, 72))
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
                channel = self._find_channel_by_name(item['values'][0])
                if channel and channel.get('url') == url:
                    self.root.after(0, lambda: self._show_channel_thumbnail(channel))
    
    def _on_channel_double_click(self, event):
        """Handle double-click to play."""
        self._play_selected_channel()
    
    def _play_selected_channel(self):
        """Play the selected channel."""
        selection = self.channel_tree.selection()
        if not selection:
            return
        
        item = self.channel_tree.item(selection[0])
        channel = self._find_channel_by_name(item['values'][0])
        
        if channel:
            self._play_channel(channel)
    
    def _play_channel(self, channel: Dict[str, Any]):
        """Open player for channel."""
        if self.player_window and self.player_window.winfo_exists():
            self.player_window.set_channel(channel)
        else:
            self.player_window = PlayerWindow(self.root, channel)
    
    def _on_channels_loaded(self, count: int):
        """Callback when channels loaded."""
        self.root.after(0, lambda: self._update_groups())
        self.root.after(0, lambda: self._set_status(f"Loaded {count} channels, validating..."))
    
    def _on_channel_validated(self, channel: Dict[str, Any], current: int, total: int):
        """Callback when channel validated - optimized for minimal UI updates."""
        if channel.get('is_working'):
            self.scan_working_count += 1
        else:
            self.scan_failed_count += 1
        self.scan_total_count = total
        
        # Very aggressive throttling - UI updates are expensive
        # Only update UI every 100-500 channels depending on total
        if total > 10000:
            update_interval = 500
        elif total > 5000:
            update_interval = 200
        else:
            update_interval = 100
        
        # Minimal update conditions
        should_update = (
            (current % update_interval == 0) or 
            (current == total) or 
            (current == 1)  # First channel only
        )
        
        if should_update:
            progress = current / total
            # Schedule update on main thread, but don't force immediate processing
            self.root.after(0, lambda p=progress, c=current, t=total: self._batch_ui_update(p, c, t))
        
        # Refresh channel list even less frequently
        if current == total or (current % 1000 == 0 and current > 0):
            if self._pending_group_update:
                self.root.after_cancel(self._pending_group_update)
            self._pending_group_update = self.root.after(500, self._debounced_refresh)
    
    def _batch_ui_update(self, progress: float, current: int, total: int):
        """Perform batched UI updates - minimal work only."""
        try:
            self.progress_var.set(progress)
            self.scan_label.configure(text=f"Scanning {current}/{total}")
            self.stats_label.configure(
                text=f"{self.scan_working_count} ok • {self.scan_failed_count} fail"
            )
            # Update scan animation widget
            self.scan_animation.update_progress(current, total, self.scan_working_count, self.scan_failed_count)
        except tk.TclError:
            pass  # Window closed during update
    
    def _debounced_refresh(self):
        """Debounced UI refresh."""
        self._pending_group_update = None
        self._update_groups()
        if self.current_group:
            self._select_group(self.current_group)
    
    def _on_validation_complete(self):
        """Callback when validation complete."""
        self.root.after(0, lambda: self.progress_var.set(1.0))
        working = len(self.channel_manager.get_working_channels())
        total = len(self.channel_manager.channels)
        self.root.after(0, lambda: self._set_status(f"Ready - {working}/{total} channels working"))
        self.root.after(0, lambda: self.scan_label.configure(text="Scan complete"))
        self.root.after(0, self._update_groups)
        
        # Update scan animation to show complete
        self.root.after(0, lambda: self.scan_animation.set_complete(working, total))
        
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
        self.root.after(0, lambda: self.scan_btn.configure(text="▶ Start Scan"))
    
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
            self.scan_btn.configure(text="▶ Start Scan")
            self._set_status("Scan stopped")
            self.scan_label.configure(text="Stopped")
        else:
            self._scan_running = True
            self.scan_btn.configure(text="⏹ Stop Scan")
            self._set_status("Starting scan...")
            self.scan_label.configure(text="Starting...")
            self.scan_working_count = 0
            self.scan_failed_count = 0
            self.channel_manager.validate_channels_async(rescan_all=False)
    
    def _edit_channel_config(self):
        """Open config file for editing."""
        import subprocess
        import sys
        
        config_path = config.CHANNELS_CONFIG_FILE
        
        if not os.path.exists(config_path):
            messagebox.showerror("Error", f"Config file not found:\n{config_path}")
            return
        
        try:
            if sys.platform == 'win32':
                os.startfile(config_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', config_path])
            else:
                for editor in ['xdg-open', 'gedit', 'kate', 'nano', 'vi']:
                    try:
                        subprocess.Popen([editor, config_path])
                        break
                    except FileNotFoundError:
                        continue
            
            messagebox.showinfo(
                "Edit Config",
                f"Opening config file:\n{config_path}\n\n"
                "Restart the app after editing."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not open config file:\n{e}")
    
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
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("About")
        dialog.geometry("550x520")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 550) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 520) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # App title
        ctk.CTkLabel(
            scroll_frame,
            text=f"📺 {config.APP_NAME}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=FluentColors.PRIMARY
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            scroll_frame,
            text=f"Version {config.APP_VERSION}",
            font=ctk.CTkFont(size=14),
            text_color=FluentColors.TEXT_SECONDARY
        ).pack(pady=(0, 15))
        
        # What is IPTV section
        ctk.CTkLabel(
            scroll_frame,
            text="📡 What is IPTV?",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=FluentColors.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 5))
        
        iptv_text = (
            "IPTV (Internet Protocol Television) delivers live TV content "
            "over the internet instead of traditional cable or satellite. "
            "Streams are transmitted using HTTP, HLS, or RTSP protocols, "
            "allowing you to watch TV channels from around the world on "
            "any internet-connected device."
        )
        ctk.CTkLabel(
            scroll_frame,
            text=iptv_text,
            font=ctk.CTkFont(size=12),
            text_color=FluentColors.TEXT_SECONDARY,
            wraplength=480,
            justify="left"
        ).pack(fill="x", pady=(0, 10))
        
        # How it works section
        ctk.CTkLabel(
            scroll_frame,
            text="🔧 How It Works",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=FluentColors.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 5))
        
        how_text = (
            "This app discovers free, publicly available IPTV streams from "
            "open repositories. It validates each stream's availability in "
            "the background, showing you which channels are currently online. "
            "Streams use M3U/M3U8 playlists - a standard format for multimedia playlists."
        )
        ctk.CTkLabel(
            scroll_frame,
            text=how_text,
            font=ctk.CTkFont(size=12),
            text_color=FluentColors.TEXT_SECONDARY,
            wraplength=480,
            justify="left"
        ).pack(fill="x", pady=(0, 10))
        
        # Features section
        ctk.CTkLabel(
            scroll_frame,
            text="✨ Features",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=FluentColors.TEXT_PRIMARY,
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
            ctk.CTkLabel(
                scroll_frame,
                text=feature,
                font=ctk.CTkFont(size=12),
                text_color=FluentColors.TEXT_PRIMARY,
                anchor="w"
            ).pack(fill="x", padx=10)
        
        # Disclaimer
        ctk.CTkLabel(
            scroll_frame,
            text="⚠️ Disclaimer",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=FluentColors.ACCENT,
            anchor="w"
        ).pack(fill="x", pady=(15, 5))
        
        disclaimer_text = (
            "This app only aggregates publicly available streams. "
            "We do not host any content. Stream availability and "
            "quality depend on third-party sources."
        )
        ctk.CTkLabel(
            scroll_frame,
            text=disclaimer_text,
            font=ctk.CTkFont(size=11),
            text_color=FluentColors.TEXT_SECONDARY,
            wraplength=480,
            justify="left"
        ).pack(fill="x", pady=(0, 15))
        
        # Close button
        ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            width=100,
            fg_color=FluentColors.PRIMARY,
            hover_color=FluentColors.PRIMARY_DARK
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
            self.scan_btn.configure(text="⏹ Stop Scan")
        else:
            self._set_status("No cache found. Fetching channels...")
            self.channel_manager.fetch_channels_async()
            self._scan_running = True
            self.scan_btn.configure(text="⏹ Stop Scan")
    
    def _on_close(self):
        """Handle close."""
        if self._pending_group_update:
            self.root.after_cancel(self._pending_group_update)
        if self._pending_channel_update:
            self.root.after_cancel(self._pending_channel_update)
        
        self.channel_manager.stop()
        
        if self.player_window and self.player_window.winfo_exists():
            self.player_window._on_close()
            self.player_window = None
        
        gc.collect()
        self.root.destroy()
    
    def run(self):
        """Start the app."""
        self.root.mainloop()
