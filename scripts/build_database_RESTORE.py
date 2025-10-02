"""
Build CLEAN RAG database - filters out wiki garbage, keeps only game information
"""

import json
import re
from pathlib import Path

# Sections to EXCLUDE (wiki garbage)
EXCLUDED_SECTIONS = {
    'art', 'artwork', 'screenshots', 'concept art', 'gallery', 'images',
    'videos', 'trailer', 'media',
    'references', 'see also', 'external links', 'sources',
    'trivia', 'notes', 'in previous games', 'history',
    'navigation', 'categories', 'category'
}

# DLC lords to exclude
DLC_LORDS = ["Yuan Bo", "Mother Ostankya", "The Changeling", "Dechala"]

def is_game_content(section_name):
    """Check if section contains actual game information"""
    lower_name = section_name.lower()

    # Exclude garbage sections
    for excluded in EXCLUDED_SECTIONS:
        if excluded in lower_name:
            return False

    # Exclude wiki templates and files
    if '[[file:' in lower_name or '{{#ev:' in lower_name:
        return False

    return True

def clean_wiki_markup(text):
    """Remove wiki markup but keep content"""
    if not text:
        return ""

    # Remove wiki templates like {{Main|...}}
    text = re.sub(r'\{\{Main\|[^\}]+\}\}', '', text)
    text = re.sub(r'\{\{[^\}]+\}\}', '', text)

    # Remove wiki tables (they're messy in text form)
    text = re.sub(r'\{\|.*?\|\}', '', text, flags=re.DOTALL)

    # Remove file references
    text = re.sub(r'\[\[File:[^\]]+\]\]', '', text)
    text = re.sub(r'\[\[Image:[^\]]+\]\]', '', text)

    # Remove category links
    text = re.sub(r'\[\[Category:[^\]]+\]\]', '', text)

    # Clean but keep content
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def extract_game_data(parsed_data, race_id):
    """Extract only game-relevant information"""
    sections = parsed_data.get("sections", {})

    # META
    meta = {
        "id": race_id,
        "name": parsed_data.get("name", ""),
        "type": "race"
    }

    # OVERVIEW
    background = sections.get("Background", {}).get("content", "")
    # Try all possible variations of "how to play"
    how_to_play = (sections.get("How to play", {}) or
                   sections.get("How They Play", {}) or
                   sections.get("How they play", {}) or
                   {})

    overview = {
        "race_id": race_id,
        "name": parsed_data.get("name", ""),
        "background": clean_wiki_markup(background),
        "how_to_play": clean_wiki_markup(how_to_play.get("content", "")),
        "key_features": how_to_play.get("list_items", []) or []
    }

    # MECHANICS - only game mechanics
    mechanics = {
        "race_id": race_id,
        "unique_mechanics": {},
        "general_mechanics": {},
        "magic": {}
    }

    for section_name, section_data in sections.items():
        if not is_game_content(section_name):
            continue

        lower_name = section_name.lower()
        content = section_data.get("content", "")
        items = section_data.get("list_items", [])

        # Skip if no real content
        if not content and not items:
            continue

        # Unique mechanics
        if 'unique' in lower_name and 'mechanic' in lower_name:
            mechanics["unique_mechanics"][section_name] = {
                "description": clean_wiki_markup(content),
                "features": items or []
            }

        # General mechanics (buildings, tech, etc)
        elif any(word in lower_name for word in ['building', 'tech', 'commandment', 'settlement']):
            mechanics["general_mechanics"][section_name] = {
                "description": clean_wiki_markup(content),
                "details": items or []
            }

        # Magic
        elif 'magic' in lower_name or 'lore' in lower_name:
            mechanics["magic"][section_name] = {
                "description": clean_wiki_markup(content),
                "lores": items or []
            }

    # BATTLE - combat mechanics
    battle = {
        "race_id": race_id,
        "combat_info": {}
    }

    for section_name, section_data in sections.items():
        if not is_game_content(section_name):
            continue

        lower_name = section_name.lower()
        if any(word in lower_name for word in ['battle', 'combat', 'harmony', 'army abilities']):
            content = section_data.get("content", "")
            items = section_data.get("list_items", [])

            if content or items:
                battle["combat_info"][section_name] = {
                    "description": clean_wiki_markup(content),
                    "details": items or []
                }

    # UNITS
    units = {
        "race_id": race_id,
        "roster_info": {}
    }

    for section_name, section_data in sections.items():
        if not is_game_content(section_name):
            continue

        lower_name = section_name.lower()
        if any(word in lower_name for word in ['unit', 'roster', 'army']):
            content = section_data.get("content", "")
            items = section_data.get("list_items", [])

            if content or items:
                units["roster_info"][section_name] = {
                    "description": clean_wiki_markup(content),
                    "unit_types": items or []
                }

    # LEGENDARY LORDS
    factions_section = sections.get("Playable factions", {})
    factions_list = factions_section.get("list_items", []) or []

    lords = {
        "race_id": race_id,
        "factions": []
    }

    for faction_line in factions_list:
        # Skip DLC
        if any(dlc in faction_line for dlc in DLC_LORDS):
            continue

        # Clean
        cleaned = clean_wiki_markup(faction_line)
        if cleaned and len(cleaned) > 5:
            lords["factions"].append(cleaned)

    return {
        "meta": meta,
        "overview": overview,
        "mechanics": mechanics,
        "battle": battle,
        "units": units,
        "lords": lords
    }

def save_clean_database(race_id, data):
    """Save cleaned data"""
    race_dir = Path("races") / race_id
    race_dir.mkdir(parents=True, exist_ok=True)

    # Only save files with content
    files = {
        "_meta.json": data["meta"],
        "overview.json": data["overview"],
        "mechanics.json": data["mechanics"],
        "battle.json": data["battle"],
        "units.json": data["units"],
        "lords.json": data["lords"]
    }

    saved_size = 0
    for filename, content in files.items():
        # Skip if empty
        if not any(content.values()):
            continue

        filepath = race_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

        saved_size += len(json.dumps(content))

    print(f"  {race_id}: {saved_size} chars (clean)")

def main():
    print("Building CLEAN Game Database (No Wiki Garbage)")
    print("="*60)

    parsed_dir = Path("scripts/parsed_data")

    for parsed_file in sorted(parsed_dir.glob("*.json")):
        race_id = parsed_file.stem
        print(f"Processing: {race_id}")

        with open(parsed_file, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)

        clean_data = extract_game_data(parsed_data, race_id)
        save_clean_database(race_id, clean_data)

    print("\n" + "="*60)
    print("DONE! Clean game database ready for RAG")

if __name__ == "__main__":
    main()
