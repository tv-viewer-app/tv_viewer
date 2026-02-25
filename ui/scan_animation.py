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
    
    # Color palettes (light theme compatible)
    COLORS = {
        '0': '',  # Transparent
        '1': '#1e90ff',  # Ocean blue
        '2': '#228b22',  # Land green
        '3': '#ffffff',  # Clouds white
        '4': '#104e8b',  # Dark ocean
    }
    
    # Signal wave colors (green)
    SIGNAL_COLORS = ['#00cc00', '#00aa00', '#008800', '#006600', '#004400']
    
    def __init__(self, parent, width=180, height=80, **kwargs):
        # Light theme background
        super().__init__(parent, width=width, height=height, 
                        bg='#E8E8E8', highlightthickness=0, **kwargs)
        
        self.width = width
        self.height = height
        self.progress = 0.0
        self.working_count = 0
        self.failed_count = 0
        self.total_count = 0
        self.pixel_size = 2
        self.animation_frame = 0
        self._animation_job = None
        self.is_scanning = False
        
        # Satellite dish position
        self.dish_x = width - 40
        self.dish_y = height - 25
        
        # Start animation
        self._animate()
    
    def set_progress(self, progress: float, working: int, failed: int, total: int):
        """Update the scan progress."""
        self.progress = min(1.0, max(0.0, progress))
        self.working_count = working
        self.failed_count = failed
        self.total_count = total
        self.is_scanning = progress < 1.0 and total > 0
    
    def set_stopped(self):
        """Mark scan as stopped (Issue #34)."""
        self.is_scanning = False
    
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
        
        # Dish base colors
        dish_color = '#808080'
        dish_dark = '#505050'
        
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
        bar_y = self.height - 12
        bar_width = self.width - 20
        bar_height = 6
        
        # Background (light theme)
        self.create_rectangle(
            bar_x, bar_y, bar_x + bar_width, bar_y + bar_height,
            fill='#C0C0C0', outline='#A0A0A0'
        )
        
        # Progress fill
        if self.progress > 0 and self.total_count > 0:
            # Working portion (green)
            working_ratio = self.working_count / self.total_count
            working_width = int(bar_width * working_ratio * self.progress)
            if working_width > 0:
                self.create_rectangle(
                    bar_x, bar_y, bar_x + working_width, bar_y + bar_height,
                    fill='#107C10', outline=''
                )
            
            # Failed portion (red)
            failed_ratio = self.failed_count / self.total_count
            failed_width = int(bar_width * failed_ratio * self.progress)
            if failed_width > 0:
                self.create_rectangle(
                    bar_x + working_width, bar_y,
                    bar_x + working_width + failed_width, bar_y + bar_height,
                    fill='#C42B1C', outline=''
                )
    
    def _draw_stats(self):
        """Draw scan statistics and percentage - FIXED layout (Issue #34)."""
        if self.total_count > 0:
            # Stats text at bottom (most important data)
            stats_text = f"{self.working_count} ok • {self.failed_count} fail"
            self.create_text(
                self.width // 2, self.height - 8,
                text=stats_text, fill='#333333',
                font=('Segoe UI', 10)  # Slightly larger
            )
            
            # Only show percentage when scan is active (Issue #30)
            pct = int(self.progress * 100)
            self.create_text(
                self.width - 25, 12,
                text=f"{pct}%", 
                fill='#107C10' if pct == 100 else '#0078D4',
                font=('Segoe UI', 14, 'bold')
            )
    
    def _draw_scanning_text(self):
        """Draw status text with proper 'Stopped' state (Issue #34)."""
        if self.is_scanning:
            dots = '.' * ((self.animation_frame // 5) % 4)
            text = f"Scanning{dots}"
            color = '#0078D4'
        elif self.progress >= 1.0:
            text = "Complete!"
            color = '#107C10'
        elif self.progress > 0:
            # FIXED: Show "Stopped" when scan was stopped mid-way (Issue #34)
            text = "Stopped"
            color = '#FF6B6B'  # Red-ish to indicate interruption
        else:
            # Idle state - hide text to reduce clutter
            text = ""
            color = '#666666'
        
        if text:  # Only draw if not empty
            self.create_text(
                self.width // 2, self.height - 22,  # Above stats, below percentage
                text=text, fill=color,
                font=('Segoe UI', 8, 'italic')  # Smaller, subtle
            )
    
    def _animate(self):
        """Animation loop."""
        self.delete('all')
        
        # Draw all elements
        self._draw_earth(15, 18)
        self._draw_satellite_dish()
        self._draw_signal_waves()
        self._draw_progress_bar()
        self._draw_stats()
        self._draw_scanning_text()
        
        self.animation_frame += 1
        
        # Schedule next frame (800ms — lighter on CPU during resize)
        self._animation_job = self.after(800, self._animate)
    
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
        self.animation = ScanAnimationWidget(self, width=180, height=80)
        self.animation.pack(pady=2)
    
    def update_progress(self, current: int, total: int, working: int, failed: int):
        """Update the scan progress display."""
        if total > 0:
            progress = current / total
        else:
            progress = 0
        self.animation.set_progress(progress, working, failed, total)
    
    def set_complete(self, working: int, total: int):
        """Set scan as complete."""
        self.animation.set_progress(1.0, working, total - working, total)
    
    def set_stopped(self):
        """Mark scan as stopped (Issue #34)."""
        self.animation.set_stopped()
    
    def destroy(self):
        """Clean up."""
        self.animation.stop_animation()
        super().destroy()
