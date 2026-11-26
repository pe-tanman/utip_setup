"""Post announcements to a Discord channel through a channel webhook (no bot needed)."""
import json
import pathlib

import requests


def post_announcement(webhook_url, *, title, description, url=None, fields=(), image_path=None,
                      mention_role_id=None, color=0xBF5700):
    embed = {"title": title, "description": description, "color": color,
             "fields": [{"name": n, "value": v, "inline": True} for n, v in fields]}
    if url:
        embed["url"] = url
    payload = {
        "username": "UTIP Announcements",
        "content": f"<@&{mention_role_id}>" if mention_role_id else "",
        "allowed_mentions": {"roles": [str(mention_role_id)]} if mention_role_id else {"parse": []},
        "embeds": [embed],
    }
    files = None
    if image_path:
        name = pathlib.Path(image_path).name
        embed["image"] = {"url": f"attachment://{name}"}
        files = {"files[0]": (name, open(image_path, "rb"), "image/png")}
    r = requests.post(webhook_url + "?wait=true",
                      data={"payload_json": json.dumps(payload)}, files=files, timeout=60)
    r.raise_for_status()
    msg = r.json()
    attachments = msg.get("attachments") or []
    # The attachment URL is public for a while, which is enough for Instagram to fetch the image.
    return {"message_id": msg.get("id"), "image_url": attachments[0]["url"] if attachments else None}
