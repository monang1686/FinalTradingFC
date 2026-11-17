"""Build a standalone Cloudflare Pages preview, never production GitHub Pages.

Cloudflare Pages settings:
  Production branch: fut-trader-27-test
  Build command: python experimental/mobile-trader/build_pages.py
  Build output directory: experimental/mobile-trader/dist
"""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist"
OUT.mkdir(exist_ok=True)
shutil.copyfile(ROOT / "dashboard.html", OUT / "index.html")
# Publish a committed, explicitly unverified history when present.
history = ROOT / "data" / "history.json"
if history.is_file():
    (OUT / "data").mkdir(exist_ok=True)
    shutil.copyfile(history, OUT / "data" / "history.json")
(OUT / "_headers").write_text(
    "/*\n"
    "  X-Content-Type-Options: nosniff\n"
    "  Referrer-Policy: no-referrer\n"
    "  X-Frame-Options: DENY\n"
    "  Cache-Control: no-cache\n"
    "  Content-Security-Policy: default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://fc27-market.val.run; base-uri 'none'; form-action 'none'\n",
    encoding="utf-8",
)
print("Cloudflare Pages preview built at", OUT)
