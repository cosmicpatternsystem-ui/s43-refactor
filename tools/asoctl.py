from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT_ASOCTL = Path(__file__).resolve().parents[1] / "asoctl.py"


def load_root_main():
    spec = importlib.util.spec_from_file_location("aso_root_asoctl", ROOT_ASOCTL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load root asoctl.py from {ROOT_ASOCTL}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "main"):
        raise RuntimeError("root asoctl.py does not expose main()")

    return module.main


def main(argv: list[str] | None = None) -> int:
    root_main = load_root_main()
    return int(root_main(argv))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
