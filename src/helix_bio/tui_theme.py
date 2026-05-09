"""Helix-Bio brand — DNA green + bone white, double-helix logo."""
from __future__ import annotations

from harness_tui.theme import Theme
from harness_tui.themes import catppuccin_mocha

HELIX_LOGO = r"""
   [bold #22C55E]╲[/]   [bold #F9FAFB]╱[/]
    [bold #22C55E]╲[/] [bold #F9FAFB]╱[/]
     [bold #22C55E]╳[/]
    [bold #F9FAFB]╱[/] [bold #22C55E]╲[/]      [dim]Helix-Bio[/]
   [bold #F9FAFB]╱[/]   [bold #22C55E]╲[/]
""".strip("\n")


def helix_theme() -> Theme:
    return catppuccin_mocha().with_brand(
        name="helix-bio",
        primary="#22C55E",
        primary_alt="#16A34A",
        accent="#F9FAFB",
        ascii_logo=HELIX_LOGO,
        spinner_frames=("◜", "◝", "◞", "◟"),
    )
