
from benchmark_keeper import console, TRACKED_DIR, REPORT_FILE, REPO_CONFIG
import subprocess

def commit_report(message):
    console.print(f"Commiting to git with message \"{message}\". Make sure all source changes are staged.")
    if subprocess.call(f"git add {TRACKED_DIR+'/'+REPORT_FILE}", shell=True) != 0:
        raise RuntimeError("Git command failed")
    if subprocess.call(f"git add {TRACKED_DIR+'/'+REPO_CONFIG}", shell=True) != 0:
        raise RuntimeError("Git command failed")
    if subprocess.call(f"git commit -m {message}", shell=True) != 0:
        raise RuntimeError("Git command failed")