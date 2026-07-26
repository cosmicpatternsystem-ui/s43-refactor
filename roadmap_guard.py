"""Shim: canonical implementation lives in scripts/roadmap_guard.py (single source of truth)."""
import importlib.util as _ilu
import os as _os

_IMPL_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "scripts", "roadmap_guard.py")
_spec = _ilu.spec_from_file_location("_roadmap_guard_impl", _IMPL_PATH)
_impl = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_impl)
globals().update({k: v for k, v in vars(_impl).items() if not k.startswith("__")})

if __name__ == "__main__":
    import sys as _sys
    _sys.exit(_impl.main() if hasattr(_impl, "main") else 0)
