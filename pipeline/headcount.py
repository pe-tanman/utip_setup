#!/usr/bin/env python3
"""How many people are coming? Lists upcoming Luma events with RSVP counts.
  python3 pipeline/headcount.py"""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utip.config import env, load_env  # noqa: E402
from utip.luma import Luma  # noqa: E402

load_env()
luma = Luma(env("LUMA_API_KEY", required=True))
now = dt.datetime.now(dt.timezone.utc).isoformat()
for ev in luma.upcoming_events(now):
    counts = luma.guest_counts(ev["id"])
    going = counts.get("approved", 0)
    extra = ", ".join(f"{k}: {v}" for k, v in counts.items() if k != "approved")
    print(f"{ev['start_at'][:16]}  {going:>3} going  {ev['name']}  ({extra or 'no others'})  {ev['url']}")
