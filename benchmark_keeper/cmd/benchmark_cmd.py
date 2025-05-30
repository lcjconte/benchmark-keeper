import subprocess
from typing import Any, Optional

from pydantic import ValidationError
import typer
import json

from benchmark_keeper import (AppConfig, Color, Experiment, ScriptDelimiter,
                               app, console, get_config, get_path, BenchmarkRunOutput, write_report)


def run_build(experiment: Experiment):
    if (script := experiment.build_script) is None:
        console.print("No build script found. Skipping.")
    else:
        with ScriptDelimiter(script):
            r = subprocess.call([script])
        if r != 0:
            raise RuntimeError("Build failed")

def run_tests(experiment: Experiment):
    if (script := experiment.test_script) is None:
        console.print("No test script found. Skipping.")
    else:
        with ScriptDelimiter(script):
            r = subprocess.call([script])
        if r != 0:
            raise RuntimeError("Tests Failed")
        
def run_benchmarks(experiment: Experiment) -> Any:
    proc = subprocess.Popen([get_path().joinpath(experiment.benchmark_script)], stdout=subprocess.PIPE, text=True)
    with ScriptDelimiter(experiment.benchmark_script):
        out = proc.communicate()[0]
    if out == "":
        console.print("Benchmark returned nothing")
        typer.Exit(1)
    return json.loads(out)
    

@app.command(name="benchmark")
def benchmark(
    message: Optional[str] = typer.Option(
        None,
        "-m",
        "--message",
        help="Commit benchmark results with message"
    ),
    dry: bool = typer.Option(
        False,
        "-d",
        "--dry",
        help="If true benchmarks will be skipped"
    )
) -> None:
    """Runs and optionally commits benchmarks"""

    config = get_config()

    if (experiment := config.active_experiment) is None:
        console.print(f"No active experiment found.")
        raise typer.Exit(1)
    
    console.print(f"Running benchmarks for \"{experiment.name}\"")

    run_build(experiment)

    run_tests(experiment)

    if dry:
        console.print("Skipping benchmarks (due to -d)")
        raise typer.Exit()
    
    b_result = run_benchmarks(experiment)

    try:
        run_output = BenchmarkRunOutput(
            version=experiment.version,
            machine=config.local_config.machine_name,
            benchmarks=b_result
        )
        write_report(run_output)
    except ValidationError as e:
        console.print(f"Benchmark script output badly formatted")
        raise e
    
