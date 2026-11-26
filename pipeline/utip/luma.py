"""Luma (luma.com) API client.

Requires Luma Plus on the calendar, and an API key from the calendar's settings -> API keys.
Luma has renamed its endpoints over time (/public/v1/event/... -> /v1/events/...). The paths
live in PATHS so a rename is a one-line fix, or set LUMA_BASE_URL / LUMA_PATHS_JSON in .env.
Check https://docs.luma.com if a call returns 404.
"""
import json
import os

import requests

BASE = os.environ.get("LUMA_BASE_URL", "https://public-api.luma.com")
PATHS = {
    "create_event": "/v1/events/create",
    "list_events": "/v1/calendar/list-events",
    "get_guests": "/v1/event/get-guests",
}
PATHS.update(json.loads(os.environ.get("LUMA_PATHS_JSON", "{}") or "{}"))


class Luma:
    def __init__(self, api_key):
        self.s = requests.Session()
        self.s.headers.update({"x-luma-api-key": api_key, "accept": "application/json"})

    def _get(self, key, **params):
        r = self.s.get(BASE + PATHS[key], params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def create_event(self, *, name, start_at, end_at, timezone, description_md, address=None,
                     place_name=None, visibility="public", require_approval=False):
        body = {
            "name": name,
            "start_at": start_at,          # ISO 8601 with offset, e.g. 2026-12-05T10:00:00-06:00
            "end_at": end_at,
            "timezone": timezone,          # e.g. America/Chicago
            "description_md": description_md,
            "visibility": visibility,
            "require_rsvp_approval": require_approval,
        }
        if address:
            body["geo_address_json"] = {"type": "manual", "address": address,
                                        "description": place_name or address}
        r = self.s.post(BASE + PATHS["create_event"], json=body, timeout=30)
        if r.status_code >= 400:
            raise RuntimeError(f"Luma create failed {r.status_code}: {r.text[:500]}")
        data = r.json()
        ev = data.get("event", data)
        event_id = ev.get("api_id") or ev.get("id") or data.get("api_id")
        url = ev.get("url") or data.get("url")
        if url and not url.startswith("http"):
            url = "https://luma.com/" + url
        return {"id": event_id, "url": url, "raw": data}

    def upcoming_events(self, after_iso):
        data = self._get("list_events", after=after_iso)
        out = []
        for entry in data.get("entries", data.get("events", [])):
            ev = entry.get("event", entry)
            url = ev.get("url", "")
            out.append({
                "id": ev.get("api_id") or ev.get("id"),
                "name": ev.get("name"),
                "start_at": ev.get("start_at"),
                "url": url if url.startswith("http") else f"https://luma.com/{url}",
                "location": (ev.get("geo_address_json") or {}).get("address", ""),
            })
        return sorted(out, key=lambda e: e["start_at"] or "")

    def guest_counts(self, event_id):
        counts, cursor = {}, None
        while True:
            params = {"event_api_id": event_id, "pagination_limit": 100}
            if cursor:
                params["pagination_cursor"] = cursor
            data = self._get("get_guests", **params)
            for entry in data.get("entries", []):
                g = entry.get("guest", entry)
                status = g.get("approval_status", "unknown")
                counts[status] = counts.get(status, 0) + 1
            cursor = data.get("next_cursor")
            if not data.get("has_more") or not cursor:
                return counts
