import subprocess
from typing import Any, Optional, Mapping

from pydantic import ValidationError, TypeAdapter
import typer
import json
from uuid import uuid4
import hashlib

from benchmark_keeper import (
    AppConfig,
    Color,
    Experiment,
    app,
    console,
    get_config,
    get_path,
    BenchmarkRun,
    BenchmarkResult,
    print_error,
)

from benchmark_keeper.formatting import ScriptDelimiter
from benchmark_keeper.git import git_add_files
from benchmark_keeper.report import add_run, get_current_run


def run_build(experiment: Experiment):
    if (script := experiment.build_script) is None:
        console.print("No build script found. Skipping.")
    else:
        with ScriptDelimiter(script):
            r = subprocess.call([script])
        if r != 0:
            print_error("Build failed")
            raise typer.Exit(1)


def run_tests(experiment: Experiment):
    if (script := experiment.test_script) is None:
        console.print("No test script found. Skipping.")
    else:
        with ScriptDelimiter(script):
            r = subprocess.call([script])
        if r != 0:
            print_error("Tests failed")
            raise typer.Exit(1)


def run_benchmarks(experiment: Experiment) -> Mapping[str, BenchmarkResult]:
    proc = subprocess.Popen(
        [get_path().joinpath(experiment.benchmark_script)],
        stdout=subprocess.PIPE,
        text=True,
    )
    with ScriptDelimiter(experiment.benchmark_script):
        out = proc.communicate()[0]
    if out == "":
        print_error("Benchmark returned nothing")
        raise typer.Exit(1)

    return TypeAdapter(Mapping[str, BenchmarkResult]).validate_python(json.loads(out))


@app.command(name="benchmark")
def benchmark(
    dry: bool = typer.Option(
        False, "-d", "--dry", help="If true benchmarks will be skipped"
    ),
    force_run: bool = typer.Option(
        False,
        "-f",
        "--force",
        help="Always run benchmarks, even if watched files haven't changed.",
    ),
) -> None:
    """Runs and optionally commits benchmarks"""

    config = get_config()

    if (experiment := config.active_experiment) is None:
        print_error("No active experiment found")
        raise typer.Exit(1)

    console.print(f'Running benchmarks for "{experiment.name}"')

    run_build(experiment)

    # Compute hashes to check for changes
    file_digest = ""
    if experiment.watch_files:
        print("Watching")
        h = hashlib.sha256(usedforsecurity=False)
        for file in experiment.watch_files:
            with open(get_path().joinpath(file), "rb") as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    h.update(data)
        file_digest = h.hexdigest()

        current_run = get_current_run(experiment.name, experiment.version)

        if (
            not force_run
            and isinstance(current_run, BenchmarkRun)
            and file_digest == current_run.file_digest
        ):
            git_add_files()
            console.print(
                "Skipping tests and benchmarks, since watched files are unchanged"
            )
            raise typer.Exit()

    run_tests(experiment)

    if dry:
        console.print("Skipping benchmarks (due to -d)")
        raise typer.Exit()

    b_result = run_benchmarks(experiment)

    try:
        run_output = BenchmarkRun(
            tag=uuid4().hex,
            experiment=experiment.name,
            experiment_version=experiment.version,
            machine=config.local_config.machine_name,
            benchmarks=b_result,
            file_digest=file_digest,
        )
        add_run(run_output)
    except ValidationError as e:
        print_error(f"Benchmark script output badly formatted")
        raise typer.Exit(1)

    git_add_files()
