# type: ignore[attr-defined]
"""Simple tracking of benchmark results across git commits"""

import sys

import typer
from rich.console import Console
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
import yaml
from typing import List, Optional, Mapping, Any
import pathlib
import subprocess
from enum import Enum

LOCAL_DIR = ".benchk.local"
TRACKED_DIR = ".benchk"
REPORT_FILE = "report.yml"

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


def get_version() -> str:
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


version: str = get_version()

app = typer.Typer(
    name="benchmark-keeper",
    help="Simple tracking of benchmark results across git commits",
    add_completion=False,
)
console = Console()

class Color(str, Enum):
    white = "white"
    red = "red"
    cyan = "cyan"
    magenta = "magenta"
    yellow = "yellow"
    green = "green"


class LocalConfig(BaseModel):
    machine_name: str
    active_experiment: str | None

default_local_config = LocalConfig(
    machine_name="MyMachine",
    active_experiment=None
)

class Experiment(BaseModel):
    name: str = "1.0.0"
    version: str = "1.0.0"
    build_script: str | None = None
    test_script: str | None = None
    benchmark_script: str

class RepoConfig(BaseModel):
    experiments: List[Experiment]

default_repo_config = RepoConfig(experiments=[])

@dataclass
class AppConfig:
    root_directory: pathlib.Path
    local_config: LocalConfig
    repo_config: RepoConfig

    @property
    def active_experiment(self) -> Optional[Experiment]:
        return next(filter(lambda x: x.name == self.local_config.active_experiment, self.repo_config.experiments), None)

def init_app(root_directory):
    pass

_root_path: pathlib.Path | None = None

def get_path():
    global _root_path
    if _root_path is None:
        proc = subprocess.run("git rev-parse --show-toplevel", shell=True, check=True, capture_output=True, text=True)
        _root_path = pathlib.Path(proc.stdout.strip())
    return _root_path

def ensure_local_dir_ignored():
    path = get_path()
    if subprocess.run(f"git check-ignore {path.joinpath(LOCAL_DIR)}", shell=True).returncode == 0:
        return
    console.print(f"[{Color.red}] Add {LOCAL_DIR} to .gitignore")



def write_local_config(config: LocalConfig):
    dir_path = get_path().joinpath(LOCAL_DIR)
    dir_path.touch()
    with open(dir_path.joinpath("config.yml"), "w") as f:
        yaml.dump(config.model_dump(), f)
    if _config is not None:
        _config.local_config = config

def write_repo_config(config: RepoConfig):
    dir_path = get_path().joinpath(TRACKED_DIR)
    dir_path.touch()
    with open(dir_path.joinpath("config.yml"), "w") as f:
        yaml.dump(config.model_dump(), f)
    if _config is not None:
        _config.repo_config = config

_config: AppConfig | None = None

def get_config() -> AppConfig:
    global _config
    if _config is None:
        path = get_path()

        local_config_path = path.joinpath(LOCAL_DIR, "config.yml")
        path.joinpath(LOCAL_DIR).mkdir(exist_ok=True)
        if not local_config_path.exists():
            write_local_config(default_local_config)
        with open(local_config_path, "r") as f:
            local_config = LocalConfig(**yaml.safe_load(f)) 

        repo_config_path = path.joinpath(TRACKED_DIR, "config.yml")
        path.joinpath(TRACKED_DIR).mkdir(exist_ok=True)
        if not repo_config_path.exists():
            write_repo_config(default_repo_config)
        with open(repo_config_path, "r") as f:
            repo_config = RepoConfig(**yaml.safe_load(f))
        _config = AppConfig(path, local_config, repo_config)
    return _config

class ScriptDelimiter(object):
    """Delimits output of script on console"""
    def __init__(self, script_name) -> None:
        self.script_name = script_name
    def __enter__(self):
        console.print(f"[{Color.yellow}]--- Running {self.script_name}")
    def __exit__(self, type, value, traceback):
        console.print(f"[{Color.yellow}]---")

class BenchmarkRunOutput(BaseModel):
    version: str
    machine: str
    benchmarks: Mapping[str, Mapping[str, Any]]

def write_report(report: BenchmarkRunOutput):
    with open(get_path().joinpath(TRACKED_DIR, REPORT_FILE), "w") as f:
        yaml.safe_dump(report.model_dump(), f)