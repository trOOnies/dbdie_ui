import os


def absp(rel_path: str) -> str:
    """Convert DBDIE relative path to absolute path"""
    return os.path.join(os.environ["DBDIE_MAIN_FD"], rel_path)
