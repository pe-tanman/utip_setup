#!/usr/bin/env python3
"""UTIP event pipeline: one YAML file -> Luma event, graphics, Discord, Instagram, SMS.

  python3 pipeline/announce.py pipeline/events/example-weekly-play.yaml            # dry run (default)
  python3 pipeline/announce.py pipeline/events/example-weekly-play.yaml --live     # really do it
  python3 pipeline/announce.py EVENT.yaml --live --only luma,render,discord        # pick steps
  python3 pipeline/announce.py EVENT.yaml --live --skip sms

Steps, in order: luma -> render -> discord -> instagram -> sms.
After a live Luma step the event URL is written back into the YAML, so re-running never
creates a duplicate event.
"""
import argparse
import datetime as dt
import pathlib
import subprocess
import sys
from zoneinfo import ZoneInfo

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utip.config import ROOT, env, load_env  # noqa: E402

STEPS = ["luma", "render", "discord", "instagram", "sms"]


def labels(ev):
    tz = ZoneInfo(ev.get("timezone", "America/Chicago"))
    start = dt.datetime.fromisoformat(str(ev["start"])).replace(tzinfo=tz)
    end = dt.datetime.fromisoformat(str(ev["end"])).replace(tzinfo=tz)
    fmt_t = lambda t: t.strftime("%I:%M %p").lstrip("0").replace(":00 ", " ")
    return {
        "start": start, "end": end,
        "date_label": start.strftime("%a, %b ") + str(start.day),
        "time_label": f"{fmt_t(start)} - {fmt_t(end)}",
    }


