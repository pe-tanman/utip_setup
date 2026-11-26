#!/usr/bin/env python3
"""UTIP Discord bot — onboarding, verification, roles, announcements and Luma event feed.

Commands (slash):
  /setup        (admin)    create/repair all roles + channels and post the welcome/verify/roles panels
  /verify                  link your Discord to the member form (UT EID) -> grants @Member
  /roles                   open the role picker (region, student status, skill level)
  /events                  upcoming events from Luma
  /links                   all UTIP links
  /announce     (officer)  post a formatted announcement to #announcements (pings @Member)
  /stats        (officer)  member counts from the Google Sheet

Automations:
  * new member joins     -> welcome DM with the onboarding steps + greeting in #welcome
  * verify button/panel  -> modal asks for UT EID, checks the member sheet, grants @Member
  * every 30 min         -> new Luma events are posted to #events; 24h-before reminder pings @Member
"""
import datetime as dt
import json
import logging
import os
import pathlib
import sys

import discord
from discord import app_commands
from discord.ext import commands, tasks

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1] / "pipeline"))
from utip.config import load_env  # noqa: E402

load_env(HERE / ".env")
from layout import CATEGORIES, REGION_ROLES, ROLES, SKILL_ROLES, STATUS_ROLES  # noqa: E402

log = logging.getLogger("utip")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.environ.get("DISCORD_GUILD_ID", "0") or 0)
LINKS = {
    "Member form": os.environ.get("LINK_FORM", "https://forms.gle/REPLACE_ME"),
    "Luma calendar": os.environ.get("LINK_LUMA", "https://luma.com/REPLACE_ME"),
    "Instagram": os.environ.get("LINK_INSTAGRAM", "https://instagram.com/utip_austin"),
}
STATE_FILE = HERE / "state.json"
ORANGE = discord.Color.from_rgb(0xBF, 0x57, 0x00)
TEAL = discord.Color.from_rgb(0x0F, 0x4C, 0x5C)


def members_api():
    url, token = os.environ.get("UTIP_API_URL"), os.environ.get("UTIP_API_TOKEN")
    if not (url and token):
        return None
    from utip.members import Members
    return Members(url, token)


def luma_api():
    key = os.environ.get("LUMA_API_KEY")
    if not key:
        return None
    from utip.luma import Luma
    return Luma(key)


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"posted_events": [], "reminded_events": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def chan(guild, name):
    return discord.utils.get(guild.text_channels, name=name)


def role(guild, name):
    return discord.utils.get(guild.roles, name=name)


def is_officer(inter: discord.Interaction):
    return inter.user.guild_permissions.administrator or any(r.name == "Officer" for r in inter.user.roles)


ONBOARDING_STEPS = (
    "**1.** Fill out the member form (2 min): {form}\n"
    "**2.** Come back here and press **Verify** in #verify (or type `/verify`) with your UT EID\n"
    "**3.** Pick your roles in #get-roles (home region, student status, skill level)\n"
    "**4.** Say hi in #introductions — where are you from, what are you studying?\n"
    "**5.** RSVP for this week on Luma: {luma}\n"
)


def onboarding_text():
    return ONBOARDING_STEPS.format(form=LINKS["Member form"], luma=LINKS["Luma calendar"])


# ---------------------------------------------------------------- UI components
class VerifyModal(discord.ui.Modal, title="Verify your UTIP membership"):
    eid = discord.ui.TextInput(label="UT EID (the one you used on the member form)",
                               placeholder="abc1234", min_length=4, max_length=12)

    async def on_submit(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=True, thinking=True)
        api = members_api()
        if api is None:
            await inter.followup.send("Verification is not configured yet — an officer will add you manually.", ephemeral=True)
            return
        try:
            res = api.verify(str(self.eid.value).strip().lower(), inter.user.id, inter.user.name)
        except Exception as exc:  # network / Apps Script hiccup
            log.exception("verify failed")
            await inter.followup.send(f"Couldn't reach the member list right now ({exc.__class__.__name__}). Try again in a minute.", ephemeral=True)
            return
        if not res.get("member"):
            await inter.followup.send(
                "I couldn't find that EID on the member list yet. Fill out the form first, wait a minute, then try again:\n"
                + LINKS["Member form"], ephemeral=True)
            return
        guild = inter.guild
        roles = [role(guild, "Member")]
        status = (res.get("status") or "").lower()
        if "international" in status or "exchange" in status:
            roles.append(role(guild, "International"))
        elif "domestic" in status:
            roles.append(role(guild, "Domestic"))
        await inter.user.add_roles(*[r for r in roles if r], reason="UTIP verify")
        await inter.followup.send(
            f"You're verified, {res.get('first_name') or inter.user.display_name}! Member channels are now unlocked. "
            "Next: pick your roles in #get-roles and introduce yourself in #introductions.", ephemeral=True)
        logch = chan(guild, "bot-log")
        if logch:
            await logch.send(f"✅ {inter.user.mention} verified as a member.")


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(discord.ui.Button(label="Member form", style=discord.ButtonStyle.link, url=LINKS["Member form"]))

    @discord.ui.button(label="Verify membership", style=discord.ButtonStyle.success, custom_id="utip:verify", emoji="✅")
    async def verify(self, inter: discord.Interaction, _):
        await inter.response.send_modal(VerifyModal())


