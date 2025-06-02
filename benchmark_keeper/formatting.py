from benchmark_keeper import Color, console


class ScriptDelimiter(object):
    """Delimits output of script on console"""
    def __init__(self, script_name) -> None:
        self.script_name = script_name
    def __enter__(self):
        console.print(f"[{Color.yellow}]--- Running {self.script_name}")
    def __exit__(self, type, value, traceback):
        console.print(f"[{Color.yellow}]--- Done")