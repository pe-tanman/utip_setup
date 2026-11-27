# Event pipeline: add one calendar event, everything else is automatic

**Source of truth: the public UTIP Google Calendar** (owned by pe.tanman12@gmail.com).
Officers only ever do step 1.

```
 Officer adds event to UTIP Google Calendar
   title · time · location · description (put the RSVP link, e.g. Luma, as the FIRST link)
        │
        ├──▶ (within minutes) Zapier "New calendar event → Discord #events"          ✅ live
        │       posts title, time (shown in each viewer's timezone), place, details,
        │       RSVP link, "react ✅ if you're coming", add-to-calendar link; pings @Member
        │
        ├──▶ Events made in the OFFICER CONSOLE (Canva box ticked):                      ✅ live
        │       Canva designs a NEW post for this event (rotating art style, yellow/teal, logo)
        │       → officer previews → "Post to Instagram" → feed post (caption with details)
        │       + story with the same design and a link sticker → RSVP link
        │       (the calendar description gets "Instagram: Canva post from the Officer Console",
        │        which tells Zapier to skip the generic graphics below)
        │
        ├──▶ Events added straight in Google Calendar (fallback, same Zapier run):        ✅ live
        │       Instagram FEED POST "New event!": post-event-generic.png, caption with details
        │       Instagram story: story-event-generic-01.png + link sticker → RSVP link (or linktr.ee/utip)
        │
        ├──▶ (24 h before) Zapier "Event reminder 24h before → Discord"               ✅ live
        │       "Tomorrow: <title>" + time, place, RSVP link; pings @Member
        │
        └──▶ (same run) Instagram story "See you tomorrow!" via Buffer API               ✅ live
                story-event-generic-02.png + link sticker → RSVP link (or linktr.ee/utip)
```

Students see the event three more ways with no extra work: the calendar link on linktr.ee/utip,
Google Calendar subscribers get it automatically, and the Discord `#events` topic links the calendar.

## How to add an event (officers)
1. Open Google Calendar (pe.tanman12@gmail.com) → create event → choose the calendar
   **"UTIP · UT International Pickleball Club"** (not your personal one).
2. Title: short and clear, e.g. `Weekly Open Play` or `Korean Food Night + Pickleball`.
3. Location: `Whitaker Courts` / `CCF` (or a full address).
4. Description: first line = RSVP link (Luma page or a form) if there is one, then 1–3 sentences.
5. Recurring weekly sessions: set "Repeats weekly". Each occurrence gets its own 24 h reminder.
   The "new event" announcement fires once, when the series is created.

## Optional: a custom graphic for a big event
For socials or anything special, make a proper post with the date and place on it:
`python3 pipeline/announce.py pipeline/events/<event>.yaml` renders `event-post.png` + `event-story.png`
(yellow theme). Then ask Claude (Buffer is connected) to schedule them, or upload them in Buffer
yourself, with a link sticker on the story.

## Headcount
- With Luma (once connected): RSVPs on the Luma page.
- Without Luma: count the ✅ reactions on the Discord event post.

## Zapier workflows
| Workflow | Link |
|---|---|
| Form sign-up → Discord Member role | https://zapier.com/workflow/01a218f6-2cca-7a8c-9b6e-aec1e73c2163 |
| New calendar event → Discord #events | https://zapier.com/workflow/01a21a37-f799-7e23-8603-da1e488892ac |
| Event reminder 24h before → Discord | https://zapier.com/workflow/01a21a5c-e7ce-7e03-8ca9-4f305d175957 |

## Notes
- Stories are created through Buffer's GraphQL API (Zapier's built-in Buffer action has no link-sticker field),
  using the Buffer account connected in Zapier. Buffer free plan: max 10 scheduled posts at once.
- If a story step fails (e.g. Buffer disconnected), the Discord post still goes out and the Zapier run shows the error.
- Check the first automatic story on your phone to confirm the link sticker appears.

## Officer Console (web page)
https://claude.ai/artifact/7PrWK5ZHz8zFaA3YdvQQuL (source: `site/officers/index.html`)
- **New event:** creates the event on the UTIP Google Calendar (optional weekly repeat), which triggers
  the Discord post and 24 h reminder above. Optional extra post in Discord #announcements.
- **Canva post per event** (connector `Canva`, box ticked by default): after the event is saved, Canva generates a
  fresh square Instagram design (one of 10 art styles, never the same twice in a row, UTIP logo asset `MAHcD0fkfWo`).
  The officer sees the preview and an editable caption, then presses **Post to Instagram (post + story)**:
  Buffer publishes the feed post now and a story using the same design with a link sticker to the RSVP link.
  **Try another design** asks Canva for a new one; **Edit in Canva** opens it for touch-ups (then post from Buffer).
  If Canva adds a blank page, pick the right page in the preview. Canva export links expire after a few hours,
  so post from the preview the same day.
- **Announcement:** Discord #announcements (via Zapier) and/or an Instagram story with a link sticker (via Buffer), now or scheduled.
- **Upcoming:** live list from the UTIP calendar.
- It runs on claude.ai with the viewer's own connectors (Google Calendar, Zapier, Buffer, luma, Canva). Another officer needs
  the page shared with them and those connectors connected to the club accounts in their claude.ai.
- **Luma** (connector `luma`): "Create event" also makes the Luma RSVP page (one per week for repeats) and puts its link first in the calendar description, so Discord posts and Instagram story stickers point to it. The Upcoming tab lists Luma events with an RSVP-count button.
