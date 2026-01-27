"""
TV Viewer for Android - Kivy-based mobile IPTV application

This is a mobile-optimized version of TV Viewer for Android devices.
Built with Kivy for native Android experience.

Target: Samsung Galaxy S24 Ultra and similar Android devices
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Any, Optional
from functools import partial

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.properties import StringProperty, BooleanProperty, ListProperty, NumericProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from kivy.metrics import dp

# Android-specific imports
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android import activity
    from jnius import autoclass
    
    # Java classes for video playback
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')


# Color scheme (Windows 11 Fluent-inspired)
COLORS = {
    'bg_primary': (0.122, 0.122, 0.122, 1),      # #1F1F1F
    'bg_secondary': (0.173, 0.173, 0.173, 1),    # #2C2C2C
    'bg_card': (0.176, 0.176, 0.176, 1),         # #2D2D2D
    'accent': (0, 0.471, 0.831, 1),              # #0078D4
    'accent_light': (0.376, 0.804, 1, 1),        # #60CDFF
    'text_primary': (1, 1, 1, 1),                # White
    'text_secondary': (0.616, 0.616, 0.616, 1),  # #9D9D9D
    'success': (0.424, 0.796, 0.373, 1),         # #6CCB5F
    'error': (1, 0.420, 0.420, 1),               # #FF6B6B
    'warning': (0.988, 0.882, 0, 1),             # #FCE100
}


class ChannelItem(RecycleDataViewBehavior, BoxLayout):
    """Individual channel item in the list."""
    
    name = StringProperty('')
    category = StringProperty('')
    is_working = BooleanProperty(True)
    url = StringProperty('')
    index = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(60)
        self.padding = dp(10)
        self.spacing = dp(10)
    
    def refresh_view_attrs(self, rv, index, data):
        """Update view with data."""
        self.index = index
        self.name = data.get('name', 'Unknown')
        self.category = data.get('category', '')
        self.is_working = data.get('is_working', True)
        self.url = data.get('url', '')
        return super().refresh_view_attrs(rv, index, data)
    
    def on_touch_down(self, touch):
        """Handle touch to play channel."""
        if self.collide_point(*touch.pos):
            app = App.get_running_app()
            app.play_channel(self.url, self.name)
            return True
        return super().on_touch_down(touch)


class ChannelList(RecycleView):
    """Scrollable list of channels using RecycleView for performance."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.viewclass = 'ChannelItem'
        
        # Use GridLayout for the recycle view
        self.layout_manager = RecycleGridLayout(
            cols=1,
            default_size=(None, dp(60)),
            default_size_hint=(1, None),
            size_hint_y=None
        )
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))
        self.add_widget(self.layout_manager)


