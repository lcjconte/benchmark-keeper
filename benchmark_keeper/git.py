from benchmark_keeper import console, TRACKED_DIR, REPORT_FILE, REPO_CONFIG, print_error
import subprocess
import typer


def git_add_files():
    if subprocess.call(f"git add {TRACKED_DIR+'/'+REPORT_FILE}", shell=True) != 0:
        print_error("Git command failed")
        raise typer.Exit(1)
    if subprocess.call(f"git add {TRACKED_DIR+'/'+REPO_CONFIG}", shell=True) != 0:
        print_error("Git command failed")
        raise typer.Exit(1)


def commit_report(message):
    console.print(
        f'Commiting to git with message "{message}". Make sure all source changes are staged.'
    )
    git_add_files()
    if subprocess.call(f"git commit -m {message}", shell=True) != 0:
        print_error("Git command failed")
        raise typer.Exit(1)
