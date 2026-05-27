"""Streamlit Cloud entry point.

Streamlit Cloud runs the file you specify in its "Main file path" setting.
This shim makes the `mcq` package importable, then runs the app module —
its top-level `st.*` calls render the page as a side effect.

Locally you can still run `streamlit run mcq/app.py` if you prefer.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from mcq import app  # noqa: F401  (side-effect: builds the Streamlit page)
