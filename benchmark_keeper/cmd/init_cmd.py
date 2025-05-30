from typing import Optional

from benchmark_keeper import app, console, Color, get_config, AppConfig
import typer
import subprocess

@app.command(name="init")
def init() -> None:
    """Inits in current repository"""

    console.print("Initializing benchmark-keeper in current git repo.")

    config = get_config()

    raise typer.Exit()