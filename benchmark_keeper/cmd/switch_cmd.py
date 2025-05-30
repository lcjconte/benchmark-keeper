
from benchmark_keeper import app, console, get_config, write_local_config
import typer

@app.command(name="switch")
def switch(experiment: str = typer.Argument(
    help="The experiment to switch to"
)) -> None:
    """Switch active experiment"""

    config = get_config()

    for exp in config.repo_config.experiments:
        if exp.name == experiment:
            console.print(f"Switching to experiment \"{experiment}\"")
            write_local_config(config.local_config.model_copy(update={"active_experiment": experiment}))
            raise typer.Exit()
    
    console.print("Experiment not found. First five Experiments are:")
    for exp in config.repo_config.experiments[:5]:
        console.print(f"{exp.name}")
