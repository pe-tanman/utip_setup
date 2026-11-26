"""Server layout used by /setup. Edit names here, then run /setup again (it only adds what's missing)."""

REGION_ROLES = ["East Asia", "Southeast Asia", "South Asia", "Middle East & North Africa", "Sub-Saharan Africa",
                "Europe", "Latin America & Caribbean", "North America", "Oceania", "Central Asia"]
STATUS_ROLES = ["International", "Domestic", "Exchange / Visiting"]
SKILL_ROLES = ["Never played", "Beginner", "Intermediate", "Advanced"]

ROLES = (
    [{"name": "Officer", "color": 0xBF5700, "hoist": True, "mentionable": True},
     {"name": "Member", "color": 0x0F4C5C, "mentionable": True}]
    + [{"name": n} for n in STATUS_ROLES + REGION_ROLES + SKILL_ROLES]
)

# visibility: public (everyone, before verifying) | members (@Member + @Officer) | officers
CATEGORIES = [
    {"name": "START HERE", "visibility": "public", "channels": [
        {"name": "welcome", "readonly": True, "topic": "Start here! How to join UTIP."},
        {"name": "rules", "readonly": True, "topic": "Community guidelines"},
        {"name": "verify", "readonly": True, "topic": "Press Verify and enter your UT EID to unlock the server"},
        {"name": "get-roles", "readonly": True, "topic": "Pick your region, status and level"},
    ]},
    {"name": "ANNOUNCEMENTS", "visibility": "public", "channels": [
        {"name": "announcements", "readonly": True, "topic": "Official UTIP news. Turn on notifications!"},
        {"name": "events", "readonly": True, "topic": "Auto-posted from our Luma calendar. RSVP there!"},
    ]},
    {"name": "COMMUNITY", "visibility": "members", "channels": [
        {"name": "general", "topic": "Hang out"},
        {"name": "introductions", "topic": "Name, where you're from, major, and one food we have to try"},
        {"name": "culture-exchange", "topic": "Share your culture, holidays, language practice — any language welcome"},
        {"name": "food-and-hangouts", "topic": "Food spots, plans, who's free tonight"},
        {"name": "photos", "topic": "Pics from sessions & socials (ask before posting people)"},
        {"name": "Lounge", "voice": True},
    ]},
    {"name": "PICKLEBALL", "visibility": "members", "channels": [
        {"name": "find-a-partner", "topic": "Looking for people to play outside club sessions?"},
        {"name": "court-updates", "topic": "Weather, court availability, who's there now"},
        {"name": "tips-and-gear", "topic": "Drills, rules, paddle recommendations"},
    ]},
    {"name": "OFFICERS", "visibility": "officers", "channels": [
        {"name": "officer-chat"},
        {"name": "officer-log", "topic": "New member sign-ups from the Google Form webhook"},
        {"name": "bot-log", "topic": "Bot verification log"},
    ]},
]
