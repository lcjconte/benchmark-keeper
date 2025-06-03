import subprocess, yaml
from enum import Enum
from typing import List, Tuple
from pydantic import ValidationError
import typer

from benchmark_keeper import (
    REPORT_FILE,
    TRACKED_DIR,
    BenchmarkRun,
    app,
    console,
    get_path,
    Report,
    print_error,
)


class DataRetrieveFailure(Enum):
    FILE_MISSING = 1
    BAD_FORMAT = 2
    RUN_MISSING = 3


def write_runs(runs: Report):
    with open(get_path().joinpath(TRACKED_DIR, REPORT_FILE), "w") as f:
        yaml.safe_dump(runs.model_dump(), f)


def read_runs() -> Report | DataRetrieveFailure:
    path = get_path().joinpath(TRACKED_DIR, REPORT_FILE)
    if not path.exists():
        write_runs(Report(runs=[]))
    with open(path, "r") as f:
        content = f.read()
    try:
        return Report(**yaml.safe_load(content))
    except (ValidationError, yaml.YAMLError):
        return DataRetrieveFailure.BAD_FORMAT


def unique_runs(runs: List[BenchmarkRun]) -> List[BenchmarkRun]:
    """Removes duplicate runs"""
    seen = set()

    def ffunc(run: BenchmarkRun):
        p = (run.experiment, run.experiment_version)
        return p not in seen and not seen.add(p)

    return list(filter(ffunc, runs))


def add_run(run: BenchmarkRun):
    if not isinstance((runs := read_runs()), Report):
        print_error(
            f"{REPORT_FILE} file badly formatted. Fix or delete it to continue."
        )
        raise typer.Exit(1)

    new_runs = unique_runs([run] + runs.runs)

    write_runs(Report(runs=new_runs))


def find_run(runs: Report | DataRetrieveFailure, exp_pair: Tuple[str, int]):
    match runs:
        case Report():
            for run in runs.runs:
                if (run.experiment, run.experiment_version) == exp_pair:
                    return run
            return DataRetrieveFailure.RUN_MISSING
        case _:
            return runs


def get_commit_run(
    commit_id: str, experiment: str, experiment_version: int
) -> BenchmarkRun | DataRetrieveFailure:
    proc = subprocess.run(
        ["git", "show", f"{commit_id}:{TRACKED_DIR+'/'+REPORT_FILE}"],
        capture_output=True,
        text=True,
    )
    if proc.stdout is None:
        return DataRetrieveFailure.FILE_MISSING
    try:
        runs = Report(**yaml.safe_load(proc.stdout))
        return find_run(runs, (experiment, experiment_version))
    except (ValidationError, yaml.YAMLError):
        return DataRetrieveFailure.BAD_FORMAT


def get_current_run(
    experiment: str, experiment_version: int
) -> BenchmarkRun | DataRetrieveFailure:
    return find_run(read_runs(), (experiment, experiment_version))
