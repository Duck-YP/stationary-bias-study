"""Allow ``python -m stationary_bias`` to use the same CLI as run.py."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())

