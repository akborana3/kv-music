import os
import yaml
import logging
from typing import List
languages = {}
languages_present = {}

LANGS_DIR = r"./strings/langs/"

def get_string(lang: str):
    return languages.get(lang, languages.get("en", {}))

def save_fixed_lang(lang_name: str, lang_data: dict):
    """Auto-fix & overwrite broken/missing yaml/txt files with corrected data."""
    try:
        path = os.path.join(LANGS_DIR, f"{lang_name}.yml")
        with open(path, "w", encoding="utf8") as f:
            yaml.dump(lang_data, f, allow_unicode=True, sort_keys=False)
        logging.info(f"[LANG-FIXED] {lang_name}.yml repaired & saved.")
    except Exception as e:
        logging.error(f"[LANG-FIX-ERROR] Could not fix {lang_name}: {e}")

# Load English first (mandatory base)
try:
    with open(os.path.join(LANGS_DIR, "en.yml"), encoding="utf8") as f:
        languages["en"] = yaml.safe_load(f) or {}
        languages_present["en"] = languages["en"].get("name", "English")
except Exception as e:
    logging.error(f"[LANG-ERROR] Failed to load en.yml: {e}")
    languages["en"] = {"name": "English"}
    languages_present["en"] = "English"

# Load all other languages (.yml or .txt)
for filename in os.listdir(LANGS_DIR):
    if not (filename.endswith(".yml") or filename.endswith(".txt")):
        continue
    if filename == "en.yml":
        continue

    language_name = filename.rsplit(".", 1)[0]  # remove .yml or .txt
    lang_data = {}

    # Step 1: Try to load YAML
    try:
        with open(os.path.join(LANGS_DIR, filename), encoding="utf8") as f:
            lang_data = yaml.safe_load(f) or {}
    except Exception as e:
        logging.error(f"[LANG-ERROR] {filename} corrupted, auto-fixing. Reason: {e}")
        lang_data = {}

    # Step 2: Auto-fill missing keys from English
    for key, value in languages["en"].items():
        if key not in lang_data:
            lang_data[key] = value

    # Step 3: Save fixed YAML (always .yml, even if it was .txt)
    save_fixed_lang(language_name, lang_data)

    # Step 4: Register language
    languages[language_name] = lang_data
    try:
        languages_present[language_name] = lang_data["name"]
    except Exception:
        logging.error(f"[LANG-ERROR] '{filename}' missing 'name' key. Added default.")
        languages_present[language_name] = f"{language_name.title()}"
