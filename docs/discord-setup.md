# Group chat: why Discord (not WhatsApp), and how to set it up

## Decision: Discord ✅
| | Discord | WhatsApp |
|---|---|---|
| Automated onboarding / bots | Free, full bot API (welcome DMs, verify, role picker, event feed) | Needs the paid WhatsApp Business API; Communities can't run bots |
| Privacy | Members see usernames only | **Everyone sees everyone's phone number**, which matters for international students |
| Structure | Channels by topic, read-only announcements, member-only areas | One big chat + announcement group; gets noisy fast |
| Scales past 100s of members | Yes | Groups cap at 1024 and get chaotic |
| Familiar to everyone? | Less so for some intl students | Very |

The WhatsApp familiarity gap is covered by the **SMS newsletter** (everyone gets event texts without
installing anything) and the step-by-step "Get on board" post. If members really want WhatsApp later,
make a WhatsApp **Community announcement-only** group and paste the same announcements there.

## 1. Create the server (5 min)
1. Discord → **+ → Create My Own → For a club or community** → name it `UTIP · UT International Pickleball`.
   Icon: `exports/instagram/profile-picture.png`.
2. Server Settings → **Enable Community** (gives you rules screening, announcement channels, insights).
3. User Settings → Advanced → **Developer Mode ON** (needed to copy IDs).

## 2. Create the bot (10 min)
1. https://discord.com/developers/applications → **New Application** → "UTIP Bot" → upload the logo.
2. **Bot** tab → Reset Token → copy into `discord/bot/.env` as `DISCORD_BOT_TOKEN` (never share it).
3. Same tab → turn on **Server Members Intent**.
4. **OAuth2 → URL Generator**: scopes `bot` + `applications.commands`; permissions: Manage Roles,
   Manage Channels, Send Messages, Embed Links, Manage Messages, Read Message History, Mention Everyone.
   Open the generated URL and add the bot to your server.
5. Copy the server ID (right-click server icon) into `DISCORD_GUILD_ID`.

## 3. Run the bot
```bash
cd discord/bot
cp .env.example .env          # fill it in
pip install -r requirements.txt
python3 bot.py
```
In Discord type **/setup**. It creates every role, category, channel and pinned panel from `layout.py`
(safe to re-run). Then:
- Server Settings → Roles → drag **UTIP Bot** *above* Member/International/region roles (bots can only
  assign roles below their own).
- Give yourself and other officers **@Officer**.
- #officer-log → Edit channel → Integrations → **Webhooks → New** → copy URL into
  `forms/UTIP_Membership.gs` `OFFICER_WEBHOOK_URL` (new sign-up pings).
- #announcements → Webhooks → New → copy URL into `pipeline/.env` `DISCORD_ANNOUNCE_WEBHOOK`.
- Server Settings → **Invites**: create a never-expiring invite from #welcome → that's your Discord link.

### Where to host it (it must stay online for welcome DMs and verification)
- **Free:** an officer's always-on computer, or Oracle Cloud "Always Free" VM, or Google Cloud e2-micro free tier.
- **~$5/mo, easiest:** Railway / Render background worker, using `discord/bot/Dockerfile`
  (`docker build -f discord/bot/Dockerfile -t utip-bot .` from the repo root) with the `.env` values as secrets.

## What the bot automates
| When | What happens |
|---|---|
| Someone joins | Welcome DM with the 5 onboarding steps + greeting in #welcome |
| They press **Verify** (or `/verify`) | Modal asks for UT EID → checked against the Google Sheet → gets **@Member** (+ International/Domestic) → member channels unlock; logged in #bot-log |
| #get-roles | Dropdowns for home region (up to 3), student status, skill level |
| New Luma event appears | Auto-posted to #events within 30 min |
| 24 h before an event | Reminder in #events pinging @Member |
| Officer runs `/announce` | Formatted announcement in #announcements pinging @Member |
| Officer runs `/stats` | Member / international / domestic / SMS opt-in / verified counts |

## Channel map
```
START HERE (everyone)     #welcome  #rules  #verify  #get-roles
ANNOUNCEMENTS (everyone)  #announcements  #events
COMMUNITY (members)       #general  #introductions  #culture-exchange  #food-and-hangouts  #photos  🔊Lounge
PICKLEBALL (members)      #find-a-partner  #court-updates  #tips-and-gear
OFFICERS (officers)       #officer-chat  #officer-log  #bot-log
```
