# Luma setup (event pages + RSVPs)

Every session and social gets a Luma page. Instagram stories link to it, so you always know how many
people are coming (`python3 pipeline/headcount.py`).

## 1. Create the calendar (free)
1. https://luma.com → sign up with the club Google account.
2. **Create Calendar** → "UTIP · UT International Pickleball Club". Avatar: `exports/instagram/profile-picture.png`,
   cover: `exports/instagram/post1-welcome/post1-welcome-01.png`, tint colour `#BF5700`.
3. Description: *"Weekly pickleball + socials for international students and everyone curious about the world.
   All levels welcome. Join our member list & Discord: [link-in-bio]"*.
4. Set a short calendar URL (e.g. `luma.com/utip`) → put it in `design/data/club.json` (`links.luma`),
   `pipeline/.env` (`LUMA_CALENDAR_URL`) and the bot `.env` (`LINK_LUMA`).
5. Add the other officers as calendar **admins**.

## 2. Registration questions (optional)
Event → Registration → add "UT EID (optional)" and "First time at UTIP?" so you can spot new people and
invite them to the member form.

## 3. Weekly event: two options
- **Free plan:** create it in Luma by hand (or duplicate last week's event), then run the pipeline with
  `luma_url:` filled in the YAML. It does everything else.
- **Luma Plus (paid):** unlocks the API → put `LUMA_API_KEY` in `pipeline/.env` and the bot `.env`.
  The pipeline then creates events itself, the bot auto-posts new events and 24h reminders in Discord, and
  `headcount.py` shows RSVPs. (Plus also removes Luma's fees if you ever sell tickets.)

## 4. Instagram ↔ Luma
For every event story: Instagram app → story → sticker → **Link** → paste the Luma event URL →
customise the text to "RSVP". Put the story into the **Events** highlight.
