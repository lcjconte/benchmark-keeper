
import subprocess, yaml
from enum import Enum
from typing import Tuple
from pydantic import ValidationError

from benchmark_keeper import (REPORT_FILE, TRACKED_DIR, BenchmarkRunOutput,
                              app, console, get_path)

def write_report(report: BenchmarkRunOutput):
    with open(get_path().joinpath(TRACKED_DIR, REPORT_FILE), "w") as f:
        yaml.safe_dump(report.model_dump(), f)

class DataRetrieveFailure(Enum):
    FILE_MISSING = 1
    BAD_FORMAT = 2

def get_commit_data(commit_id) -> BenchmarkRunOutput | DataRetrieveFailure:
    proc = subprocess.run(
        ["git", "show", f"{commit_id}:{TRACKED_DIR+'/'+REPORT_FILE}"],
        capture_output=True,
        text=True,
    )
    if proc.stdout is None:
        return DataRetrieveFailure.FILE_MISSING
    try:
        ret = BenchmarkRunOutput(**yaml.safe_load(proc.stdout)) 
    except ValidationError | yaml.YAMLError:
        return DataRetrieveFailure.BAD_FORMAT
    return ret

def get_current_data() -> BenchmarkRunOutput | DataRetrieveFailure:
    path = get_path().joinpath(TRACKED_DIR, REPORT_FILE)
    if not path.exists():
        return DataRetrieveFailure.FILE_MISSING
    with open(path, "r") as f:
        content = f.read()
    try:
        ret = BenchmarkRunOutput(**yaml.safe_load(content))
    except ValidationError | yaml.YAMLError:
        return DataRetrieveFailure.BAD_FORMAT
    return ret