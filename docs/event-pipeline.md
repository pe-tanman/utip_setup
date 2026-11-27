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
        ├──▶ (same run) Instagram story "New event just dropped!" via Buffer API         ✅ live
        │       story-event-generic-01.png + link sticker → RSVP link (or linktr.ee/utip)
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
