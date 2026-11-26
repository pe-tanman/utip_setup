#!/usr/bin/env python3
"""Send a one-off text newsletter to everyone who opted in.
  python3 pipeline/newsletter.py "Courts are wet - today's session moves to Gregory Gym!"           # preview
  python3 pipeline/newsletter.py "..." --live"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utip.config import env, load_env  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("message")
ap.add_argument("--live", action="store_true")
a = ap.parse_args()
load_env()
text = lambda name: f"UTIP: {a.message} Reply STOP to opt out"
print("Preview:", text("Alex"), f"({len(text('Alex'))} chars; >160 is sent as 2+ segments)")
if a.live:
    from utip.members import Members
    from utip.sms import Twilio
    rcp = Members(env("UTIP_API_URL", required=True), env("UTIP_API_TOKEN", required=True)).sms_list()
    tw = Twilio(env("TWILIO_ACCOUNT_SID", required=True), env("TWILIO_AUTH_TOKEN", required=True),
                env("TWILIO_MESSAGING_SERVICE_SID"), env("TWILIO_FROM_NUMBER"))
    sent, failed = tw.broadcast(rcp, text)
    print(f"sent {sent}/{len(rcp)}", failed or "")
