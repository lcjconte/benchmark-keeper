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
LOCAL_CONFIG = "local_config.yml"
REPO_CONFIG = "repo_config.yml"

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


def print_error(error: str, message: str = ""):
    console.print(f"[{Color.red}]{error}[/{Color.red}] {message}")


class LocalConfig(BaseModel):
    machine_name: str
    active_experiment: str | None


default_local_config = LocalConfig(machine_name="MyMachine", active_experiment=None)


class Experiment(BaseModel):
    name: str
    version: int = 1
    build_script: str | None = None
    test_script: str | None = None
    benchmark_script: str
    watch_files: List[str] = []


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
        return next(
            filter(
                lambda x: x.name == self.local_config.active_experiment,
                self.repo_config.experiments,
            ),
            None,
        )


_root_path: pathlib.Path | None = None


def get_path():
    global _root_path
    if _root_path is None:
        proc = subprocess.run(
            "git rev-parse --show-toplevel",
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
        _root_path = pathlib.Path(proc.stdout.strip())
    return _root_path


def write_local_config(config: LocalConfig):
    dir_path = get_path().joinpath(LOCAL_DIR)
    dir_path.touch()
    with open(dir_path.joinpath(LOCAL_CONFIG), "w") as f:
        yaml.dump(config.model_dump(), f)
    if _config is not None:
        _config.local_config = config


def write_repo_config(config: RepoConfig):
    dir_path = get_path().joinpath(TRACKED_DIR)
    dir_path.touch()
    with open(dir_path.joinpath(REPO_CONFIG), "w") as f:
        yaml.dump(config.model_dump(), f)
    if _config is not None:
        _config.repo_config = config


_config: AppConfig | None = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        path = get_path()

        local_config_path = path.joinpath(LOCAL_DIR, LOCAL_CONFIG)
        if not path.joinpath(LOCAL_DIR).exists():
            path.joinpath(LOCAL_DIR).mkdir()
            # Create gitignore to ignore LOCAL_DIR
            with open(path.joinpath(LOCAL_DIR, ".gitignore"), "w") as f:
                f.write("*")
        if not local_config_path.exists():
            write_local_config(default_local_config)
        with open(local_config_path, "r") as f:
            local_config = LocalConfig(**yaml.safe_load(f))

        repo_config_path = path.joinpath(TRACKED_DIR, REPO_CONFIG)
        path.joinpath(TRACKED_DIR).mkdir(exist_ok=True)
        if not repo_config_path.exists():
            write_repo_config(default_repo_config)
        with open(repo_config_path, "r") as f:
            repo_config = RepoConfig(**yaml.safe_load(f))
        _config = AppConfig(path, local_config, repo_config)

    if _config.local_config.active_experiment is None and repo_config.experiments:
        console.print(
            f'No active experiment set. Using "{repo_config.experiments[0].name}"'
        )
        _config.local_config.active_experiment = repo_config.experiments[0].name
        write_local_config(_config.local_config)

    return _config


class BenchmarkResult(BaseModel):
    """
    The result of one benchmark. target is (for now) measured in ns.
    """

    target: float
    labels: List[str] = []
    unstructured: Mapping[str, Any] = {}


class BenchmarkRun(BaseModel):
    """
    Contains results of multiple benchmarks within one (experiment,version).
    The tag uniquely identifies this run.
    """

    tag: str
    experiment: str
    experiment_version: int
    machine: str
    benchmarks: Mapping[str, BenchmarkResult]
    file_digest: str = ""


class Report(BaseModel):
    """
    Persisted runs across different experiments/versions.
    Should contain, for every (experiment, experiment_version) pair at most one run.
    """

    runs: List[BenchmarkRun]
