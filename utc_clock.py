#!/usr/bin/env python3
"""UTC clock — big bold UTC time, copy the ISO 8601 stamp with a click."""

import time
import datetime as dt
import tkinter as tk
import tkinter.font as tkfont

# --- Identity ---
APP_NAME = "UTC clock"
VERSION = "0.1"

# --- Design tokens ---
# Mirrors the ndisc-suite fizx palette (see bpm-tapper for the same set).
# Keep in sync if the canonical palette shifts.
BG            = "#090d12"  # near-black navy field
PANEL         = "#131d2a"  # secondary surface (footer band)
FG            = "#f0f6fc"  # cool white
MUTED         = "#6b7a8d"  # cool grey-blue — secondary chrome
MUTED_ACCENT  = "#6f989d"  # MUTED warmed toward ACCENT — sub-line tone
ACCENT        = "#7af0cd"  # mint — focal HH:MM
ACCENT_DIM    = "#3f8a76"  # mint dimmed ~50% — trailing seconds, doesn't compete
OK            = "#4ade80"  # green — copy-confirm flash

# Two-tier typography. The clock digits ride Ubuntu Sans Bold (proportional
# but tabular-ish at this weight); footer info (epoch, day-of-year, ISO
# week) is mono so digit counts stay visually steady frame to frame.
TIME_FONT_SIZE  = 64
SUB_FONT_SIZE   = 16
FOOT_FONT_SIZE  = 11
ABOUT_FONT_SIZE = 11

UI_FAMILIES = ["Ubuntu Sans", "Ubuntu", "Helvetica", "Arial",
               "Liberation Sans", "DejaVu Sans"]
MONO_FAMILIES = ["Ubuntu Sans Mono", "Ubuntu Mono", "Liberation Mono",
                 "DejaVu Sans Mono", "Courier New", "Courier"]


def _resolve_family(root, preferences):
    """Pick the first preferred family that's installed; fall back to the
    last entry (Tk will substitute its own default if absent)."""
    available = {f.lower(): f for f in tkfont.families(root)}
    for fam in preferences:
        if fam.lower() in available:
            return available[fam.lower()]
    return preferences[-1]


