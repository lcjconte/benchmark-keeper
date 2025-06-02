import subprocess
from subprocess import PIPE, Popen
from typing import Any, List, Mapping, Tuple

import typer
from pydantic.dataclasses import dataclass

from benchmark_keeper import (REPORT_FILE, TRACKED_DIR, BenchmarkRun,
                              app, console, get_config, Color)
from benchmark_keeper.report import get_commit_run, get_current_run
from benchmark_keeper.aggregator import aggregator_presets, DEFAULT_AGGREGATOR

fail_counter = 0


def get_commits() -> List[Tuple[str, str]]:
    proc = Popen(
        ["git", "log", "--pretty=format:%H %s"], stdout=PIPE, stderr=PIPE, text=True
    )
    o, e = proc.communicate()
    if e:
        raise RuntimeError("Error querying commit list")
    return list(
        map(
            lambda x: (x.split(" ")[0], " ".join(x.split(" ")[1:])),
            o.strip().split("\n"),
        )
    )

@dataclass
class CommitData:
    commit_hash: str
    subject: str
    data: BenchmarkRun

@dataclass
class AnnotatedCommitData:
    data: CommitData
    score: float

def reducer(benchmark_results: Mapping[str, Mapping[str, Any]], metric: str) -> float:
    return sum(result[metric] for bench, result in benchmark_results.items()) / len(benchmark_results)
            

@app.command(name="list")
def list_cmd(
    limit: int = typer.Option(
        None,
        "-l",
        "--limit",
        help="Limit number of commits to show",
    ),
    aggregator: str = typer.Option(
        None,
        "-a",
        "--aggregator",
        help="How to aggregate results of different benchmarks",
    ),
    commit_order: bool = typer.Option(
        False,
        "-c",
        "--commit-order",
        help="Sort results by commit order. If false, results will be shown in score order (default: false)",
    ),
) -> None:
    """Switch active experiment"""
    global fail_counter

    fail_counter = 0

    config = get_config()

    experiment = config.active_experiment
    if experiment is None:
        raise RuntimeError("Experiment missing")

    console.print(f"Comparing results for machine: {config.local_config.machine_name}\n")

    commit_data: List[CommitData] = []
    for commit in get_commits():
        res = get_commit_run(commit[0], experiment.name, experiment.version)
        if isinstance(res, BenchmarkRun):
            commit_data.append(CommitData(commit_hash=commit[0], subject=commit[1], data=res))
        # Ignore failures for now
    
    current_data = get_current_run(experiment.name, experiment.version)
    current_tag = ""
    if isinstance(current_data, BenchmarkRun):
        commit_data.insert(0, CommitData(commit_hash="0"*40, subject="Current", data=current_data))
        current_tag = current_data.tag

    # Commit data is sorted by commit order
    # Remove duplicate tags
    seen = set()
    
    commit_data = [
        cd for cd in commit_data[::-1] if (cd.data.machine == config.local_config.machine_name and cd.data.tag not in seen and not seen.add(cd.data.tag))
    ]

    # Get aggregator
    _agg = aggregator_presets[aggregator if aggregator else DEFAULT_AGGREGATOR]()
    aggregated = _agg.aggregate([cd.data.benchmarks for cd in commit_data])

    annotated_data: List[AnnotatedCommitData] = []
    for i, cd in enumerate(commit_data):
        annotated_data.append(AnnotatedCommitData(data=cd, score=aggregated[i]))

    if not commit_order:
        annotated_data.sort(key=lambda x: x.score, reverse=_agg.lower_is_better())

    if limit is not None:
        current_annotated_run = None
        for an in annotated_data:
            if an.data.data.tag == current_tag:
                current_annotated_run = an
                break

        annotated_data = annotated_data[-limit:]

        # Include current run regardless of limit
        if current_annotated_run is not None and current_annotated_run not in annotated_data:
            annotated_data.insert(0, current_annotated_run)
    
    if not annotated_data:
        console.print(f"No results found for experiment {experiment.name} on machine {config.local_config.machine_name}")
        raise typer.Exit(0)

    for i, cd in enumerate(annotated_data):
        best_str = f" [{Color.yellow}](best)[/{Color.yellow}]" if i == len(annotated_data)-1 else ""
        current_str = f" [{Color.yellow}](current)[/{Color.yellow}]" if cd.data.data.tag == current_tag else ""
        console.print(f"{cd.score:012.2f} \[{_agg.unit()}], {cd.data.commit_hash[:10]}, {cd.data.subject}{best_str}{current_str}")