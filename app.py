from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def resolve_dashboard_path() -> Path:
    """Resolve dashboard.py from common execution contexts."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "dashboard.py",
        Path.cwd() / "dashboard.py",
        Path.cwd().parent / "dashboard.py",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    searched = "\n".join(f"- {path}" for path in candidates)
    raise FileNotFoundError(
        "Could not find dashboard.py. Checked:\n"
        f"{searched}\n"
        "Run this from the project folder or keep app.py and dashboard.py in the same directory."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the Streamlit sales dashboard.")
    parser.add_argument("--port", type=int, default=8501, help="Port for Streamlit server (default: 8501)")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start Streamlit without auto-opening the browser.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dashboard_path = resolve_dashboard_path()
    streamlit_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(dashboard_path),
        "--server.port",
        str(args.port),
    ]
    if args.no_browser:
        streamlit_cmd.extend(["--server.headless", "true"])

    print(f"Starting dashboard: {dashboard_path}")
    print(f"Using command: {' '.join(streamlit_cmd)}")

    subprocess.run(
        streamlit_cmd,
        cwd=str(dashboard_path.parent),
        check=False,
    )


if __name__ == "__main__":
    main()
