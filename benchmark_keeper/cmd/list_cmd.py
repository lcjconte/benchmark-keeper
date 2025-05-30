from benchmark_keeper import app, console, TRACKED_DIR, REPORT_FILE, get_config, BenchmarkRunOutput

import subprocess
from subprocess import Popen, PIPE
import typer
from typing import List, Tuple

fail_counter = 0


def get_commits() -> List[Tuple[str, str]]:
    proc = Popen(
        ["git", "log", "--pretty=format:%H %s"], stdout=PIPE, stderr=PIPE, text=True
    )
    o, e = proc.communicate()
    if e:
        raise RuntimeError("Error querying commits")
    return list(
        map(
            lambda x: (x.split(" ")[0], " ".join(x.split(" ")[1:])),
            o.strip().split("\n"),
        )
    )


def get_commit_data(commit_id):
    proc = subprocess.run(
        ["git", "show", f"{commit_id}:{TRACKED_DIR+'/'+REPORT_FILE}"],
        capture_output=True,
        text=True,
    )
    print(proc.stdout)

class CommitData:
    commit_hash: str
    subject: str
    data: BenchmarkRunOutput


@app.command(name="list")
def list_cmd() -> None:
    """Switch active experiment"""
    global fail_counter

    fail_counter = 0

    config = get_config()

    for commit in get_commits():
        print(commit, get_commit_data(commit[0]))

    # Stats

