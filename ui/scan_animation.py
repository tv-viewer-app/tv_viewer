"""Pixel art animation widget for scan progress."""

import tkinter as tk
from tkinter import ttk
from typing import Optional
import math


class ScanAnimationWidget(tk.Canvas):
    """Animated pixel art Earth with satellite dish showing scan progress."""
    
    # Pixel art frames for Earth (16x16)
    EARTH_PIXELS = [
        # Frame colors: 0=transparent, 1=ocean, 2=land, 3=clouds, 4=dark ocean
        [
            "0000011111100000",
            "0001111211110000",
            "0011122221111000",
            "0112222211141100",
            "1112211111141110",
            "1122111122111110",
            "1121111222211111",
            "1111112222221111",
            "1111222221111111",
            "1112222111111111",
            "1112211111111110",
            "0111111111111110",
            "0111111111111100",
            "0011111111111000",
            "0001111111110000",
            "0000011111000000",
        ],
    ]
    
    # Color palettes
    COLORS = {
        '0': '',  # Transparent
        '1': '#1e90ff',  # Ocean blue
        '2': '#228b22',  # Land green
        '3': '#ffffff',  # Clouds white
        '4': '#104e8b',  # Dark ocean
    }
    
    # Signal wave colors
    SIGNAL_COLORS = ['#00ff00', '#00dd00', '#00bb00', '#009900', '#007700']
    
    def __init__(self, parent, width=200, height=100, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        bg='#1a1a2e', highlightthickness=0, **kwargs)
        
        self.width = width
        self.height = height
        self.progress = 0.0
        self.working_count = 0
        self.failed_count = 0
        self.total_count = 0
        self.pixel_size = 3
        self.animation_frame = 0
        self._animation_job = None
        self.is_scanning = False
        
        # Satellite dish position
        self.dish_x = width - 50
        self.dish_y = height - 30
        
        # Start animation
        self._animate()
    
    def set_progress(self, progress: float, working: int, failed: int, total: int):
        """Update the scan progress."""
        self.progress = min(1.0, max(0.0, progress))
        self.working_count = working
        self.failed_count = failed
        self.total_count = total
        self.is_scanning = progress < 1.0 and total > 0
    
    def _draw_earth(self, offset_x: int, offset_y: int):
        """Draw the pixel art Earth."""
        earth = self.EARTH_PIXELS[0]
        
        # Rotation effect based on animation frame
        rotation_offset = self.animation_frame % 16
        
        for y, row in enumerate(earth):
            for x, pixel in enumerate(row):
                if pixel != '0':
                    color = self.COLORS.get(pixel, '#ffffff')
                    # Apply rotation by shifting x
                    draw_x = (x + rotation_offset) % 16
                    self.create_rectangle(
                        offset_x + draw_x * self.pixel_size,
                        offset_y + y * self.pixel_size,
                        offset_x + (draw_x + 1) * self.pixel_size,
                        offset_y + (y + 1) * self.pixel_size,
                        fill=color, outline=''
                    )
    
    def _draw_satellite_dish(self):
        """Draw a pixel art satellite dish."""
        x, y = self.dish_x, self.dish_y
        ps = 2  # Pixel size for dish
        
        # Dish base (triangle/parabola shape)
        dish_color = '#c0c0c0'
        dish_dark = '#808080'
        
        # Dish shape
        dish_pixels = [
            "  111  ",
            " 11111 ",
            "1111111",
            " 11111 ",
            "  111  ",
            "   1   ",
            "   1   ",
            "  111  ",
        ]
        
        for row_idx, row in enumerate(dish_pixels):
            for col_idx, pixel in enumerate(row):
                if pixel == '1':
                    color = dish_color if row_idx < 5 else dish_dark
                    self.create_rectangle(
                        x + col_idx * ps,
                        y + row_idx * ps,
                        x + (col_idx + 1) * ps,
                        y + (row_idx + 1) * ps,
                        fill=color, outline=''
                    )
    
    def _draw_signal_waves(self):
        """Draw animated signal waves between dish and earth."""
        if not self.is_scanning:
            return
        
        # Draw expanding circles from dish
        dish_cx = self.dish_x + 7
        dish_cy = self.dish_y + 5
        
        for i in range(3):
            wave_offset = (self.animation_frame + i * 5) % 20
            if wave_offset < 15:
                radius = 5 + wave_offset * 2
                alpha_idx = min(4, wave_offset // 3)
                color = self.SIGNAL_COLORS[alpha_idx]
                
                # Draw arc towards earth
                self.create_arc(
                    dish_cx - radius, dish_cy - radius,
                    dish_cx + radius, dish_cy + radius,
                    start=120, extent=60,
                    outline=color, width=2, style='arc'
                )
    
    def _draw_progress_bar(self):
        """Draw a progress bar at the bottom."""
        bar_x = 10
        bar_y = self.height - 15
        bar_width = self.width - 20
        bar_height = 8
        
        # Background
        self.create_rectangle(
            bar_x, bar_y, bar_x + bar_width, bar_y + bar_height,
            fill='#333333', outline='#555555'
        )
        
        # Progress fill with gradient effect
        if self.progress > 0:
            fill_width = int(bar_width * self.progress)
            
            # Working portion (green)
            if self.total_count > 0:
                working_ratio = self.working_count / self.total_count
                working_width = int(bar_width * working_ratio * self.progress)
                if working_width > 0:
                    self.create_rectangle(
                        bar_x, bar_y, bar_x + working_width, bar_y + bar_height,
                        fill='#00ff00', outline=''
                    )
                
                # Failed portion (red) - after working
                failed_ratio = self.failed_count / self.total_count
                failed_width = int(bar_width * failed_ratio * self.progress)
                if failed_width > 0:
                    self.create_rectangle(
                        bar_x + working_width, bar_y,
                        bar_x + working_width + failed_width, bar_y + bar_height,
                        fill='#ff4444', outline=''
                    )
    
    def _draw_stats(self):
        """Draw scan statistics."""
        # Stats text
        if self.total_count > 0:
            stats_text = f"✓{self.working_count}  ✗{self.failed_count}  ◷{self.total_count - self.working_count - self.failed_count}"
            self.create_text(
                self.width // 2, 10,
                text=stats_text, fill='#ffffff',
                font=('Consolas', 9, 'bold')
            )
        
        # Percentage
        pct = int(self.progress * 100)
        self.create_text(
            self.width // 2, self.height - 22,
            text=f"{pct}%", fill='#00ff00' if pct == 100 else '#ffff00',
            font=('Consolas', 8, 'bold')
        )
    
    def _draw_scanning_text(self):
        """Draw 'SCANNING' text with animation."""
        if self.is_scanning:
            dots = '.' * ((self.animation_frame // 5) % 4)
            text = f"SCANNING{dots}"
        elif self.progress >= 1.0:
            text = "COMPLETE!"
        else:
            text = "READY"
        
        self.create_text(
            self.width // 2, self.height // 2 + 25,
            text=text, fill='#00ffff',
            font=('Consolas', 10, 'bold')
        )
    
    def _draw_stars(self):
        """Draw twinkling stars in background."""
        import random
        random.seed(42)  # Consistent star positions
        
        for _ in range(20):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height - 20)
            
            # Twinkle effect
            brightness = 150 + int(50 * math.sin(self.animation_frame * 0.1 + x))
            color = f'#{brightness:02x}{brightness:02x}{brightness:02x}'
            
            self.create_rectangle(x, y, x+1, y+1, fill=color, outline='')
    
    def _animate(self):
        """Animation loop."""
        self.delete('all')
        
        # Draw all elements
        self._draw_stars()
        self._draw_earth(20, 25)
        self._draw_satellite_dish()
        self._draw_signal_waves()
        self._draw_progress_bar()
        self._draw_stats()
        self._draw_scanning_text()
        
        self.animation_frame += 1
        
        # Schedule next frame (reduced from 100ms to 150ms to save CPU)
        self._animation_job = self.after(150, self._animate)
    
    def stop_animation(self):
        """Stop the animation loop."""
        if self._animation_job:
            self.after_cancel(self._animation_job)
            self._animation_job = None
    
    def destroy(self):
        """Clean up when widget is destroyed."""
        self.stop_animation()
        super().destroy()


class ScanProgressFrame(ttk.Frame):
    """Frame containing the scan animation and detailed stats."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Animation widget
        self.animation = ScanAnimationWidget(self, width=200, height=100)
        self.animation.pack(pady=5)
        
        # Detailed stats label
        self.stats_label = ttk.Label(
            self, text="Waiting to scan...",
            font=('Consolas', 8)
        )
        self.stats_label.pack()
    
    def update_progress(self, current: int, total: int, working: int, failed: int):
        """Update the scan progress display."""
        if total > 0:
            progress = current / total
        else:
            progress = 0
        
        checking = current - working - failed
        
        self.animation.set_progress(progress, working, failed, total)
        self.stats_label.config(
            text=f"Scanned: {current}/{total} | Working: {working} | Failed: {failed}"
        )
    
    def set_complete(self, working: int, total: int):
        """Set scan as complete."""
        self.animation.set_progress(1.0, working, total - working, total)
        self.stats_label.config(
            text=f"Complete! {working}/{total} channels working"
        )
    
    def destroy(self):
        """Clean up."""
        self.animation.stop_animation()
        super().destroy()
