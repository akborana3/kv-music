# PragyanMusic/plugins/tools/cookies.py
# /cookies (owner-only): reply to Netscape cookies text or .txt doc to update root cookies.txt

from __future__ import annotations

import os
import re
from pathlib import Path

from pyrogram import filters
from pyrogram.types import Message

from PragyanMusic import app
from config import OWNER_ID, BANNED_USERS

COOKIES_PATH = Path("cookies.txt").resolve()

# Accept both tab- and space-separated cookie rows
_COOKIE_ROW_RE = re.compile(
    r"^(?P<domain>\S+)\s+(?P<flag>TRUE|FALSE)\s+(?P<path>\S*)\s+(?P<secure>TRUE|FALSE)\s+(?P<expiry>\d+)\s+(?P<name>[^\s=]+)\s+(?P<value>.*)$",
    re.MULTILINE,
)

def _normalize_to_netscape(text: str) -> list[str]:
    """Convert any whitespace-separated cookie lines to proper Netscape (tab-separated) and keep header comments."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines_in = text.split("\n")
    out: list[str] = []
    for ln in lines_in:
        if not ln.strip():
            continue
        if ln.lstrip().startswith("#"):
            out.append(ln.rstrip())
            continue
        m = _COOKIE_ROW_RE.match(ln)
        if not m:
            # Skip junk
            continue
        gd = m.groupdict()
        # Sanity: required parts must exist
        if not all(k in gd and gd[k] is not None for k in ("domain","flag","path","secure","expiry","name")):
            continue
        # Rebuild as Netscape with TABS
        rebuilt = "\t".join([
            gd["domain"],
            gd["flag"],
            gd["path"],
            gd["secure"],
            gd["expiry"],
            gd["name"],
            gd.get("value",""),
        ]).rstrip()
        out.append(rebuilt)
    return out

def _count_rows(lines: list[str]) -> int:
    return sum(1 for ln in lines if ln and not ln.startswith("#"))

@app.on_message(
    filters.command(["cookies"], prefixes=["/", "!", ".", "$", "%", "#"]) 
    & filters.user(OWNER_ID) 
    & ~BANNED_USERS
)
async def cookies_update_handler(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text(
            "Reply to the cookies text or attach a `.txt` file containing Netscape cookies."
        )

    replied = message.reply_to_message
    data: str | None = None
    temp_path: Path | None = None

    try:
        if replied.document:
            # Basic size safeguard (1 MB)
            if replied.document.file_name and not replied.document.file_name.lower().endswith(".txt"):
                return await message.reply_text("Send a `.txt` cookies file or paste cookies as text.")
            if replied.document.file_size and replied.document.file_size > 1_000_000:
                return await message.reply_text("File too large. Keep cookies file under 1 MB.")
            path = await replied.download()
            temp_path = Path(path)
            try:
                data = temp_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                data = temp_path.read_text(encoding="latin-1", errors="ignore")
        elif replied.text:
            data = replied.text
        else:
            return await message.reply_text("Please reply to a text message or a `.txt` document.")
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

    if not data or not data.strip():
        return await message.reply_text("No cookies found in the replied message.")

    # Normalize & validate
    lines = _normalize_to_netscape(data)

    # Ensure standard header is present
    header_present = any("Netscape HTTP Cookie File" in ln for ln in lines)
    if not header_present:
        header = [
            "# Netscape HTTP Cookie File",
            "# http://curl.haxx.se/rfc/cookie_spec.html",
            "# This is a generated file!  Do not edit.",
            "",
        ]
        lines = header + lines

    saved = _count_rows(lines)
    if saved == 0:
        return await message.reply_text("No valid cookie lines detected. Make sure you sent Netscape-format cookies.")

    # Write atomically
    try:
        tmp = COOKIES_PATH.with_suffix(".txt.tmp")
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(tmp, COOKIES_PATH)
        try:
            os.chmod(COOKIES_PATH, 0o600)
        except Exception:
            pass
    except Exception as e:
        return await message.reply_text(f"Failed to write cookies: `{type(e).__name__}: {e}`")

    return await message.reply_text(f"✅ Cookies updated in `cookies.txt`\n• Saved cookie rows: **{saved}**")