def caption(ev, lab, handle):
    tags = ev.get("hashtags", "#UTAustin #pickleball #internationalstudents #UTIP #hookem")
    return (f"{ev['title']}\n\n"
            f"\U0001F4C5 {lab['date_label']} · {lab['time_label']}\n"
            f"\U0001F4CD {ev['location']}\n\n"
            f"{ev.get('blurb', '').strip()}\n\n"
            f"RSVP on Luma — link in bio & in our story! International and domestic students all welcome. "
            f"No experience needed.\n\n{tags}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("event_file")
    ap.add_argument("--live", action="store_true", help="actually call the APIs (default is a dry run)")
    ap.add_argument("--only", default="", help="comma list of steps to run")
    ap.add_argument("--skip", default="", help="comma list of steps to skip")
    a = ap.parse_args()
    load_env()

    path = pathlib.Path(a.event_file)
    ev = yaml.safe_load(path.read_text())
    lab = labels(ev)
    steps = [s for s in STEPS if (not a.only or s in a.only.split(",")) and s not in a.skip.split(",")]
    live = a.live
    tag = "LIVE" if live else "DRY-RUN"
    slug = path.stem
    out_dir = ROOT / "exports" / "events" / slug
    handle = env("IG_HANDLE", "@utipickleball")
    print(f"[{tag}] {ev['title']} | {lab['date_label']} {lab['time_label']} | steps: {', '.join(steps)}")

    # 1. Luma --------------------------------------------------------------
    if "luma" in steps:
        if ev.get("luma_url"):
            print(f"  luma: already exists -> {ev['luma_url']}")
        elif not live:
            print("  luma: would create event on Luma")
            ev["luma_url"] = "https://luma.com/DRY-RUN"
        else:
            from utip.luma import Luma
            res = Luma(env("LUMA_API_KEY", required=True)).create_event(
                name=ev["title"], start_at=lab["start"].isoformat(), end_at=lab["end"].isoformat(),
                timezone=ev.get("timezone", "America/Chicago"),
                description_md=ev.get("description") or ev.get("blurb", ""),
                address=ev.get("address"), place_name=ev["location"])
            ev["luma_url"] = res["url"]
            # Persist so a re-run never duplicates the event.
            text = path.read_text().rstrip("\n") + f"\nluma_url: {res['url']}\n"
            path.write_text(text)
            print(f"  luma: created -> {res['url']}")
    url = ev.get("luma_url") or env("LUMA_CALENDAR_URL", "https://luma.com")

    # 2. Graphics ------------------------------------------------------------
    post_png, story_png = out_dir / "event-post.png", out_dir / "event-story.png"
    if "render" in steps:
        render_input = out_dir / "render.yaml"
        out_dir.mkdir(parents=True, exist_ok=True)
        render_input.write_text("\n".join(f"{k}: {v}" for k, v in {
            "title": ev["title"], "kind": ev.get("kind", "UTIP event"), "date_label": lab["date_label"],
            "time_label": lab["time_label"], "location": ev["location"], "blurb": ev.get("blurb", "").strip().replace("\n", " "),
        }.items()))
        subprocess.run(["node", str(ROOT / "design/render.js"), "--event", str(render_input),
                        "--out", str(out_dir.relative_to(ROOT))], check=True, cwd=ROOT)
    cap = caption(ev, lab, handle)
    (out_dir).mkdir(parents=True, exist_ok=True)
    (out_dir / "caption.txt").write_text(cap)
    print(f"  caption: {out_dir.relative_to(ROOT)}/caption.txt")

    # 3. Discord -------------------------------------------------------------
    public_image = None
    if "discord" in steps:
        desc = f"{ev.get('blurb', '').strip()}\n\n**[RSVP on Luma]({url})**"
        fields = [("When", f"{lab['date_label']}\n{lab['time_label']}"), ("Where", ev["location"])]
        if not live:
            print("  discord: would post announcement embed + image to #announcements")
        else:
            from utip.discord_webhook import post_announcement
            res = post_announcement(env("DISCORD_ANNOUNCE_WEBHOOK", required=True), title=ev["title"],
                                    description=desc, url=url, fields=fields,
                                    image_path=post_png if post_png.exists() else None,
                                    mention_role_id=env("DISCORD_MEMBER_ROLE_ID"))
            public_image = res["image_url"]
            print(f"  discord: posted message {res['message_id']}")

    # 4. Instagram -----------------------------------------------------------
    if "instagram" in steps:
        base = env("IMAGE_BASE_URL")  # optional: where exports/ is publicly hosted
        feed_url = public_image or (f"{base}/events/{slug}/event-post.png" if base else None)
        story_url = f"{base}/events/{slug}/event-story.png" if base else None
        if not live:
            print("  instagram: would publish feed post" + (" + story" if story_url else "") +
                  " (add the Luma link sticker to the story in the app)")
        elif not (env("IG_USER_ID") and env("IG_ACCESS_TOKEN")):
            print("  instagram: IG_USER_ID / IG_ACCESS_TOKEN not set -> post manually with exports + caption.txt")
        elif not feed_url:
            print("  instagram: no public image URL (run the discord step or set IMAGE_BASE_URL) -> skipped")
        else:
            from utip.instagram import Instagram
            ig = Instagram(env("IG_USER_ID"), env("IG_ACCESS_TOKEN"))
            print(f"  instagram: feed post {ig.publish_image(feed_url, cap)}")
            if story_url:
                print(f"  instagram: story {ig.publish_story(story_url)} -> now add the Luma link sticker in the app!")

    # 5. SMS -----------------------------------------------------------------
    if "sms" in steps:
        from utip.sms import build_text
        when = f"{lab['date_label']} {lab['time_label']}"
        sample = build_text("Alex", title=ev["title"], when=when, where=ev["location"], url=url)
        print(f"  sms preview ({len(sample)} chars): {sample}")
        if live:
            from utip.members import Members
            from utip.sms import Twilio
            recipients = Members(env("UTIP_API_URL", required=True), env("UTIP_API_TOKEN", required=True)).sms_list()
            tw = Twilio(env("TWILIO_ACCOUNT_SID", required=True), env("TWILIO_AUTH_TOKEN", required=True),
                        env("TWILIO_MESSAGING_SERVICE_SID"), env("TWILIO_FROM_NUMBER"))
            sent, failed = tw.broadcast(recipients, lambda n: build_text(
                n, title=ev["title"], when=when, where=ev["location"], url=url))
            print(f"  sms: sent {sent}/{len(recipients)}" + (f", failed: {failed}" if failed else ""))
        else:
            print("  sms: would text every member who opted in")

    print("\nManual follow-ups:\n"
          f"  [ ] Instagram story: upload {story_png.relative_to(ROOT)} if not auto-posted, add a LINK sticker -> {url}\n"
          "  [ ] Pin the story to the 'Events' highlight\n"
          "  [ ] Update the link-in-bio page if this is a big event")


if __name__ == "__main__":
    main()
