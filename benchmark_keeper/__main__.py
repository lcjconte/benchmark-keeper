# type: ignore[attr-defined]
from typing import Optional

from enum import Enum
from random import choice

import typer
from rich.console import Console

from benchmark_keeper import version, app, console, Color

import benchmark_keeper.cmd

def version_callback(print_version: bool) -> None:
    """Print the version of the package."""
    if print_version:
        console.print(f"[yellow]benchmark-keeper[/] version: [bold blue]{version}[/]")
        raise typer.Exit()

if __name__ == "__main__":
    app()
