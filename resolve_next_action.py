# resolve_next_action.py  (root shim -> scripts/resolve_next_action.py)
# SSOT: scripts/resolve_next_action.py - do NOT edit logic here.
import importlib.util
import pathlib
import sys

_src = pathlib.Path(__file__).resolve().parent / "scripts" / "resolve_next_action.py"
if not _src.is_file():
    raise FileNotFoundError(f"SSOT missing: {_src}")

_spec = importlib.util.spec_from_file_location("resolve_next_action", _src)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["resolve_next_action"] = _mod
_spec.loader.exec_module(_mod)

# Re-export public symbols so loaders that execute THIS file directly
# (e.g. spec_from_file_location on the root shim) also see the real API.
globals().update({_k: _v for _k, _v in vars(_mod).items() if not _k.startswith("_")})
