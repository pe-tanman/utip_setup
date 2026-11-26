"""Generate QR-code SVGs for every link in design/data/club.json.
Run: python3 design/make_qr.py   (needs: pip install qrcode)"""
import json, pathlib
import qrcode, qrcode.image.svg

here = pathlib.Path(__file__).parent
club = json.loads((here / "data/club.json").read_text())
for key, url in club["links"].items():
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathFillImage, border=1,
                      error_correction=qrcode.constants.ERROR_CORRECT_M)
    out = here / "data" / f"qr-{key}.svg"
    img.save(str(out))
    print("wrote", out.relative_to(here.parent), "->", url)
