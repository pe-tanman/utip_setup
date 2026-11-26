# What's live right now

_Last updated 2026-11-26. Theme: all yellow (`#FFD23F`) with deep-teal ink._

| Platform | Status | Link / ID |
|---|---|---|
| Instagram | ✅ @utip_austin, connected to **Buffer** for scheduling | https://instagram.com/utip_austin |
| Member form | ✅ Created via Zapier (Google Forms API) | https://docs.google.com/forms/d/e/1FAIpQLSeNMdK0OxRarvqIEcnPV3a4rZCL4zsUBN2K8LrAHyiHnj6Wlw/viewform · edit: https://docs.google.com/forms/d/17o2rVdPNrBEjgDV7YBRsa606WnHy3M1pSTuXpJi-wNA/edit |
| Discord | ✅ Server restructured via Zapier, permanent invite | https://discord.gg/uFwZuz9KA9 |
| Form → Discord automation | ✅ Zapier workflow, enabled, trigger active | https://zapier.com/workflow/01a218f6-2cca-7a8c-9b6e-aec1e73c2163 |
| Google Calendar | ✅ Public "UTIP · UT International Pickleball Club" calendar (America/Chicago) | Subscribe: https://calendar.google.com/calendar/r?cid=5b94b9099a75cdd09d5b2955846f51de4a1bc5f9cfe1f6cbc2ffb269739be73b@group.calendar.google.com · Web view: https://calendar.google.com/calendar/embed?src=5b94b9099a75cdd09d5b2955846f51de4a1bc5f9cfe1f6cbc2ffb269739be73b@group.calendar.google.com&ctz=America/Chicago |
| Calendar → Discord automation | ✅ Zapier workflow, enabled, trigger active: every new calendar event is posted to #events and pings @Member | https://zapier.com/workflow/01a21a37-f799-7e23-8603-da1e488892ac |
| Canva | ✅ Folder with editable yellow-theme designs | https://www.canva.com/folder/FAHcDrfFYFM |
| Linktree | ⏳ create the profile in the Linktree app (MCP can't create profiles on this plan) | |
| Luma | ⏳ to do: `docs/luma-setup.md` | |
| SMS (Twilio) | ⏳ to do: `docs/sms-setup.md` | |

## Discord layout (built through the Zapier Discord connection)
```
START HERE (everyone, read-only)  #welcome (pinned guide)  #announcements  #rules  #events
COMMUNITY (@Member only)          #general  #introductions  #culture-exchange  #find-a-partner  #court-updates
Voice Channels (@Member only)     🔊Lounge  🔊Court Chat
OFFICERS (@Officer only)          #officer-chat  #officer-log
```
Roles: **@Officer**, **@Member**, **@International**, **@Domestic**, **@Exchange / Visiting**.
Leftover from Discord's club template: the role "officers (example)" sits above the Zapier bot's role,
so it couldn't be edited automatically. Delete it in Server Settings → Roles.

## How a new member gets in (no bot hosting needed)
1. They join Discord (invite above) and can only see START HERE.
2. They fill out the member form **with their Discord username**.
3. Zapier workflow "UTIP: Form sign-up → Discord Member role" (runs within a few minutes):
   finds their Discord account → adds **@Member** (+ International / Domestic / Exchange) →
   DMs a welcome → posts a line in **#officer-log**.
4. If the username is missing or not in the server yet, #officer-log says so, and an officer adds @Member by hand
   (right-click the user → Roles).

Tested 2026-11-26 with the founder account: roles added, DM sent, log posted.

## Still optional
- `forms/UTIP_Membership.gs` (Apps Script): attaches to the same form (`EXISTING_FORM_ID`) and adds answer
  validation, a clean Members sheet, welcome emails, and the private member API used for SMS. Run `setup()` once.
- `discord/bot/`: the self-hosted bot adds the region/skill role picker and a Luma event feed. The Zapier flow
  already covers onboarding, so the bot is only an upgrade.