class RoleSelect(discord.ui.Select):
    def __init__(self, group_name, names, custom_id, max_values):
        self.names = names
        super().__init__(placeholder=group_name, min_values=0, max_values=max_values, custom_id=custom_id,
                         options=[discord.SelectOption(label=n) for n in names])

    async def callback(self, inter: discord.Interaction):
        guild, member = inter.guild, inter.user
        want = set(self.values)
        add = [role(guild, n) for n in want]
        remove = [role(guild, n) for n in self.names if n not in want]
        await member.remove_roles(*[r for r in remove if r and r in member.roles], reason="role picker")
        await member.add_roles(*[r for r in add if r], reason="role picker")
        await inter.response.send_message(f"Updated: {', '.join(want) or 'cleared'}", ephemeral=True)


class RolesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect("Where is home? (pick up to 3)", REGION_ROLES, "utip:region", 3))
        self.add_item(RoleSelect("Student status", STATUS_ROLES, "utip:status", 1))
        self.add_item(RoleSelect("Pickleball level", SKILL_ROLES, "utip:skill", 1))


class AnnounceModal(discord.ui.Modal, title="Post an announcement"):
    a_title = discord.ui.TextInput(label="Title", max_length=120)
    body = discord.ui.TextInput(label="Details", style=discord.TextStyle.paragraph, max_length=1500)
    link = discord.ui.TextInput(label="Luma / link (optional)", required=False)

    async def on_submit(self, inter: discord.Interaction):
        ch = chan(inter.guild, "announcements")
        member_role = role(inter.guild, "Member")
        emb = discord.Embed(title=str(self.a_title), description=str(self.body), color=ORANGE,
                            url=str(self.link) or None)
        if self.link.value:
            emb.add_field(name="RSVP", value=str(self.link))
        emb.set_footer(text=f"Posted by {inter.user.display_name}")
        await ch.send(content=member_role.mention if member_role else None, embed=emb,
                      allowed_mentions=discord.AllowedMentions(roles=True))
        await inter.response.send_message(f"Posted in {ch.mention}.", ephemeral=True)


# ---------------------------------------------------------------- bot
class UTIPBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # needed for on_member_join (enable "Server Members Intent" in the portal)
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(VerifyView())
        self.add_view(RolesView())
        if GUILD_ID:
            g = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=g)
            await self.tree.sync(guild=g)
        else:
            await self.tree.sync()
        luma_feed.start()


bot = UTIPBot()


@bot.event
async def on_ready():
    log.info("Logged in as %s", bot.user)


@bot.event
async def on_member_join(member: discord.Member):
    emb = discord.Embed(
        title="Welcome to UTIP — UT International Pickleball Club! 🏓🌏",
        description=("We're a community for international students and anyone curious about other cultures. "
                     "Domestic students are super welcome!\n\n**Get set up in 3 minutes:**\n" + onboarding_text()),
        color=ORANGE)
    try:
        await member.send(embed=emb)
    except discord.Forbidden:
        pass  # DMs closed: the #welcome greeting below still works
    ch = chan(member.guild, "welcome")
    if ch:
        await ch.send(f"Welcome {member.mention}! 👋 Start in {chan(member.guild, 'verify').mention if chan(member.guild, 'verify') else '#verify'} "
                      "to unlock the server, then tell us where you're from in #introductions.")


