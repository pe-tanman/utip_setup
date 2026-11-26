"""Text-message newsletter via Twilio.

US texting from an app number needs A2P 10DLC registration (or a verified toll-free number).
See docs/sms-setup.md. Every message ends with opt-out language; Twilio handles STOP/HELP itself.
"""
import time

import requests


class Twilio:
    def __init__(self, account_sid, auth_token, messaging_service_sid=None, from_number=None):
        if not (messaging_service_sid or from_number):
            raise ValueError("Set TWILIO_MESSAGING_SERVICE_SID (preferred) or TWILIO_FROM_NUMBER")
        self.sid, self.auth = account_sid, (account_sid, auth_token)
        self.mss, self.from_number = messaging_service_sid, from_number

    def send(self, to, body):
        data = {"To": to, "Body": body}
        if self.mss:
            data["MessagingServiceSid"] = self.mss
        else:
            data["From"] = self.from_number
        r = requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{self.sid}/Messages.json",
                          data=data, auth=self.auth, timeout=30)
        return r.status_code < 300, (r.json().get("sid") if r.ok else r.text[:200])

    def broadcast(self, recipients, render, pause=0.2):
        """recipients: [{'name','phone'}]; render(name) -> message text."""
        sent, failed = 0, []
        for rcp in recipients:
            ok, info = self.send(rcp["phone"], render(rcp["name"]))
            if ok:
                sent += 1
            else:
                failed.append((rcp["phone"][-4:], info))
            time.sleep(pause)
        return sent, failed


def build_text(name, *, title, when, where, url):
    hi = f"Hi {name}! " if name else ""
    return f"UTIP: {hi}{title} - {when} @ {where}. RSVP: {url} Reply STOP to opt out"
