# UTIP: UT International Pickleball Club launch kit

Everything needed to start the club: brand, Instagram launch posts, Discord server + onboarding bot,
member form + database, Luma events, a one-command announcement pipeline, posters, and the UT
registration guide.

> **Mission:** almost no non-religious international student orgs exist at UT, and the few there are often
> inactive or unwelcoming. UTIP is a place where international students, and every student curious about
> other cultures, connect through weekly pickleball and socials. Domestic students are very welcome.

## What's in here
| Folder | What | Guide |
|---|---|---|
| `brand/` | Logo (SVG), colours, type, AI prompts | `brand/brand.md` |
| `exports/instagram/` | Profile picture, 3 launch carousels, story, highlight covers (ready to post) | `docs/instagram-setup.md`, `content/captions.md` |
| `exports/posters/` | Letter poster + half-letter flyer (PNG + print PDF) with QR code | below |
| `design/` | HTML templates + renderer that produce all graphics | `docs/instagram-setup.md#editing-the-designs` |
| `discord/bot/` | UTIP Bot: welcome DM, EID verification, role picker, Luma feed, reminders, /announce | `docs/discord-setup.md` |
| `forms/` | Apps Script that creates the member Google Form + Sheet + private API | `forms/README.md` |
| `pipeline/` | `announce.py`: Luma → graphics → Discord → Instagram → SMS in one command | `pipeline/README.md` |
| `docs/` | Luma, SMS, UT registration, constitution template, member guide | |
| `site/` | Link-in-bio page (host free on GitHub Pages / Netlify) | |

## Launch checklist (do in this order)
**Week 1: accounts (about 2 hours total)**
1. [ ] Create a shared club Google account (e.g. `utipickleball@gmail.com`) and a shared password manager.
2. [ ] **Member form:** follow `forms/README.md` (5 min). You get the form link + API token.
3. [ ] **Discord:** follow `docs/discord-setup.md`: create server, create bot, run it, `/setup`. Make a permanent invite link.
4. [ ] **Luma:** follow `docs/luma-setup.md`: create the calendar, create the first weekly session.
5. [ ] **Links:** put the form, Discord, Luma (and link-in-bio) URLs into `design/data/club.json`, `site/index.html`,
       `forms/UTIP_Membership.gs` CONFIG, and the two `.env` files. Then re-render (QR codes!):
       ```bash
       python3 design/make_qr.py && node design/render.js
       ```
6. [ ] **Officers:** fill in `design/data/officers.json` (+ square photos in `design/data/photos/`, e.g. `"photo": "yuki.jpg"`), re-render.
7. [ ] **Link-in-bio page:** publish `site/` (GitHub Pages: Settings → Pages → deploy from branch, folder `/site`;
       or drag the folder into Netlify Drop), or use Linktree.

**Week 1: go public**
8. [ ] **Instagram:** follow `docs/instagram-setup.md`: create account, profile picture, bio, then post
       Welcome → Get on board → Meet the officers with the captions in `content/captions.md`. Pin all three.
9. [ ] Story with link sticker → member form; set up highlights.
10. [ ] **Print posters** (`exports/posters/*.pdf`): put them up in the international office area (Texas Global),
        dorms, the Union, PCL, Gregory Gym, and RecSports boards (check each building's posting rules).
11. [ ] First event: `python3 pipeline/announce.py pipeline/events/example-weekly-play.yaml` (preview), then `--live`.

**Weeks 2–6: make it official**
12. [ ] Reach 10 members → register on HornsLink: `docs/ut-org-registration.md` + `docs/constitution-template.md`.
13. [ ] **SMS:** start Twilio registration early (carrier review takes 1–3 weeks): `docs/sms-setup.md`.
14. [ ] Optional: connect Instagram to the Graph API for auto-posting; get Luma Plus for API automation.

## The weekly routine (about 10 minutes)
1. Copy last week's event YAML, change the date → `python3 pipeline/announce.py <file> --live`
2. Add the Luma link sticker to the Instagram story.
3. Day before: check RSVPs (Luma dashboard or `python3 pipeline/headcount.py`). The bot posts the 24h reminder.
4. After: post photos (with permission!) and story reposts.

## What still needs a human
- Creating the Instagram, Discord, Google, Luma and Twilio accounts (phone/email verification and terms acceptance).
- Officer names/photos, final meeting day & time, and confirming the court locations
  (`CCF or Whitaker Courts` is used throughout; change it in `design/data/club.json`).
- Adding the Luma link sticker to Instagram stories (Instagram's API doesn't support link stickers).
- Luma API paths were taken from Luma's current docs listing (`public-api.luma.com/v1/...`) but couldn't be
  tested from the build environment. If a call returns 404, adjust `PATHS` in `pipeline/utip/luma.py`.
