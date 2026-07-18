"""CLI entry point for ai-employee."""

from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(
    name="ai-employee",
    help="AI Employee V3.0 - local multi-agent system",
    no_args_is_help=True,
)
console = Console()


@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
) -> None:
    """Start the API server."""
    import uvicorn

    console.print(f"[green]Starting API on {host}:{port}[/green]")
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def eval(
    domain: str = typer.Option("all", help="Domain to eval, or 'all'"),
    ci: bool = typer.Option(False, help="CI mode (fail on regression)"),
) -> None:
    """Run eval suite."""
    console.print(f"[green]Running eval for domain={domain}[/green]")
    # TODO: import and call eval runner


@app.command()
def version() -> None:
    """Print version."""
    from core import __version__

    console.print(f"ai-employee [bold cyan]v{__version__}[/bold cyan]")


def main() -> None:
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
