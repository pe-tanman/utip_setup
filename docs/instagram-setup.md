# Instagram setup

> I (Claude) can't create the account for you: Instagram requires a phone/email verification and a
> human to accept its terms. Everything else (name, bio, icon, posts, captions, highlight covers) is ready.

## 1. Create the account (10 min)
1. Use a **shared club email** (e.g. a new Gmail like `utipickleball@gmail.com`), not a personal one, so
   the account survives officer turnover. Store the password in a shared password manager.
2. ✅ Done: the account is **@utip_austin** (connected to Buffer for scheduling). Alternative handles considered: `utip.atx`,
   `ut.intlpickleball`, `utip_club`. (If you change the handle, update `design/data/club.json` and re-render.)
3. **Name** field (searchable!): `UTIP · UT Intl Pickleball Club`
4. **Profile picture**: `exports/instagram/profile-picture.png`
5. **Bio** (150 chars max):
   ```
   🌏 International Pickleball Club at UT Austin
   🏓 Weekly games + socials · all levels
   🤝 Int'l & domestic students welcome
   👇 Join + RSVP
   ```
6. **Link**: your link-in-bio page (`site/index.html`, see below) or a free Linktree with: Member form,
   Discord, Luma calendar.
7. Settings → **Account type and tools → Switch to professional account → Creator or Business**, category
   "Community Organization"/"Sports Club". Required for the pipeline's auto-posting and gives you insights.
8. Add officers as collaborators instead of sharing the password where possible (Meta Accounts Center).

## 2. Launch sequence
| Day | Post | File |
|-----|------|------|
| 1 | Welcome / why we started (carousel) | `exports/instagram/post1-welcome/` |
| 1 | Story: "New club alert" + link sticker → form | `exports/instagram/stories/story-join.png` |
| 2 | Get on board (carousel) | `exports/instagram/post3-get-on-board/` |
| 3 | Meet the officers (carousel) | `exports/instagram/post2-officers/` |
| 4+ | First event post + story with Luma link | made by `pipeline/announce.py` |

Captions: `content/captions.md`. Pin all three launch posts to your profile.

## 3. Story highlights
Create highlights **About / Events / Join / Team** using covers in `exports/instagram/highlight-covers/`
(post the cover as a story, add it to a new highlight, then "Edit highlight → Edit cover").

## 4. Connect Instagram to the pipeline (optional, for auto-posting)
1. Create a Facebook Page for UTIP and link it to the Instagram professional account.
2. developers.facebook.com → create an app → add **Instagram Graph API** → generate a long-lived token
   with `instagram_basic`, `instagram_content_publish`, `pages_show_list`.
3. Put `IG_USER_ID` and `IG_ACCESS_TOKEN` in `pipeline/.env`.
4. Link stickers can't be added via the API, so the pipeline posts the feed post (and story if
   `IMAGE_BASE_URL` is set); you add the Luma **link sticker** to the story in the app (30 seconds).

## Editing the designs
All graphics are HTML templates in `design/templates/` rendered with Playwright:
```bash
python3 design/make_qr.py     # after changing links in design/data/club.json
node design/render.js         # re-renders everything into exports/
```
Prefer Canva? Upload the PNGs or `brand/logo.svg` to Canva and use the palette in `brand/brand.md`.
