"""
Build final RAG database structure from parsed wiki data
Creates hierarchical folder structure optimized for RAG retrieval
"""

import json
import re
from pathlib import Path

# DLC legendary lords to exclude (base game only)
DLC_LORDS = ["Yuan Bo"]

def create_race_structure(parsed_data, race_id):
    """
    Create structured database from parsed wiki data
    """
    sections = parsed_data.get("sections", {})

    # Extract meta information
    meta = {
        "id": race_id,
        "name": parsed_data.get("name", ""),
        "type": "race"
    }

    # Extract overview
    overview = {
        "race_id": race_id,
        "name": parsed_data.get("name", ""),
        "description": sections.get("Background", {}).get("content", "")[:500],  # First 500 chars
        "full_background": sections.get("Background", {}).get("content", ""),
        "playstyle": sections.get("How They Play", {}).get("content", "")
    }

    # Extract mechanics
    mechanics_section = sections.get("Unique campaign mechanics", {})
    mechanics_list = mechanics_section.get("list_items", []) or []

    mechanics = {
        "race_id": race_id,
        "unique_mechanics": []
    }

    for mechanic_name in mechanics_list:
        # Clean up template syntax
        mechanic_clean = re.sub(r'\{\{|\}\}', '', mechanic_name).strip()
        mechanics["unique_mechanics"].append({
            "name": mechanic_clean,
            "description": f"Unique campaign mechanic for {parsed_data.get('name')}"
        })

    # Add specific mechanic details from dedicated sections
    if "Harmony" in sections:
        harmony_content = sections["Harmony"].get("content", "")
        for mech in mechanics["unique_mechanics"]:
            if "Harmony" in mech["name"]:
                mech["description"] = harmony_content

    # Extract magic lores
    magic_section = sections.get("Magic", {})
    magic_lores = magic_section.get("list_items", [])

    if magic_lores:
        mechanics["magic_lores"] = [
            {"name": lore.strip(), "type": "magic"}
            for lore in magic_lores
        ]

    # Extract factions and lords
    factions_section = sections.get("Playable factions", {})
    factions_content = factions_section.get("content", "")

    legendary_lords = {
        "race_id": race_id,
        "legendary_lords": [],
        "playable_factions": []
    }

    # Parse factions from content
    for line in factions_content.split('*'):
        if "led by" in line.lower():
            # Extract faction and lord info
            parts = line.split("led by")
            if len(parts) == 2:
                faction_name = re.sub(r'\{\{|\}\}|faction', '', parts[0]).strip()
                lord_name = re.sub(r'\{\{|\}\}|\.', '', parts[1]).strip()

                # Skip DLC lords
                if any(dlc in lord_name for dlc in DLC_LORDS):
                    continue

                lord_id = lord_name.lower().replace(',', '').replace(' ', '_')

                legendary_lords["legendary_lords"].append({
                    "id": lord_id,
                    "name": lord_name,
                    "faction": faction_name
                })

                legendary_lords["playable_factions"].append({
                    "name": faction_name,
                    "led_by": lord_name
                })

    # Extract units information
    units_section = sections.get("Units", {})
    harmony_section = sections.get("Harmony", {})

    units = {
        "race_id": race_id,
        "unit_characteristics": sections.get("How They Play", {}).get("content", ""),
        "harmony_mechanics": harmony_section.get("content", "") if harmony_section else None
    }

    return {
        "meta": meta,
        "overview": overview,
        "mechanics": mechanics,
        "legendary_lords": legendary_lords,
        "units": units
    }

def save_race_database(race_id, structured_data):
    """
    Save race data to hierarchical folder structure
    """
    race_dir = Path("races") / race_id
    race_dir.mkdir(parents=True, exist_ok=True)

    # Save each component
    files = {
        "_meta.json": structured_data["meta"],
        "overview.json": structured_data["overview"],
        "mechanics.json": structured_data["mechanics"],
        "legendary_lords.json": structured_data["legendary_lords"],
        "units.json": structured_data["units"]
    }

    for filename, data in files.items():
        filepath = race_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  Saved: {filepath}")

def main():
    """
    Build final database structure
    """
    print("Building RAG Database Structure")
    print("="*50)

    parsed_dir = Path("scripts/parsed_data")

    if not parsed_dir.exists():
        print("No parsed data found. Run wiki_parser.py first.")
        return

    for parsed_file in sorted(parsed_dir.glob("*.json")):
        race_id = parsed_file.stem
        print(f"\nProcessing: {race_id}")

        with open(parsed_file, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)

        # Create structured data
        structured_data = create_race_structure(parsed_data, race_id)

        # Save to database
        save_race_database(race_id, structured_data)

    print("\n" + "="*50)
    print("Database build complete!")
    print(f"Location: races/")
    print("\nStructure:")
    print("  races/")
    print("    <race_id>/")
    print("      _meta.json          # Quick reference")
    print("      overview.json       # Full description")
    print("      mechanics.json      # Unique mechanics")
    print("      legendary_lords.json # Lords and factions")
    print("      units.json          # Unit information")

if __name__ == "__main__":
    main()