class UTCClock:
    def __init__(self, root):
        self.root = root
        self.root.title("UTC Clock")
        self.root.geometry("520x320")
        self.root.minsize(480, 300)
        self.root.configure(bg=BG)

        self.ui = _resolve_family(root, UI_FAMILIES)
        self.mono = _resolve_family(root, MONO_FAMILIES)

        self._build_ui()
        self._bind_keys()
        self._tick()

    def _build_ui(self):
        self.about_label = tk.Label(
            self.root, text=f"{APP_NAME} v{VERSION}",
            font=(self.ui, ABOUT_FONT_SIZE),
            fg=MUTED, bg=BG, cursor="hand2",
        )
        self.about_label.place(relx=1.0, x=-12, y=10, anchor="ne")
        self.about_label.bind("<Button-1>", self._show_about)

        # Main clock — HH:MM in ACCENT, :SS in ACCENT_DIM so the
        # constantly-changing trailer doesn't tug the eye away from the
        # focal HH:MM pair. Two adjacent labels in a frame keep that
        # split cheap and let the colon between them inherit ACCENT.
        # UTC meaning lives in the title bar + date sub-line, not inline.
        clock_frame = tk.Frame(self.root, bg=BG)
        clock_frame.pack(pady=(50, 0))
        self.hm_label = tk.Label(
            clock_frame, text="--:--",
            font=(self.ui, TIME_FONT_SIZE, "bold"),
            fg=ACCENT, bg=BG, cursor="hand2",
        )
        self.hm_label.pack(side="left")
        self.ss_label = tk.Label(
            clock_frame, text=":--",
            font=(self.ui, TIME_FONT_SIZE, "bold"),
            fg=ACCENT_DIM, bg=BG, cursor="hand2",
        )
        self.ss_label.pack(side="left")

        # Date — weekday + ISO date.
        self.date_label = tk.Label(
            self.root, text="",
            font=(self.ui, SUB_FONT_SIZE),
            fg=MUTED_ACCENT, bg=BG,
        )
        self.date_label.pack(pady=(14, 0))

        # Footer info strip — day-of-year, ISO week, unix epoch. Mono so
        # the digit columns stay visually steady when the epoch ticks.
        self.foot_label = tk.Label(
            self.root, text="",
            font=(self.mono, FOOT_FONT_SIZE),
            fg=MUTED, bg=BG,
        )
        self.foot_label.pack(pady=(18, 0))

        # Inline copy hint / confirmation — sits below the footer so the
        # confirm flash doesn't displace any chrome.
        self.hint_label = tk.Label(
            self.root, text="click to copy ISO 8601",
            font=(self.ui, ABOUT_FONT_SIZE),
            fg=MUTED, bg=BG,
        )
        self.hint_label.pack(pady=(8, 0))

    def _bind_keys(self):
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<Control-c>", self._copy_iso)
        self.root.bind("<Control-C>", self._copy_iso)
        self.root.bind("<Button-1>", self._root_click)

    def _root_click(self, event):
        if event.widget is self.about_label:
            return
        self._copy_iso()

    def _show_about(self, _event=None):
        win = tk.Toplevel(self.root)
        win.title(f"About {APP_NAME}")
        win.configure(bg=BG)
        win.geometry("320x220")
        win.resizable(False, False)
        win.transient(self.root)
        tk.Label(win, text=APP_NAME,
                 font=(self.ui, 20, "bold"),
                 fg=ACCENT, bg=BG).pack(pady=(28, 0))
        tk.Label(win, text=f"version {VERSION}",
                 font=(self.mono, ABOUT_FONT_SIZE),
                 fg=MUTED, bg=BG).pack(pady=(2, 0))
        tk.Label(win,
                 text="Big UTC clock. Click to copy ISO 8601.",
                 font=(self.ui, ABOUT_FONT_SIZE),
                 fg=FG, bg=BG, wraplength=280).pack(pady=(14, 0))
        tk.Label(win, text="Python 3 · Tkinter",
                 font=(self.ui, ABOUT_FONT_SIZE),
                 fg=MUTED, bg=BG).pack(pady=(14, 0))
        tk.Label(win, text="github.com/xjmzx/utc-clock",
                 font=(self.mono, ABOUT_FONT_SIZE),
                 fg=MUTED, bg=BG).pack(pady=(2, 0))
        tk.Button(win, text="close",
                  font=(self.ui, ABOUT_FONT_SIZE),
                  bg=PANEL, fg=FG, activebackground=PANEL,
                  activeforeground=FG, relief="flat", bd=0,
                  padx=14, pady=6, cursor="hand2",
                  command=win.destroy).pack(pady=(18, 0))
        win.bind("<Escape>", lambda e: win.destroy())

    def _copy_iso(self, _event=None):
        now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        # Trailing Z is the canonical UTC ISO 8601 form.
        stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.root.clipboard_clear()
        self.root.clipboard_append(stamp)
        self.hint_label.config(text=f"copied {stamp}", fg=OK)
        self.root.after(1100, self._reset_hint)

    def _reset_hint(self):
        self.hint_label.config(text="click to copy ISO 8601", fg=MUTED)

    def _tick(self):
        now = dt.datetime.now(dt.timezone.utc)
        self.hm_label.config(text=now.strftime("%H:%M"))
        self.ss_label.config(text=now.strftime(":%S"))
        # Weekday + ISO date + UTC label — one line, three registers.
        self.date_label.config(
            text=now.strftime("%A · %Y-%m-%d · UTC"))
        iso = now.isocalendar()
        epoch = int(now.timestamp())
        self.foot_label.config(
            text=f"day {now.timetuple().tm_yday:03d}   "
                 f"week {iso.week:02d}   "
                 f"epoch {epoch}")
        # 200ms refresh — the seconds digit only changes once per second
        # but a sub-second tick keeps the displayed value never more than
        # ~200ms stale (matters for the copy-action latency feel).
        self.root.after(200, self._tick)


def main():
    root = tk.Tk()
    UTCClock(root)
    root.mainloop()


if __name__ == "__main__":
    main()
