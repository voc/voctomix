import os


def ui_file(path: str):
    return os.path.join(os.path.dirname(__file__), path)
