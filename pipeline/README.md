# Event pipeline: one command to announce everywhere

```
 event YAML ──► Luma event ──► graphics (post + story) ──► Discord #announcements ──► Instagram ──► SMS to opted-in members
                  (or reuse       design/templates/        (webhook, pings @Member)    (Graph API, or     (Twilio, list from the
                   luma_url)      → exports/events/…                                    manual + caption)  Google Sheet API)
```

## Setup
```bash
pip install -r pipeline/requirements.txt      # requests, PyYAML
cp pipeline/.env.example pipeline/.env        # fill in what you have; missing services are skipped/explained
```
Node + Playwright are needed for the graphics (`npm i playwright && npx playwright install chromium`
on a new machine).

## Every week
1. Copy `pipeline/events/example-weekly-play.yaml` to e.g. `pipeline/events/2026-12-05-open-play.yaml`, edit it.
   (No Luma Plus? Create the event on luma.com and paste its URL as `luma_url:`.)
2. Preview everything (nothing is sent):
   ```bash
   python3 pipeline/announce.py pipeline/events/2026-12-05-open-play.yaml
   ```
   Check `exports/events/2026-12-05-open-play/` (event-post.png, event-story.png, caption.txt).
3. Publish:
   ```bash
   python3 pipeline/announce.py pipeline/events/2026-12-05-open-play.yaml --live
   ```
   Run only some steps with `--only luma,render,discord` or `--skip sms`.
4. In the Instagram app: post the story (if not auto-posted), add the **Luma link sticker**, add to the
   Events highlight.
5. The day before: `python3 pipeline/headcount.py` → how many are coming (Luma Plus), or check the Luma
   dashboard. The Discord bot also posts a 24h reminder automatically.

## Other tools
- `python3 pipeline/newsletter.py "message" [--live]`: one-off text to everyone who opted in.
- `python3 pipeline/headcount.py`: RSVP counts for upcoming events.

## Safety
- Dry run is the default. `--live` is required to send anything.
- After a live Luma step the event URL is written back into the YAML, so re-running won't create duplicates.
- SMS goes only to members who said yes on the form, and always includes "Reply STOP to opt out".
