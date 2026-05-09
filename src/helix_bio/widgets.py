"""Helix-Bio project widgets — faithfulness ledger + dual-use banner."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static


AnchorState = Literal["anchored", "unanchored", "contested"]
_ANCHOR_STYLE = {
    "anchored":   ("checkmark", "green"),
    "unanchored": ("cross",     "red"),
    "contested":  ("partial",   "yellow"),
}
_GLYPHS = {"checkmark": "OK", "cross": "X", "partial": "?"}


@dataclass
class Claim:
    id: str
    text: str
    source: str
    state: AnchorState
    confidence: float


@dataclass
class DualUseStatus:
    triggered: bool = False
    rule: str = ""
    rationale: str = ""
    hitl_required: bool = False


_DEMO_CLAIMS: List[Claim] = [
    Claim("c1", "Spike RBD binds ACE2 with KD around 15 nM",
          "UniProt:P0DTC2", "anchored", 0.93),
    Claim("c2", "K417N substitution reduces antibody neutralization",
          "PDB:7BWJ + literature", "anchored", 0.81),
    Claim("c3", "Furin cleavage site is unique to SARS-CoV-2",
          "(no source)", "unanchored", 0.55),
    Claim("c4", "Omicron BA.5 has higher fitness than BA.2",
          "literature (mixed)", "contested", 0.62),
    Claim("c5", "Insulin signaling activates AKT via PI3K",
          "UniProt:P31749 + KEGG", "anchored", 0.97),
]


_DEMO_DUAL_USE = DualUseStatus(
    triggered=False,
    rule="dual-use-bio.v3",
    rationale="no gain-of-function pattern detected; PII redacted; HITL ready.",
)


class FaithfulnessLedger(Vertical):
    DEFAULT_CSS = """
    FaithfulnessLedger {
        height: 1fr;
    }
    FaithfulnessLedger #dualuse {
        height: 4;
        padding: 0 1;
        background: $bg_alt;
    }
    FaithfulnessLedger #ledger {
        height: 1fr;
        padding: 0 1;
        background: $bg;
    }
    """

    def __init__(self,
                 claims: List[Claim] | None = None,
                 dual_use: DualUseStatus | None = None) -> None:
        super().__init__()
        self.claims = list(claims) if claims is not None else list(_DEMO_CLAIMS)
        self.dual_use = dual_use or _DEMO_DUAL_USE

    def compose(self) -> ComposeResult:
        yield Static(self._render_dual_use(), id="dualuse")
        yield Static(self._render_ledger(), id="ledger")

    def _render_dual_use(self) -> Panel:
        if self.dual_use.triggered:
            head = Text("DUAL-USE FLAG", style="bold red")
            head.append("\n")
            head.append(escape(self.dual_use.rule), style="red")
            head.append("\n")
            head.append(escape(self.dual_use.rationale), style="default")
            if self.dual_use.hitl_required:
                head.append("\n[HITL REQUIRED]", style="bold red")
            border = "red"
        else:
            head = Text("dual-use: clear", style="bold green")
            head.append("\n")
            head.append(escape(self.dual_use.rule or "(no rule loaded)"),
                        style="dim")
            head.append("\n")
            head.append(escape(self.dual_use.rationale), style="dim")
            border = "green"
        return Panel(head, title="[bold]safety[/]", title_align="left",
                     border_style=border)

    def _render_ledger(self) -> Panel:
        anchored = sum(1 for c in self.claims if c.state == "anchored")
        unanchored = sum(1 for c in self.claims if c.state == "unanchored")
        contested = sum(1 for c in self.claims if c.state == "contested")
        title = (f"[bold]ledger[/]  "
                 f"[green]{anchored} anchored[/]  "
                 f"[red]{unanchored} unanchored[/]  "
                 f"[yellow]{contested} contested[/]")

        table = Table(show_header=True, header_style="bold cyan", box=None,
                      padding=(0, 1), expand=True)
        table.add_column("id", no_wrap=True, style="bold")
        table.add_column("state", no_wrap=True)
        table.add_column("conf", no_wrap=True, justify="right")
        table.add_column("source", no_wrap=True, style="cyan")
        table.add_column("claim", overflow="fold", style="default")

        for c in self.claims:
            glyph_key, color = _ANCHOR_STYLE[c.state]
            label = _GLYPHS[glyph_key]
            table.add_row(
                c.id,
                Text(f"{label} {c.state}", style=color),
                f"{c.confidence:.2f}",
                escape(c.source),
                escape(c.text),
            )

        return Panel(table, title=title, title_align="left", border_style="cyan")
