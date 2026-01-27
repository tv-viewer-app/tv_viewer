"""Main application window with Material Design UI using CustomTkinter."""

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
from .player_window import PlayerWindow
from .scan_animation import ScanProgressFrame
from .constants import MaterialColors
import config

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

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")  # "dark", "light", or "system"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"


class MainWindow:
    """Main application window with Material Design."""
    
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
        
        # Thumbnail images cache
        self._thumbnail_images = {}
        self._current_thumbnail = None
        
        # UI update debouncing and batching
        self._pending_group_update = None
        self._pending_channel_update = None
        self._last_ui_refresh = 0
        self._ui_update_queue = []  # Queue for batched updates
        self._ui_batch_timer = None  # Timer for batch processing
        self._min_update_interval = 50  # Minimum ms between UI updates
        
        # Create UI
        self._create_sidebar()
        self._create_main_content()
        self._create_status_bar()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Load channels on startup
        self.root.after(100, self._initialize)
    
    def _setup_callbacks(self):
        """Set up callbacks for channel manager events."""
        self.channel_manager.on_channels_loaded = self._on_channels_loaded
        self.channel_manager.on_channel_validated = self._on_channel_validated
        self.channel_manager.on_validation_complete = self._on_validation_complete
        self.channel_manager.on_fetch_progress = self._on_fetch_progress
    
    def _create_sidebar(self):
        """Create the left sidebar with Material Design."""
        # Sidebar frame
        self.sidebar = ctk.CTkFrame(
            self.root,
            width=320,
            corner_radius=0,
            fg_color=MaterialColors.BG_CARD
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)  # Make category list expandable
        self.sidebar.grid_propagate(False)
        
        # App title with logo
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text=f"📺 {config.APP_NAME}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=MaterialColors.PRIMARY
        )
        self.title_label.pack(anchor="w")
        
        self.version_label = ctk.CTkLabel(
            title_frame,
            text=f"v{config.APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color=MaterialColors.TEXT_SECONDARY
        )
        self.version_label.pack(anchor="w")
        
        # Scan progress indicator
        self._create_scan_indicator()
        
        # Search box with Material Design
        self._create_search_box()
        
        # Group by selector
        self._create_group_selector()
        
        # Media type selector (All/TV/Radio)
        self._create_media_type_selector()
        
        # Filter toggles
        self._create_filter_toggles()
        
        # Category list
        self._create_category_list()
        
        # Action buttons at bottom
        self._create_action_buttons()
    
    def _create_scan_indicator(self):
        """Create scan progress indicator with animation widget."""
        self.scan_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=MaterialColors.SURFACE_VARIANT,
            corner_radius=10
        )
        self.scan_frame.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        
        # Pixel art scan animation widget
        self.scan_animation = ScanProgressFrame(self.scan_frame)
        self.scan_animation.pack(padx=5, pady=5)
        
        # Progress label
        self.scan_label = ctk.CTkLabel(
            self.scan_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=MaterialColors.TEXT_SECONDARY
        )
        self.scan_label.pack(padx=15, pady=(5, 5))
        
        # Progress bar
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(
            self.scan_frame,
            variable=self.progress_var,
            progress_color=MaterialColors.PRIMARY,
            fg_color=MaterialColors.BG_DARK
        )
        self.progress_bar.pack(padx=15, pady=(0, 5), fill="x")
        
        # Stats
        self.stats_label = ctk.CTkLabel(
            self.scan_frame,
            text="0 working • 0 failed",
            font=ctk.CTkFont(size=11),
            text_color=MaterialColors.TEXT_SECONDARY
        )
        self.stats_label.pack(padx=15, pady=(0, 10))
    
    def _create_search_box(self):
        """Create Material Design search box."""
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self.sidebar,
            placeholder_text="🔍 Search channels...",
            textvariable=self.search_var,
            height=40,
            corner_radius=20,
            border_width=0,
            fg_color=MaterialColors.SURFACE_VARIANT
        )
        self.search_entry.grid(row=2, column=0, padx=15, pady=10, sticky="ew")
        self.search_var.trace('w', self._on_search)
    
    def _create_group_selector(self):
        """Create group by selector."""
        group_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        group_frame.grid(row=3, column=0, padx=15, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            group_frame,
            text="Group by:",
            font=ctk.CTkFont(size=12),
            text_color=MaterialColors.TEXT_SECONDARY
        ).pack(side="left")
        
        self.group_segmented = ctk.CTkSegmentedButton(
            group_frame,
            values=["Category", "Country"],
            command=self._on_group_by_change,
            font=ctk.CTkFont(size=11),
            selected_color=MaterialColors.PRIMARY,
            selected_hover_color=MaterialColors.PRIMARY_DARK,
            width=180
        )
        self.group_segmented.set("Category")
        self.group_segmented.pack(side="right", fill="x", expand=True)
    
    def _create_media_type_selector(self):
        """Create media type selector (All/TV/Radio)."""
        media_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        media_frame.grid(row=4, column=0, padx=15, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            media_frame,
            text="Media:",
            font=ctk.CTkFont(size=12),
            text_color=MaterialColors.TEXT_SECONDARY
        ).pack(side="left")
        
        self.media_type_var = ctk.StringVar(value="All")
        self.media_segmented = ctk.CTkSegmentedButton(
            media_frame,
            values=["All", "TV", "Radio"],
            command=self._on_media_type_change,
            variable=self.media_type_var,
            font=ctk.CTkFont(size=11),
            selected_color=MaterialColors.PRIMARY,
            selected_hover_color=MaterialColors.PRIMARY_DARK,
            width=180
        )
        self.media_segmented.set("All")
        self.media_segmented.pack(side="right", fill="x", expand=True)
    
    def _create_filter_toggles(self):
        """Create filter toggle switches."""
        filter_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        filter_frame.grid(row=5, column=0, padx=15, pady=5, sticky="ew")
        
        self.hide_checking_var = ctk.BooleanVar(value=False)
        self.hide_checking_switch = ctk.CTkSwitch(
            filter_frame,
            text="Hide checking",
            variable=self.hide_checking_var,
            command=self._apply_filters,
            font=ctk.CTkFont(size=12),
            progress_color=MaterialColors.PRIMARY
        )
        self.hide_checking_switch.pack(side="left", padx=(0, 15))
        
        self.hide_failed_var = ctk.BooleanVar(value=False)
        self.hide_failed_switch = ctk.CTkSwitch(
            filter_frame,
            text="Hide failed",
            variable=self.hide_failed_var,
            command=self._apply_filters,
            font=ctk.CTkFont(size=12),
            progress_color=MaterialColors.PRIMARY
        )
        self.hide_failed_switch.pack(side="left")
    
    def _create_category_list(self):
        """Create the category/country scrollable list."""
        # Header
        self.group_header = ctk.CTkLabel(
            self.sidebar,
            text="📂 Categories",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=MaterialColors.TEXT_PRIMARY,
            anchor="w"
        )
        self.group_header.grid(row=6, column=0, padx=20, pady=(15, 5), sticky="w")
        
        # Scrollable frame for categories
        self.category_scroll = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_button_color=MaterialColors.SURFACE_VARIANT,
            scrollbar_button_hover_color=MaterialColors.PRIMARY
        )
        self.category_scroll.grid(row=7, column=0, padx=10, pady=5, sticky="nsew")
        
        # Store category buttons
        self.category_buttons = []
    
    def _create_action_buttons(self):
        """Create action buttons at bottom of sidebar."""
        button_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        button_frame.grid(row=8, column=0, padx=15, pady=15, sticky="ew")
        
        # Scan toggle button
        self.scan_btn = ctk.CTkButton(
            button_frame,
            text="▶ Start Scan",
            command=self._toggle_scan,
            height=36,
            corner_radius=18,
            fg_color=MaterialColors.PRIMARY,
            hover_color=MaterialColors.PRIMARY_DARK
        )
        self.scan_btn.pack(fill="x", pady=(0, 8))
        
        # Settings button
        self.settings_btn = ctk.CTkButton(
            button_frame,
            text="⚙️ Edit Config",
            command=self._edit_channel_config,
            height=36,
            corner_radius=18,
            fg_color=MaterialColors.SURFACE_VARIANT,
            hover_color=MaterialColors.BG_ELEVATED,
            text_color=MaterialColors.TEXT_PRIMARY
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
            hover_color=MaterialColors.SURFACE_VARIANT,
            text_color=MaterialColors.TEXT_SECONDARY,
            border_width=1,
            border_color=MaterialColors.SURFACE_VARIANT
        )
        self.about_btn.pack(fill="x")
    
    def _create_main_content(self):
        """Create the main content area with channel list."""
        # Main content frame
        self.main_frame = ctk.CTkFrame(
            self.root,
            fg_color=MaterialColors.BG_DARK,
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
            fg_color=MaterialColors.BG_CARD,
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
            text_color=MaterialColors.TEXT_PRIMARY
        )
        self.channel_header.pack(side="left", padx=20, pady=15)
        
        # Count label
        self.channel_count_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=MaterialColors.TEXT_SECONDARY
        )
        self.channel_count_label.pack(side="right", padx=20, pady=15)
    
    def _create_channel_list(self):
        """Create the channel list with custom styling."""
        # Container frame
        list_container = ctk.CTkFrame(
            self.main_frame,
            fg_color=MaterialColors.BG_DARK,
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
            background=MaterialColors.BG_CARD,
            foreground=MaterialColors.TEXT_PRIMARY,
            fieldbackground=MaterialColors.BG_CARD,
            borderwidth=0,
            font=('Segoe UI', 11),
            rowheight=36
        )
        style.configure(
            "Material.Treeview.Heading",
            background=MaterialColors.SURFACE_VARIANT,
            foreground=MaterialColors.TEXT_PRIMARY,
            borderwidth=0,
            font=('Segoe UI', 11, 'bold'),
            padding=(10, 8)
        )
        style.map(
            "Material.Treeview",
            background=[('selected', MaterialColors.PRIMARY)],
            foreground=[('selected', MaterialColors.TEXT_PRIMARY)]
        )
        style.map(
            "Material.Treeview.Heading",
            background=[('active', MaterialColors.BG_ELEVATED)]
        )
        
        # Scrollbar styling
        style.configure(
            "Material.Vertical.TScrollbar",
            background=MaterialColors.SURFACE_VARIANT,
            troughcolor=MaterialColors.BG_DARK,
            borderwidth=0,
            arrowsize=0
        )
        
        # Create Treeview
        tree_frame = ctk.CTkFrame(list_container, fg_color=MaterialColors.BG_CARD, corner_radius=10)
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
        self.channel_tree.tag_configure('working', foreground=MaterialColors.SUCCESS)
        self.channel_tree.tag_configure('not_working', foreground=MaterialColors.ERROR)
        self.channel_tree.tag_configure('checking', foreground=MaterialColors.WARNING)
        
        # Bindings
        self.channel_tree.bind('<Double-1>', self._on_channel_double_click)
        self.channel_tree.bind('<Return>', self._on_channel_double_click)
        self.channel_tree.bind('<<TreeviewSelect>>', self._on_channel_select)
    
    def _create_preview_panel(self):
        """Create the preview panel."""
        preview_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=MaterialColors.BG_CARD,
            corner_radius=10,
            height=100
        )
        preview_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        preview_frame.grid_propagate(False)
        
        # Thumbnail container
        thumb_container = ctk.CTkFrame(
            preview_frame,
            fg_color=MaterialColors.BG_DARK,
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
            text_color=MaterialColors.TEXT_DISABLED
        )
        self.thumbnail_label.pack(expand=True)
        
        # Info container
        info_frame = ctk.CTkFrame(preview_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=14)
        
        self.preview_name_label = ctk.CTkLabel(
            info_frame,
            text="Select a channel",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=MaterialColors.TEXT_PRIMARY,
            anchor="w"
        )
        self.preview_name_label.pack(anchor="w")
        
        self.preview_url_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=MaterialColors.TEXT_SECONDARY,
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
            fg_color=MaterialColors.ACCENT,
            hover_color=MaterialColors.ACCENT_DARK,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.play_btn.pack(side="right", padx=20)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_frame = ctk.CTkFrame(
            self.root,
            fg_color=MaterialColors.SURFACE,
            corner_radius=0,
            height=30
        )
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_frame.grid_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Starting...",
            font=ctk.CTkFont(size=11),
            text_color=MaterialColors.TEXT_SECONDARY
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
            hover_color=MaterialColors.SURFACE_VARIANT,
            text_color=MaterialColors.TEXT_PRIMARY,
            anchor="w",
            height=36,
            corner_radius=8
        )
        all_btn.pack(fill="x", pady=2)
        self.category_buttons.append(all_btn)
        
        # Separator
        sep = ctk.CTkFrame(self.category_scroll, height=1, fg_color=MaterialColors.SURFACE_VARIANT)
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
                hover_color=MaterialColors.SURFACE_VARIANT,
                text_color=MaterialColors.TEXT_PRIMARY,
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
        
        # Clear existing items
        self.channel_tree.delete(*self.channel_tree.get_children())
        
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
            self.preview_status_label.configure(text='✓ Working', text_color=MaterialColors.SUCCESS)
        elif is_working is False:
            self.preview_status_label.configure(text='✗ Offline', text_color=MaterialColors.ERROR)
        else:
            self.preview_status_label.configure(text='◌ Checking...', text_color=MaterialColors.WARNING)
        
        # Show thumbnail
        self._show_channel_thumbnail(channel)
    
    def _find_channel_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a channel by name."""
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
            except Exception:
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
        """Callback when channel validated - optimized for UI responsiveness."""
        progress = (current / total)
        
        if channel.get('is_working'):
            self.scan_working_count += 1
            if self.scan_working_count % 10 == 1:
                url = channel.get('url', '')
                if url and not thumbnail_exists(url):
                    capture_thumbnail_async(url)
        else:
            self.scan_failed_count += 1
        self.scan_total_count = total
        
        # Adaptive update interval based on total channels
        if total > 10000:
            update_interval = 200
        elif total > 5000:
            update_interval = 100
        else:
            update_interval = 50
        
        # Check if enough time has passed since last update
        current_time = time.time() * 1000  # ms
        time_since_last = current_time - self._last_ui_refresh
        
        should_update = (
            (current % update_interval == 0) or 
            (current == total) or 
            (current <= 3) or
            (time_since_last > 500)  # Force update every 500ms
        )
        
        if should_update:
            self._last_ui_refresh = current_time
            # Use after_idle for non-blocking UI updates
            self.root.after_idle(lambda p=progress, c=current, t=total: self._batch_ui_update(p, c, t))
        
        # Refresh group list less frequently
        refresh_interval = 500 if total > 5000 else 250
        if current % refresh_interval == 0 or current == total:
            if self._pending_group_update:
                self.root.after_cancel(self._pending_group_update)
            self._pending_group_update = self.root.after(200, self._debounced_refresh)
    
    def _batch_ui_update(self, progress: float, current: int, total: int):
        """Perform batched UI updates without blocking."""
        try:
            self.progress_var.set(progress)
            self.scan_label.configure(text=f"Scanning {current}/{total}")
            self.stats_label.configure(
                text=f"{self.scan_working_count} working • {self.scan_failed_count} failed"
            )
            # Update scan animation widget
            self.scan_animation.update_progress(current, total, self.scan_working_count, self.scan_failed_count)
            self._set_status(f"Validating channels... {current}/{total}")
            # Process any pending events to keep UI responsive
            self.root.update_idletasks()
        except Exception:
            pass  # Ignore errors if window is closing
    
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
            text_color=MaterialColors.PRIMARY
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            scroll_frame,
            text=f"Version {config.APP_VERSION}",
            font=ctk.CTkFont(size=14),
            text_color=MaterialColors.TEXT_SECONDARY
        ).pack(pady=(0, 15))
        
        # What is IPTV section
        ctk.CTkLabel(
            scroll_frame,
            text="📡 What is IPTV?",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=MaterialColors.TEXT_PRIMARY,
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
            text_color=MaterialColors.TEXT_SECONDARY,
            wraplength=480,
            justify="left"
        ).pack(fill="x", pady=(0, 10))
        
        # How it works section
        ctk.CTkLabel(
            scroll_frame,
            text="🔧 How It Works",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=MaterialColors.TEXT_PRIMARY,
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
            text_color=MaterialColors.TEXT_SECONDARY,
            wraplength=480,
            justify="left"
        ).pack(fill="x", pady=(0, 10))
        
        # Features section
        ctk.CTkLabel(
            scroll_frame,
            text="✨ Features",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=MaterialColors.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", pady=(10, 5))
        
        features = [
            "• Auto-discover IPTV repositories worldwide",
            "• Background stream validation",
            "• Filter by category, country, or media type",
            "• Material Design user interface",
            "• Embedded VLC-powered video player",
            "• Support for TV and Radio streams",
            "• Thumbnail previews for channels",
            "• No login or subscription required"
        ]
        
        for feature in features:
            ctk.CTkLabel(
                scroll_frame,
                text=feature,
                font=ctk.CTkFont(size=12),
                text_color=MaterialColors.TEXT_PRIMARY,
                anchor="w"
            ).pack(fill="x", padx=10)
        
        # Disclaimer
        ctk.CTkLabel(
            scroll_frame,
            text="⚠️ Disclaimer",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=MaterialColors.ACCENT,
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
            text_color=MaterialColors.TEXT_SECONDARY,
            wraplength=480,
            justify="left"
        ).pack(fill="x", pady=(0, 15))
        
        # Close button
        ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            width=100,
            fg_color=MaterialColors.PRIMARY,
            hover_color=MaterialColors.PRIMARY_DARK
        ).pack(pady=15)
    
    def _initialize(self):
        """Initialize on startup."""
        self._set_status("Loading cached channels...")
        self.scan_label.configure(text="Loading...")
        
        has_cache = self.channel_manager.load_cached_channels()
        if has_cache:
            self._update_groups()
            cached_count = len(self.channel_manager.channels)
            working = len(self.channel_manager.get_working_channels())
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
