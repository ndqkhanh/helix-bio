"""Helix-Bio TUI — biomedical research agent."""
from __future__ import annotations

import os
from typing import Optional

import click
from harness_tui import HarnessApp, ProjectConfig
from harness_tui.commands.registry import register_command
from harness_tui.transport import HTTPTransport, MockTransport

from .tui_theme import helix_theme
from .widgets import FaithfulnessLedger


@register_command(name="ontology", description="Look up an ontology id (UniProt/PDB/AlphaFold)",
                  category="Helix")
async def cmd_ontology(app, args: str) -> None:  # type: ignore[no-untyped-def]
    if args.startswith("lookup "):
        oid = args[7:].strip()
        app.shell.chat_log.write_system(f"ontology lookup: {oid} (mock)")
    else:
        app.shell.chat_log.write_system("usage: /ontology lookup <id>")


@register_command(name="faithfulness", description="Audit claims against ontology sources",
                  category="Helix")
async def cmd_faithfulness(app, args: str) -> None:  # type: ignore[no-untyped-def]
    app.shell.chat_log.write_system(
        "faithfulness audit: 12/12 claims anchored, 0 unanchored (mock)"
    )


@register_command(name="dualuse", description="Run dual-use safety check on a plan",
                  category="Helix")
async def cmd_dualuse(app, args: str) -> None:  # type: ignore[no-untyped-def]
    if args.startswith("check"):
        app.shell.chat_log.write_system("dual-use check: PASS (mock; HITL gates engaged)")
    else:
        app.shell.chat_log.write_system("usage: /dualuse check <plan>")


@click.command()
@click.option("--url", default=None)
@click.option("--mock", is_flag=True)
@click.option("--serve", is_flag=True,
              help="Run the TUI in a browser via textual-serve.")
@click.option("--port", type=int, default=8006,
              help="Web mode port (with --serve).")
@click.option("--host", default="127.0.0.1",
              help="Web mode host (with --serve).")
def main(url: Optional[str], mock: bool, serve: bool, port: int, host: str) -> None:
    """Open the Helix-Bio TUI."""
    if serve:
        from harness_tui.serve import serve_app, make_module_command

        flags = []
        if mock:
            flags.append("--mock")
        if url:
            flags.append(f"--url {url}")
        serve_app(
            command=make_module_command("helix_bio.tui", " ".join(flags)),
            host=host, port=port,
            title="helix-bio",
        )
        return
    if mock:
        transport = MockTransport()
    else:
        backend = url or os.environ.get("HELIX_BACKEND") or "http://localhost:8006"
        transport = HTTPTransport(
            backend,
            endpoints={"run": "/v1/queries"},
            payload_builder=lambda t, m: {"question": t},
            text_field="answer",
        )
    cfg = ProjectConfig(
        name="helix-bio",
        description="Biomedical research agent",
        theme=helix_theme(),
        transport=transport,
        model=os.environ.get("HELIX_MODEL", "auto"),
        sidebar_tabs=[("Faithfulness", FaithfulnessLedger())],
    )
    app = HarnessApp(cfg)
    app.run()
    summary = getattr(app, "last_exit_summary", None)
    if summary:
        click.echo(summary.render())


if __name__ == "__main__":  # pragma: no cover
    main()