class TVViewerApp(App):
    """Main TV Viewer Android Application."""
    
    channels = ListProperty([])
    filtered_channels = ListProperty([])
    categories = ListProperty([])
    current_category = StringProperty('All')
    search_query = StringProperty('')
    is_loading = BooleanProperty(False)
    status_text = StringProperty('Ready')
    
    # IPTV Repository URLs
    REPOSITORIES = [
        'https://iptv-org.github.io/iptv/index.m3u',
        'https://iptv-org.github.io/iptv/index.category.m3u',
    ]
    
    def build(self):
        """Build the application UI."""
        Window.clearcolor = COLORS['bg_primary']
        
        # Request Android permissions
        if platform == 'android':
            request_permissions([Permission.INTERNET, Permission.WRITE_EXTERNAL_STORAGE])
        
        # Main layout
        self.root = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Header
        header = self._create_header()
        self.root.add_widget(header)
        
        # Search bar
        search_bar = self._create_search_bar()
        self.root.add_widget(search_bar)
        
        # Category filter
        category_bar = self._create_category_bar()
        self.root.add_widget(category_bar)
        
        # Channel list
        self.channel_list = ChannelList()
        self.root.add_widget(self.channel_list)
        
        # Status bar
        status_bar = self._create_status_bar()
        self.root.add_widget(status_bar)
        
        # Load channels on startup
        Clock.schedule_once(lambda dt: self.load_channels(), 1)
        
        return self.root
    
    def _create_header(self):
        """Create app header."""
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=dp(5)
        )
        
        title = Label(
            text='📺 TV Viewer',
            font_size=dp(24),
            bold=True,
            color=COLORS['accent_light'],
            halign='left'
        )
        header.add_widget(title)
        
        # Refresh button
        refresh_btn = Button(
            text='🔄',
            size_hint_x=None,
            width=dp(50),
            background_color=COLORS['accent'],
            on_press=lambda x: self.load_channels()
        )
        header.add_widget(refresh_btn)
        
        return header
    
    def _create_search_bar(self):
        """Create search input."""
        search_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(45),
            spacing=dp(10)
        )
        
        self.search_input = TextInput(
            hint_text='🔍 Search channels...',
            multiline=False,
            background_color=COLORS['bg_card'],
            foreground_color=COLORS['text_primary'],
            hint_text_color=COLORS['text_secondary'],
            padding=(dp(15), dp(10)),
            font_size=dp(16)
        )
        self.search_input.bind(text=self.on_search)
        search_layout.add_widget(self.search_input)
        
        return search_layout
    
    def _create_category_bar(self):
        """Create category filter."""
        category_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(5)
        )
        
        Label(
            text='Category:',
            size_hint_x=None,
            width=dp(80),
            color=COLORS['text_secondary']
        )
        category_layout.add_widget(Label(text=''))  # Spacer
        
        self.category_spinner = Spinner(
            text='All',
            values=['All'],
            size_hint_x=None,
            width=dp(200),
            background_color=COLORS['bg_card']
        )
        self.category_spinner.bind(text=self.on_category_change)
        category_layout.add_widget(self.category_spinner)
        
        return category_layout
    
    def _create_status_bar(self):
        """Create status bar."""
        status_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30)
        )
        
        self.status_label = Label(
            text='Ready',
            color=COLORS['text_secondary'],
            font_size=dp(12),
            halign='left'
        )
        status_layout.add_widget(self.status_label)
        
        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_x=0.3
        )
        status_layout.add_widget(self.progress_bar)
        
        return status_layout
    
    def load_channels(self):
        """Load channels from repositories."""
        if self.is_loading:
            return
        
        self.is_loading = True
        self.status_label.text = 'Loading channels...'
        self.progress_bar.value = 0
        
        # Run async loading
        asyncio.ensure_future(self._async_load_channels())
    
    async def _async_load_channels(self):
        """Async channel loading."""
        all_channels = []
        seen_urls = set()
        
        try:
            async with aiohttp.ClientSession() as session:
                for i, repo_url in enumerate(self.REPOSITORIES):
                    try:
                        async with session.get(repo_url, timeout=30) as response:
                            if response.status == 200:
                                content = await response.text()
                                channels = self._parse_m3u(content)
                                
                                for ch in channels:
                                    url = ch.get('url', '')
                                    if url and url not in seen_urls:
                                        seen_urls.add(url)
                                        all_channels.append(ch)
                    except Exception as e:
                        print(f"Error fetching {repo_url}: {e}")
                    
                    # Update progress
                    progress = ((i + 1) / len(self.REPOSITORIES)) * 100
                    Clock.schedule_once(
                        lambda dt, p=progress: setattr(self.progress_bar, 'value', p),
                        0
                    )
        except Exception as e:
            print(f"Error loading channels: {e}")
        
        # Update UI on main thread
        Clock.schedule_once(lambda dt: self._on_channels_loaded(all_channels), 0)
    
    def _on_channels_loaded(self, channels: List[Dict[str, Any]]):
        """Called when channels are loaded."""
        self.channels = channels
        
        # Extract categories
        categories = set()
        for ch in channels:
            cat = ch.get('category', 'Other')
            if cat:
                categories.add(cat)
        
        self.categories = ['All'] + sorted(categories)
        self.category_spinner.values = self.categories
        
        # Filter and display
        self.filter_channels()
        
        self.is_loading = False
        self.status_label.text = f'{len(channels)} channels loaded'
        self.progress_bar.value = 100
    
    def _parse_m3u(self, content: str) -> List[Dict[str, Any]]:
        """Parse M3U playlist content."""
        channels = []
        lines = content.split('\n')
        
        current_channel = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('#EXTINF:'):
                # Parse channel info
                current_channel = {}
                
                # Extract name (after last comma)
                if ',' in line:
                    current_channel['name'] = line.split(',')[-1].strip()
                
                # Extract attributes
                if 'group-title="' in line:
                    start = line.index('group-title="') + 13
                    end = line.index('"', start)
                    current_channel['category'] = line[start:end]
                
                if 'tvg-logo="' in line:
                    start = line.index('tvg-logo="') + 10
                    end = line.index('"', start)
                    current_channel['logo'] = line[start:end]
            
            elif line and not line.startswith('#'):
                # This is the URL
                if line.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
                    current_channel['url'] = line
                    current_channel['is_working'] = True  # Assume working
                    channels.append(current_channel)
                    current_channel = {}
        
        return channels
    
    def on_search(self, instance, value):
        """Handle search input change."""
        self.search_query = value
        self.filter_channels()
    
    def on_category_change(self, instance, value):
        """Handle category filter change."""
        self.current_category = value
        self.filter_channels()
    
    def filter_channels(self):
        """Filter channels based on search and category."""
        filtered = self.channels
        
        # Filter by category
        if self.current_category != 'All':
            filtered = [ch for ch in filtered if ch.get('category') == self.current_category]
        
        # Filter by search query
        if self.search_query:
            query = self.search_query.lower()
            filtered = [ch for ch in filtered if query in ch.get('name', '').lower()]
        
        # Update list
        self.filtered_channels = filtered
        self.channel_list.data = filtered
        
        # Update status
        self.status_label.text = f'{len(filtered)} channels'
    
    def play_channel(self, url: str, name: str):
        """Play a channel stream."""
        if not url:
            return
        
        self.status_label.text = f'Playing: {name}'
        
        if platform == 'android':
            # Open in external video player (VLC, MX Player, etc.)
            try:
                intent = Intent(Intent.ACTION_VIEW)
                intent.setDataAndType(Uri.parse(url), "video/*")
                intent.putExtra("title", name)
                
                # Try to use VLC specifically
                intent.setPackage("org.videolan.vlc")
                
                current_activity = PythonActivity.mActivity
                current_activity.startActivity(intent)
            except Exception as e:
                # Fallback to any video player
                try:
                    intent = Intent(Intent.ACTION_VIEW)
                    intent.setDataAndType(Uri.parse(url), "video/*")
                    current_activity = PythonActivity.mActivity
                    current_activity.startActivity(intent)
                except Exception as e2:
                    self._show_error(f"Could not play stream: {e2}")
        else:
            # Desktop fallback - just print URL
            print(f"Would play: {url}")
            self._show_info(f"Playing: {name}\n\n{url}")
    
    def _show_error(self, message: str):
        """Show error popup."""
        popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()
    
    def _show_info(self, message: str):
        """Show info popup."""
        popup = Popup(
            title='Info',
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()


# Register custom widget for RecycleView
from kivy.factory import Factory
Factory.register('ChannelItem', cls=ChannelItem)


if __name__ == '__main__':
    # For async support
    import asyncio
    from kivy.config import Config
    
    # Optimize for mobile
    Config.set('graphics', 'multisamples', '0')
    Config.set('kivy', 'log_level', 'info')
    
    # Run app
    loop = asyncio.get_event_loop()
    app = TVViewerApp()
    
    # Handle async
    async def run_app():
        await app.async_run(async_lib='asyncio')
    
    try:
        loop.run_until_complete(run_app())
    except Exception as e:
        print(f"App error: {e}")
        app.run()
