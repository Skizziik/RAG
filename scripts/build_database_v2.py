"""
Build complete RAG database - saves ALL wiki sections without filtering
Optimized for maximum information retention
"""

import json
from pathlib import Path

# DLC legendary lords to exclude
DLC_LORDS = ["Yuan Bo", "Mother Ostankya"]

def build_complete_race_data(parsed_data, race_id):
    """
    Build database keeping ALL information from wiki
    """
    sections = parsed_data.get("sections", {})

    # Meta - quick reference
    meta = {
        "id": race_id,
        "name": parsed_data.get("name", ""),
        "type": "race"
    }

    # Overview - combine background and playstyle
    background = sections.get("Background", {}).get("content", "")
    how_to_play = sections.get("How to play", {}) or sections.get("How They Play", {})
    playstyle_content = how_to_play.get("content", "")
    playstyle_list = how_to_play.get("list_items", [])

    overview = {
        "race_id": race_id,
        "name": parsed_data.get("name", ""),
        "background": background,
        "playstyle": {
            "description": playstyle_content,
            "key_features": playstyle_list or []
        }
    }

    # Mechanics - collect from multiple sections
    mechanics = {
        "race_id": race_id,
        "campaign_mechanics": {},
        "battle_mechanics": {},
        "magic": {}
    }

    # Scan for relevant sections
    for section_name, section_data in sections.items():
        lower_name = section_name.lower()

        # Campaign mechanics
        if any(keyword in lower_name for keyword in ['mechanic', 'campaign', 'unique']):
            mechanics["campaign_mechanics"][section_name] = {
                "content": section_data.get("content", ""),
                "details": section_data.get("list_items", [])
            }

        # Battle mechanics
        if any(keyword in lower_name for keyword in ['battle', 'combat', 'harmony']):
            mechanics["battle_mechanics"][section_name] = {
                "content": section_data.get("content", ""),
                "details": section_data.get("list_items", [])
            }

        # Magic
        if 'magic' in lower_name or 'lore' in lower_name:
            mechanics["magic"][section_name] = {
                "content": section_data.get("content", ""),
                "lores": section_data.get("list_items", [])
            }

    # Legendary Lords
    factions_section = sections.get("Playable factions", {})
    factions_list = factions_section.get("list_items", []) or []

    legendary_lords = {
        "race_id": race_id,
        "lords_and_factions": []
    }

    for faction_line in factions_list:
        # Skip DLC mentions
        if any(dlc in faction_line for dlc in DLC_LORDS):
            continue

        # Clean and store
        cleaned = faction_line.replace("{{", "").replace("}}", "").replace("faction", "").strip()
        if cleaned and len(cleaned) > 5:  # Skip empty or malformed
            legendary_lords["lords_and_factions"].append(cleaned)

    # Units - comprehensive unit information
    units = {
        "race_id": race_id,
        "roster_info": {}
    }

    for section_name, section_data in sections.items():
        lower_name = section_name.lower()
        if any(keyword in lower_name for keyword in ['unit', 'roster', 'army']):
            units["roster_info"][section_name] = {
                "content": section_data.get("content", ""),
                "details": section_data.get("list_items", [])
            }

    # Additional - everything else we haven't categorized
    additional = {
        "race_id": race_id,
        "other_information": {}
    }

    # Capture all other sections
    captured_sections = set()
    for mech_dict in [mechanics["campaign_mechanics"], mechanics["battle_mechanics"], mechanics["magic"], units["roster_info"]]:
        captured_sections.update(mech_dict.keys())

    for section_name, section_data in sections.items():
        if section_name not in captured_sections and section_name not in ["Background", "How to play", "How They Play", "Playable factions"]:
            content = section_data.get("content", "")
            items = section_data.get("list_items", [])
            if content or items:  # Only save if has data
                additional["other_information"][section_name] = {
                    "content": content,
                    "details": items
                }

    return {
        "meta": meta,
        "overview": overview,
        "mechanics": mechanics,
        "legendary_lords": legendary_lords,
        "units": units,
        "additional": additional
    }

def save_race_database(race_id, data):
    """Save to races/ folder"""
    race_dir = Path("races") / race_id
    race_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "_meta.json": data["meta"],
        "overview.json": data["overview"],
        "mechanics.json": data["mechanics"],
        "legendary_lords.json": data["legendary_lords"],
        "units.json": data["units"],
        "additional.json": data["additional"]
    }

    for filename, content in files.items():
        filepath = race_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

    print(f"  Saved {race_id}: {sum(len(json.dumps(v)) for v in files.values())} chars total")

def main():
    print("Building COMPLETE RAG Database (Maximum Information)")
    print("="*60)

    parsed_dir = Path("scripts/parsed_data")

    for parsed_file in sorted(parsed_dir.glob("*.json")):
        race_id = parsed_file.stem
        print(f"\nProcessing: {race_id}")

        with open(parsed_file, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)

        race_data = build_complete_race_data(parsed_data, race_id)
        save_race_database(race_id, race_data)

    print("\n" + "="*60)
    print("COMPLETE! Check races/ folder")

if __name__ == "__main__":
    main()
