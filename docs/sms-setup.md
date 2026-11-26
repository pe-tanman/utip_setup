# Text-message newsletter (Twilio)

Members opt in on the form. The pipeline texts them when a new event is posted; `newsletter.py` sends
one-off messages (e.g. "rain: moving to Gregory Gym").

## Rules you must follow (US carriers enforce them)
- Only text people who **opted in** (the form's consent question does this) and include
  **"Reply STOP to opt out"** (the scripts add it automatically). Twilio handles STOP/HELP replies for you.
- Unregistered app-to-person texts from a normal US number get **blocked**. Register first (below).
- Keep it to roughly 1–4 texts a month; don't send at night.

## Setup (about 30 min, then 1–3 weeks of carrier review)
1. Create a Twilio account (club email) and add ~$20 credit. A US local number is ~$1.15/mo, and texts
   cost about $0.01 each including carrier fees (check current prices).
2. Buy a number with SMS capability.
3. **Messaging → Regulatory compliance → A2P 10DLC**: register a *Sole Proprietor* brand (an officer's
   name works for a student org) **or** use a **toll-free number + toll-free verification** (often
   simpler for clubs). Campaign description: "Event announcements for UT International Pickleball Club
   members who opted in via our Google Form." Sample message: one of the pipeline previews.
   Opt-in proof: screenshot of the form's consent question.
4. Create a **Messaging Service**, add the number, copy its SID.
5. `pipeline/.env`: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_MESSAGING_SERVICE_SID`.
6. Test: `python3 pipeline/newsletter.py "Test from UTIP"` (preview), then text only yourself by
   temporarily opting in just your row, before the first real `--live` send.

**Cheaper/no-code alternative while registration is pending:** send the same message from a
free **Google Voice** number to small groups by hand, or use a texting tool built for clubs
(e.g. SimpleTexting, EZ Texting). The Members sheet's "Phone (E.164)" column exports cleanly to any of them.
