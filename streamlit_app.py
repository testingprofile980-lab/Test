"""Streamlit Cloud entry point.

Streamlit reruns the main script on every interaction. We use runpy so
mcq/app.py executes fresh each time (a plain `import` would be cached
and the page would go blank on rerun).

Locally you can still run `streamlit run mcq/app.py` if you prefer.
"""
import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

runpy.run_path(str(_ROOT / "mcq" / "app.py"), run_name="__main__")
