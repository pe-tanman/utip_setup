import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def load_env(path=None):
    """Minimal .env loader (KEY=VALUE lines). Existing environment variables win."""
    path = pathlib.Path(path or ROOT / "pipeline" / ".env")
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def env(name, default=None, required=False):
    val = os.environ.get(name, default)
    if required and not val:
        raise SystemExit(f"Missing {name}. Add it to pipeline/.env (see pipeline/.env.example).")
    return val
