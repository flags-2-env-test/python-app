"""Python consumer of oresoftware/flags-2-env.

Asserts the contract in EXPECTED.md. Exits non-zero on the first disagreement,
which is what makes `docker run` the whole test.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VENDOR = REPO / ".vendor/.zed/oresoftware/flags-2-env"

# The Python client is not on PyPI in this fixture; it is consumed straight out
# of the directory .zpkg.toml's [install].dir points at. flags2env.py re-exports
# from a sibling module named `lib`, so the client directory itself has to be on
# sys.path -- importing by file path alone would not resolve that sibling.
sys.path.insert(0, str(VENDOR / "clients/python"))

from flags2env import Flags2Env  # noqa: E402

CONFIG = str(REPO / ".cli-flags.toml")

DEFAULTS = {"PORT": "3000", "DEBUG": "false", "APP_ENV": "development", "COLOR": "true"}
OVERRIDDEN = {"PORT": "8181", "DEBUG": "true", "APP_ENV": "production", "COLOR": "true"}

CASES = [
    ("defaults", [], DEFAULTS),
    ("long flags", ["--port", "8181", "--debug=t", "--mode", "production"], OVERRIDDEN),
    ("short flags", ["-p", "8181", "-d", "1", "--env", "production"], OVERRIDDEN),
    ("long aliases", ["--listen-port", "8181", "--debug", "1", "--mode", "production"], OVERRIDDEN),
    ("joined by =", ["--port=8181", "--debug=yes", "--mode=production"], OVERRIDDEN),
    ("negation", ["--no-color"], {**DEFAULTS, "COLOR": "false"}),
]


def main() -> int:
    # No explicit library path: the client falls back to FLAGS2ENV_NATIVE_LIB,
    # which the Dockerfile points at the shared object built from the vendored
    # src/parser.c.
    sdk = Flags2Env()

    failures = 0
    for label, flags, expected in CASES:
        got = sdk.parse(["demo", *flags], CONFIG)
        status = "ok  " if got == expected else "FAIL"
        if got != expected:
            failures += 1
        print(f"{status} {label:<13} demo {' '.join(flags)}")
        for key in sorted(expected):
            print(f"       {key}={got.get(key, '<missing>')}")
        if got != expected:
            print(f"       expected {expected}", file=sys.stderr)
            print(f"       got      {got}", file=sys.stderr)

    if failures:
        print(f"\npython-app: {failures} of {len(CASES)} cases disagree with the contract", file=sys.stderr)
        return 1
    print(f"\npython-app OK: {len(CASES)} cases, via ctypes into oresoftware/flags-2-env")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
