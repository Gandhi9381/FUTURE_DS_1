from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    dashboard_path = Path(__file__).with_name("dashboard.py")
    subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(dashboard_path)], cwd=str(dashboard_path.parent))


if __name__ == "__main__":
    main()
