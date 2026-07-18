from __future__ import annotations

import hashlib

from aso_x.core.types import PositionState
from aso_x.replay.canonical import state_to_canonical_dict, to_canonical_json


def state_hash(state: PositionState) -> str:
    payload = to_canonical_json(state_to_canonical_dict(state)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
