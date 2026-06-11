#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print("usage: termux_write_file.py <target>", file=sys.stderr)
        sys.exit(2)

    target = Path(sys.argv[1]).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    data = sys.stdin.read()

    tmp = target.with_suffix(target.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

    os.replace(tmp, target)
    print(str(target))

if __name__ == "__main__":
    main()
