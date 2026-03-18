import os


def asset_path(*parts: str) -> str:
    return os.path.join(os.path.dirname(__file__), "assets", *parts)
