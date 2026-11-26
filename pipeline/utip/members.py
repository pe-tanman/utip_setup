"""Client for the private member API served by forms/UTIP_Membership.gs (doPost)."""
import requests


class Members:
    def __init__(self, url, token):
        self.url, self.token = url, token

    def _call(self, action, **kw):
        # Apps Script answers POST with a redirect; requests follows it with GET, which is what Google expects.
        r = requests.post(self.url, json={"token": self.token, "action": action, **kw}, timeout=60)
        r.raise_for_status()
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"member API error: {data.get('error')}")
        return data

    def verify(self, eid, discord_id, discord_name):
        return self._call("verify", eid=eid, discord_id=str(discord_id), discord_name=discord_name)

    def sms_list(self):
        return self._call("sms_list")["recipients"]

    def stats(self):
        return self._call("stats")
