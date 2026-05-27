#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from laptop_init.cli import Cli, CommandError

if __name__ == '__main__':
    try:
        Cli().run()
    except CommandError as exc:
        raise SystemExit(str(exc))
