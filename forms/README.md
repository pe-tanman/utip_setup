# Member form + member list (Google Forms / Sheets / Apps Script)

One script creates the Google Form, the private member spreadsheet, and a tiny private API used by
the Discord bot (verification) and the pipeline (SMS list).

**Form fields:** Full name\*, UT EID\* (format-checked), Email\*, Phone\*, Discord username,
Text-message newsletter opt-in\* (with STOP/HELP consent language, required for US texting rules),
international/domestic, home country, classification, experience, how they heard. (\* = required)

## Install (about 5 minutes)
1. Sign in to the **club Google account**, go to https://script.google.com → **New project**, name it
   "UTIP Members".
2. Delete the sample code, paste all of `UTIP_Membership.gs`, and edit `CONFIG` at the top (Discord invite,
   Luma link, optional officer webhook). **Save**.
3. Choose `setup` in the function dropdown → **Run** → approve permissions ("Advanced → Go to UTIP Members"
   is normal for your own script).
4. **Execution log** prints: the form link (share this), the private sheet link, and the **API token**.
5. **Deploy → New deployment → Web app** → Execute as **Me**, Who has access **Anyone** → Deploy →
   copy the `/exec` URL. ("Anyone" is required so the bot can call it; every request still needs the
   secret token, and the API never returns EIDs or emails.)
6. Put the URL and token in `pipeline/.env` and `discord/bot/.env` as `UTIP_API_URL` / `UTIP_API_TOKEN`.
7. Shorten the form link (Send → link → "Shorten URL") and put it in `design/data/club.json` → `links.form`,
   then `python3 design/make_qr.py && node design/render.js` so the posters' QR codes are correct.

## Day-to-day
- New responses land in the **Form Responses** tab (raw) and the **Members** tab (clean, one row per EID;
  re-submitting updates the row instead of duplicating it).
- Members get an automatic welcome email with the Discord + Luma links.
- Officers get a ping in #officer-log for each sign-up (if the webhook is set).
- For the UT roster / HornsLink: run `exportRosterForHornsLink()` → "Roster export" tab.
- Lost the token? Run `showToken()`.

## Privacy
The sheet contains EIDs and phone numbers. Share it only with officers who need it, never post it, and
remove members who ask. Don't reuse the data for anything except club communication.