# ---------------------------------------------------------------- slash commands
@bot.tree.command(description="Create/repair UTIP roles and channels and post the onboarding panels (admin).")
@app_commands.default_permissions(administrator=True)
async def setup(inter: discord.Interaction):
    await inter.response.defer(ephemeral=True, thinking=True)
    guild = inter.guild
    made = []
    for spec in ROLES:
        if not role(guild, spec["name"]):
            await guild.create_role(name=spec["name"], color=discord.Color(spec.get("color", 0)),
                                    hoist=spec.get("hoist", False), mentionable=spec.get("mentionable", False))
            made.append("@" + spec["name"])
    everyone, member_r, officer_r = guild.default_role, role(guild, "Member"), role(guild, "Officer")
    me = guild.me
    for cat in CATEGORIES:
        vis = cat["visibility"]
        ow = {me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)}
        if vis == "public":
            ow[everyone] = discord.PermissionOverwrite(view_channel=True)
        elif vis == "members":
            ow[everyone] = discord.PermissionOverwrite(view_channel=False)
            ow[member_r] = discord.PermissionOverwrite(view_channel=True)
            ow[officer_r] = discord.PermissionOverwrite(view_channel=True)
        else:  # officers
            ow[everyone] = discord.PermissionOverwrite(view_channel=False)
            ow[officer_r] = discord.PermissionOverwrite(view_channel=True)
        category = discord.utils.get(guild.categories, name=cat["name"])
        if not category:
            category = await guild.create_category(cat["name"], overwrites=ow)
            made.append(cat["name"])
        for c in cat["channels"]:
            name, readonly = c["name"], c.get("readonly", False)
            c_ow = dict(ow)
            if readonly:
                base = discord.PermissionOverwrite.from_pair(*c_ow.get(everyone, discord.PermissionOverwrite()).pair())
                base.send_messages = False
                c_ow[everyone] = base
                if vis == "members":
                    c_ow[member_r] = discord.PermissionOverwrite(view_channel=True, send_messages=False)
                c_ow[officer_r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            if c.get("voice"):
                if not discord.utils.get(guild.voice_channels, name=name):
                    await guild.create_voice_channel(name, category=category, overwrites=c_ow)
                    made.append("🔊" + name)
            elif not chan(guild, name):
                await guild.create_text_channel(name, category=category, overwrites=c_ow, topic=c.get("topic"))
                made.append("#" + name)

    await post_panels(guild)
    await inter.followup.send("Setup complete. Created: " + (", ".join(made) or "nothing new (all existed)") +
                              "\nNext: give yourself and other officers the @Officer role, and drag the bot's role above "
                              "the roles it assigns (Server Settings → Roles).", ephemeral=True)


async def post_panels(guild):
    """(Re)post the pinned onboarding panels if they aren't there yet."""
    async def ensure(channel_name, marker, **kwargs):
        ch = chan(guild, channel_name)
        if not ch:
            return
        async for m in ch.history(limit=20):
            if m.author == guild.me and m.embeds and m.embeds[0].footer and m.embeds[0].footer.text == marker:
                return
        msg = await ch.send(**kwargs)
        await msg.pin()

    welcome = discord.Embed(title="Welcome to UTIP 🏓🌏", color=ORANGE, description=(
        "**UT International Pickleball Club** — a welcoming, non-religious community for international students and "
        "everyone who wants to connect across cultures. Domestic students: you're so welcome here!\n\n"
        "We play every week at CCF or Whitaker Courts and host socials & culture nights.\n\n**Get started:**\n" + onboarding_text()))
    welcome.set_footer(text="utip:welcome")
    await ensure("welcome", "utip:welcome", embed=welcome)

    rules = discord.Embed(title="Community guidelines", color=TEAL, description=(
        "1. **Be kind and welcoming.** Everyone is new somewhere. No harassment, hate speech or discrimination — "
        "about nationality, accent, religion, race, gender, sexuality, or anything else.\n"
        "2. **English is our shared language** in public channels so everyone can join in — other languages are "
        "welcome in #culture-exchange.\n"
        "3. **No spam, selling or promotion** without officer approval.\n"
        "4. **Respect privacy.** Don't share other people's photos or info without asking.\n"
        "5. **Play safe & play fair.** Call your own lines, rotate courts, include beginners.\n"
        "6. Follow UT's student conduct rules and Discord's Terms of Service.\n\n"
        "Problems? DM any @Officer. We handle reports confidentially."))
    rules.set_footer(text="utip:rules")
    await ensure("rules", "utip:rules", embed=rules)

    verify = discord.Embed(title="Verify your membership", color=ORANGE, description=(
        "1) Fill out the **member form** (button below) if you haven't.\n"
        "2) Press **Verify membership** and enter your UT EID.\n\n"
        "This unlocks the member channels. Your EID is only used to match you to the member list."))
    verify.set_footer(text="utip:verify")
    await ensure("verify", "utip:verify", embed=verify, view=VerifyView())

    roles = discord.Embed(title="Pick your roles", color=TEAL, description=(
        "Tell us where home is, whether you're an international or domestic student, and your level — "
        "it helps us match partners and plan culture nights. You can change these anytime."))
    roles.set_footer(text="utip:roles")
    await ensure("get-roles", "utip:roles", embed=roles, view=RolesView())


@bot.tree.command(description="Verify your UTIP membership with your UT EID.")
async def verify(inter: discord.Interaction):
    await inter.response.send_modal(VerifyModal())


@bot.tree.command(description="Pick your region, student status and skill-level roles.")
async def roles(inter: discord.Interaction):
    await inter.response.send_message("Pick your roles:", view=RolesView(), ephemeral=True)


@bot.tree.command(description="All UTIP links.")
async def links(inter: discord.Interaction):
    emb = discord.Embed(title="UTIP links", color=ORANGE,
                        description="\n".join(f"**{k}:** {v}" for k, v in LINKS.items()))
    await inter.response.send_message(embed=emb, ephemeral=True)


@bot.tree.command(description="Upcoming UTIP events (from Luma).")
async def events(inter: discord.Interaction):
    luma = luma_api()
    if not luma:
        await inter.response.send_message(f"See our calendar: {LINKS['Luma calendar']}", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True)
    evs = luma.upcoming_events(dt.datetime.now(dt.timezone.utc).isoformat())[:8]
    if not evs:
        await inter.followup.send("No upcoming events posted yet — check back soon!", ephemeral=True)
        return
    lines = [f"**{e['name']}** — <t:{int(dt.datetime.fromisoformat(e['start_at'].replace('Z', '+00:00')).timestamp())}:F>\n{e['url']}" for e in evs]
    await inter.followup.send(embed=discord.Embed(title="Upcoming events", description="\n\n".join(lines), color=TEAL), ephemeral=True)


@bot.tree.command(description="Post an announcement to #announcements (officers).")
async def announce(inter: discord.Interaction):
    if not is_officer(inter):
        await inter.response.send_message("Officers only.", ephemeral=True)
        return
    await inter.response.send_modal(AnnounceModal())


@bot.tree.command(description="Member counts from the member sheet (officers).")
async def stats(inter: discord.Interaction):
    if not is_officer(inter):
        await inter.response.send_message("Officers only.", ephemeral=True)
        return
    api = members_api()
    if not api:
        await inter.response.send_message("UTIP_API_URL / UTIP_API_TOKEN not configured.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True)
    s = api.stats()
    await inter.followup.send(
        f"**Members:** {s['members']}  ·  International: {s['international']}  ·  Domestic: {s['domestic']}\n"
        f"**Text alerts:** {s['sms_opt_in']}  ·  **Discord verified:** {s['discord_verified']}", ephemeral=True)


# ---------------------------------------------------------------- Luma feed
@tasks.loop(minutes=30)
async def luma_feed():
    luma = luma_api()
    if not luma or not GUILD_ID:
        return
    guild = bot.get_guild(GUILD_ID)
    ch = guild and chan(guild, "events")
    if not ch:
        return
    state = load_state()
    now = dt.datetime.now(dt.timezone.utc)
    try:
        evs = luma.upcoming_events(now.isoformat())
    except Exception:
        log.exception("luma fetch failed")
        return
    member_role = role(guild, "Member")
    for e in evs:
        start = dt.datetime.fromisoformat(e["start_at"].replace("Z", "+00:00"))
        ts = int(start.timestamp())
        if e["id"] not in state["posted_events"]:
            emb = discord.Embed(title=e["name"], url=e["url"], color=ORANGE,
                                description=f"🗓 <t:{ts}:F> (<t:{ts}:R>)\n📍 {e['location'] or 'see Luma'}\n\n**[RSVP on Luma]({e['url']})**")
            await ch.send(content="📣 New event!", embed=emb)
            state["posted_events"].append(e["id"])
        if e["id"] not in state["reminded_events"] and dt.timedelta(0) < start - now <= dt.timedelta(hours=24):
            await ch.send(f"{member_role.mention if member_role else ''} ⏰ **{e['name']}** is <t:{ts}:R>! "
                          f"RSVP so we know how many courts to grab: {e['url']}",
                          allowed_mentions=discord.AllowedMentions(roles=True))
            state["reminded_events"].append(e["id"])
    save_state(state)


@luma_feed.before_loop
async def _wait():
    await bot.wait_until_ready()


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Set DISCORD_BOT_TOKEN in discord/bot/.env (see .env.example)")
    bot.run(TOKEN)
