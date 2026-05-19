"""Spectrum analyzer visualizer for radio/audio-only playback.

Renders animated frequency bars on a tkinter Canvas when no video
track is present. Uses simulated spectrum data derived from VLC
audio stats to keep CPU usage minimal (~2-3% at 24fps).
"""

import math
import random
import tkinter as tk
from typing import Optional

# Bar configuration
NUM_BARS = 32
BAR_GAP = 3
MIN_HEIGHT_FRAC = 0.02   # minimum bar height as fraction of canvas height
MAX_HEIGHT_FRAC = 0.85   # maximum bar height
SMOOTHING = 0.25         # exponential smoothing (lower = smoother)
DECAY = 0.92             # per-frame decay (gravity effect)
FPS = 24                 # target frame rate
FRAME_MS = 1000 // FPS

# Color gradient (bottom to top): deep blue → cyan → white
GRADIENT = [
    "#0d47a1", "#1565c0", "#1976d2", "#1e88e5",
    "#2196f3", "#42a5f5", "#64b5f6", "#90caf9",
    "#00bcd4", "#26c6da", "#4dd0e1", "#80deea",
    "#b2ebf2", "#e0f7fa", "#ffffff",
]


class SpectrumVisualizer:
    """Canvas-based spectrum analyzer for audio-only streams."""

    def __init__(self, canvas: tk.Canvas):
        self._canvas = canvas
        self._running = False
        self._timer_id: Optional[str] = None

        # Bar state: current heights (0.0 – 1.0)
        self._bars = [0.0] * NUM_BARS
        # Peak hold
        self._peaks = [0.0] * NUM_BARS
        self._peak_hold = [0] * NUM_BARS  # frames since peak set

        # Phase accumulators for pseudo-random but smooth animation
        self._phases = [random.uniform(0, math.tau) for _ in range(NUM_BARS)]
        self._speeds = [random.uniform(1.5, 4.0) for _ in range(NUM_BARS)]

        # External energy input (0.0 – 1.0) from VLC stats
        self._energy = 0.5

    def start(self):
        """Start the animation loop."""
        if self._running:
            return
        self._running = True
        self._animate()

    def stop(self):
        """Stop the animation loop and clear canvas."""
        self._running = False
        if self._timer_id is not None:
            try:
                self._canvas.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None

    def set_energy(self, level: float):
        """Set audio energy level (0.0 – 1.0) from external source."""
        self._energy = max(0.0, min(1.0, level))

    def _animate(self):
        """Single animation frame."""
        if not self._running:
            return
        self._update_bars()
        self._draw()
        self._timer_id = self._canvas.after(FRAME_MS, self._animate)

    def _update_bars(self):
        """Update bar heights with smooth pseudo-spectrum motion."""
        energy = self._energy
        for i in range(NUM_BARS):
            # Sine-based oscillation + energy modulation
            self._phases[i] += self._speeds[i] * 0.08
            # Mix multiple frequencies for natural look
            base = (math.sin(self._phases[i]) + 1.0) * 0.5
            harmonic = (math.sin(self._phases[i] * 2.3 + i * 0.7) + 1.0) * 0.25
            # Center bars higher (simulates typical audio spectrum shape)
            center_weight = 1.0 - abs(i - NUM_BARS / 2) / (NUM_BARS / 2)
            center_weight = 0.4 + 0.6 * center_weight

            target = (base + harmonic) * energy * center_weight
            target = max(MIN_HEIGHT_FRAC, min(MAX_HEIGHT_FRAC, target))

            # Smooth approach
            current = self._bars[i]
            if target > current:
                self._bars[i] = current + (target - current) * SMOOTHING
            else:
                self._bars[i] = current * DECAY

            # Peak hold
            if self._bars[i] >= self._peaks[i]:
                self._peaks[i] = self._bars[i]
                self._peak_hold[i] = 0
            else:
                self._peak_hold[i] += 1
                if self._peak_hold[i] > 18:  # hold ~0.75s then drop
                    self._peaks[i] *= 0.95

    def _draw(self):
        """Render bars on canvas."""
        canvas = self._canvas
        try:
            cw = canvas.winfo_width()
            ch = canvas.winfo_height()
        except Exception:
            return
        if cw < 10 or ch < 10:
            return

        canvas.delete("spectrum")

        total_bar_width = cw - 80  # margins
        bar_w = max(4, (total_bar_width - (NUM_BARS - 1) * BAR_GAP) // NUM_BARS)
        actual_width = NUM_BARS * bar_w + (NUM_BARS - 1) * BAR_GAP
        x_offset = (cw - actual_width) // 2
        y_bottom = int(ch * 0.88)
        max_h = int(ch * 0.7)

        for i in range(NUM_BARS):
            x = x_offset + i * (bar_w + BAR_GAP)
            bar_h = int(self._bars[i] * max_h)
            if bar_h < 2:
                bar_h = 2

            # Draw bar with gradient segments
            segments = min(len(GRADIENT), max(1, bar_h // 6))
            seg_h = bar_h / segments
            for s in range(segments):
                y_top = y_bottom - int((s + 1) * seg_h)
                y_bot = y_bottom - int(s * seg_h)
                color_idx = int(s * (len(GRADIENT) - 1) / max(1, segments - 1))
                color = GRADIENT[min(color_idx, len(GRADIENT) - 1)]
                canvas.create_rectangle(
                    x, y_top, x + bar_w, y_bot,
                    fill=color, outline="", tags="spectrum"
                )

            # Peak indicator (thin bright line)
            peak_y = y_bottom - int(self._peaks[i] * max_h)
            if peak_y < y_bottom - 4:
                canvas.create_rectangle(
                    x, peak_y, x + bar_w, peak_y + 2,
                    fill="#ffffff", outline="", tags="spectrum"
                )

        # Reflection (subtle mirrored bars below baseline)
        reflect_max = int(ch * 0.08)
        for i in range(NUM_BARS):
            x = x_offset + i * (bar_w + BAR_GAP)
            ref_h = int(self._bars[i] * reflect_max)
            if ref_h > 1:
                canvas.create_rectangle(
                    x, y_bottom + 2, x + bar_w, y_bottom + 2 + ref_h,
                    fill="#1a237e", outline="", tags="spectrum"
                )
