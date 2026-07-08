import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

POLICY_SMOKE_TESTS = [
    "ops/tests/policy_engine_factory_smoke.py",
    "ops/tests/policy_engine_shadow_smoke.py",
    "ops/tests/policy_decision_audit_contract_smoke.py",
    "ops/tests/g11_capital_kill_switch_smoke.py",
]


def main():
    for test_path in POLICY_SMOKE_TESTS:
        print(f"==> {test_path}")
        subprocess.run(
            [sys.executable, str(ROOT / test_path)],
            cwd=ROOT,
            check=True,
        )

    print("OK: all policy smoke contracts passed")


if __name__ == "__main__":
    main()
