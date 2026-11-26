"""Instagram publishing via the Instagram Graph API (Business/Creator account linked to a Facebook Page).

Limits worth knowing:
  * The image must be at a public HTTPS URL (we reuse the Discord attachment URL, or IMAGE_BASE_URL).
  * Link stickers can NOT be added to stories through the API — add the Luma link sticker in the app.
  * JPEG is the officially supported format; PNG usually works, we convert to JPEG anyway.
"""
import time

import requests

GRAPH = "https://graph.facebook.com/v21.0"


class Instagram:
    def __init__(self, ig_user_id, access_token):
        self.uid, self.token = ig_user_id, access_token

    def _post(self, path, **data):
        data["access_token"] = self.token
        r = requests.post(f"{GRAPH}/{path}", data=data, timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(f"Instagram API {path} failed: {r.text[:400]}")
        return r.json()

    def _wait_ready(self, container_id, tries=20):
        for _ in range(tries):
            r = requests.get(f"{GRAPH}/{container_id}", params={"fields": "status_code", "access_token": self.token}, timeout=30)
            if r.ok and r.json().get("status_code") == "FINISHED":
                return
            time.sleep(3)
        raise RuntimeError("Instagram media container never finished processing")

    def publish_image(self, image_url, caption):
        c = self._post(f"{self.uid}/media", image_url=image_url, caption=caption)
        self._wait_ready(c["id"])
        return self._post(f"{self.uid}/media_publish", creation_id=c["id"])["id"]

    def publish_story(self, image_url):
        c = self._post(f"{self.uid}/media", image_url=image_url, media_type="STORIES")
        self._wait_ready(c["id"])
        return self._post(f"{self.uid}/media_publish", creation_id=c["id"])["id"]
