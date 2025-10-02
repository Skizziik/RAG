"""
FINAL RAG Database Builder - Complete & Clean
Combines v2 structure (6 files with additional.json) + v3 cleaning + enriched metadata
"""

import json
import re
from pathlib import Path

# Excluded wiki garbage
EXCLUDED_SECTIONS = {
    'art', 'artwork', 'screenshots', 'concept art', 'gallery', 'images',
    'videos', 'trailer', 'media',
    'references', 'see also', 'external links', 'sources',
    'trivia', 'notes', 'in previous games', 'history',
    'navigation', 'categories', 'category'
}

DLC_LORDS = ["Yuan Bo", "Mother Ostankya", "The Changeling", "Dechala"]

# Race metadata
RACE_METADATA = {
    "grand_cathay": {
        "faction_type": "order",
        "playstyle": ["defensive", "balanced", "ranged"],
        "difficulty": "medium",
        "strengths": ["Magic", "Ranged units", "Defensive", "Harmony bonuses"],
        "weaknesses": ["Mobility", "Dependent on balance"],
        "keywords": ["dragons", "harmony", "yin", "yang", "cathay", "empire", "defensive"]
    },
    "kislev": {
        "faction_type": "order",
        "playstyle": ["hybrid", "cavalry", "magic"],
        "difficulty": "medium",
        "strengths": ["Hybrid units", "Cavalry", "Ice magic", "Versatile"],
        "weaknesses": ["No flying units", "Resource dependent"],
        "keywords": ["bears", "ice", "cavalry", "hybrid", "russia", "cold", "ursun"]
    },
    "khorne": {
        "faction_type": "chaos",
        "playstyle": ["aggressive", "melee"],
        "difficulty": "easy",
        "strengths": ["Melee damage", "Aggression", "No magic weakness"],
        "weaknesses": ["No ranged", "No magic", "Poor diplomacy"],
        "keywords": ["blood", "melee", "skulls", "aggressive", "khorne", "chaos", "blood god"]
    },
    "tzeentch": {
        "faction_type": "chaos",
        "playstyle": ["magic", "ranged", "mobile"],
        "difficulty": "hard",
        "strengths": ["Magic", "Ranged", "Flying units", "Teleportation"],
        "weaknesses": ["Weak melee", "Complex mechanics"],
        "keywords": ["magic", "scheming", "barriers", "flying", "tzeentch", "chaos", "change"]
    },
    "nurgle": {
        "faction_type": "chaos",
        "playstyle": ["defensive", "attrition"],
        "difficulty": "medium",
        "strengths": ["Durability", "Attrition", "Plagues", "Corruption"],
        "weaknesses": ["Slow", "Low mobility"],
        "keywords": ["plague", "slow", "durable", "attrition", "nurgle", "chaos", "decay"]
    },
    "slaanesh": {
        "faction_type": "chaos",
        "playstyle": ["fast", "aggressive", "melee"],
        "difficulty": "medium",
        "strengths": ["Speed", "Close combat", "Seduction", "Diplomacy"],
        "weaknesses": ["Low armor", "No ranged", "Fragile"],
        "keywords": ["fast", "seduction", "pleasure", "speed", "slaanesh", "chaos", "excess"]
    },
    "daemons_of_chaos": {
        "faction_type": "chaos",
        "playstyle": ["versatile", "adaptive"],
        "difficulty": "hard",
        "strengths": ["Versatile roster", "All god units", "Customizable"],
        "weaknesses": ["Complex", "Jack of all trades"],
        "keywords": ["undivided", "versatile", "daemon prince", "all gods", "chaos", "mixed"]
    },
    "ogre_kingdoms": {
        "faction_type": "neutral",
        "playstyle": ["monstrous", "mercenary"],
        "difficulty": "easy",
        "strengths": ["Large units", "Charge bonus", "Camps anywhere"],
        "weaknesses": ["No flying", "Expensive units"],
        "keywords": ["ogres", "monstrous", "camps", "meat", "mercenary", "big", "hungry"]
    }
}

def is_game_content(section_name):
    """Check if section contains game information"""
    lower_name = section_name.lower()
    for excluded in EXCLUDED_SECTIONS:
        if excluded in lower_name:
            return False
    if '[[file:' in lower_name or '{{#ev:' in lower_name:
        return False
    return True

def extract_text_from_tables(text):
    """Extract text content from MediaWiki tables"""
    if not text:
        return ""

    def extract_table_text(match):
        table_content = match.group(1)
        extracted = []
        rows = table_content.split('|-')
        for row in rows:
            lines = row.split('\n')
            for line in lines:
                line = re.sub(r'^[\|!]+', '', line.strip())
                if line and not line.startswith('class=') and not line.startswith('style=') and not line.startswith('colspan='):
                    extracted.append(line)
        return ' '.join(extracted)

    text = re.sub(r'\{\|(.*?)\|\}', extract_table_text, text, flags=re.DOTALL)
    return text

def clean_wiki_markup(text):
    """Remove wiki markup"""
    if not text:
        return ""

    # Extract tables first
    text = extract_text_from_tables(text)

    # Extract faction names from {{The X faction}} templates
    text = re.sub(r'\{\{The ([^\}]+?) faction\}\}', r'The \1', text)

    # Remove other templates
    text = re.sub(r'\{\{[^\}]+\}\}', '', text)
    text = re.sub(r'\[\[File:[^\]]+\]\]', '', text)
    text = re.sub(r'\[\[Image:[^\]]+\]\]', '', text)
    text = re.sub(r'\[\[Category:[^\]]+\]\]', '', text)
    text = re.sub(r'\[\[(?:[^\|\]]*\|)?([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_game_data(parsed_data, race_id):
    """Extract game information with metadata"""
    sections = parsed_data.get("sections", {})

    # ENRICHED META
    meta_info = RACE_METADATA.get(race_id, {})
    background = sections.get("Background", {}).get("content", "")
    short_desc = clean_wiki_markup(background[:200]) + "..." if len(background) > 200 else clean_wiki_markup(background)

    meta = {
        "id": race_id,
        "name": parsed_data.get("name", ""),
        "type": "race",
        "description": short_desc,
        "faction_type": meta_info.get("faction_type", "unknown"),
        "playstyle": meta_info.get("playstyle", []),
        "difficulty": meta_info.get("difficulty", "medium"),
        "strengths": meta_info.get("strengths", []),
        "weaknesses": meta_info.get("weaknesses", []),
        "keywords": meta_info.get("keywords", []),
        "tags": [race_id, meta_info.get("faction_type", ""), "base_game"] + meta_info.get("playstyle", [])
    }

    # OVERVIEW
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

    # MECHANICS
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

        if not content and not items:
            continue

        if 'unique' in lower_name and 'mechanic' in lower_name:
            mechanics["unique_mechanics"][section_name] = {
                "description": clean_wiki_markup(content),
                "features": items or []
            }
        elif any(word in lower_name for word in ['building', 'tech', 'commandment', 'settlement']):
            mechanics["general_mechanics"][section_name] = {
                "description": clean_wiki_markup(content),
                "details": items or []
            }
        elif 'magic' in lower_name or 'lore' in lower_name:
            mechanics["magic"][section_name] = {
                "description": clean_wiki_markup(content),
                "lores": items or []
            }

    # LEGENDARY LORDS
    factions_section = sections.get("Playable factions", {})
    factions_list = factions_section.get("list_items", []) or []

    legendary_lords = {
        "race_id": race_id,
        "factions": []
    }

    for faction_line in factions_list:
        if any(dlc in faction_line for dlc in DLC_LORDS):
            continue
        cleaned = clean_wiki_markup(faction_line)
        if cleaned and len(cleaned) > 5:
            legendary_lords["factions"].append(cleaned)

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

    # ADDITIONAL - everything else
    additional = {
        "race_id": race_id,
        "other_information": {}
    }

    captured_sections = set()
    for mech_dict in [mechanics["unique_mechanics"], mechanics["general_mechanics"], mechanics["magic"], units["roster_info"]]:
        captured_sections.update(mech_dict.keys())

    for section_name, section_data in sections.items():
        if section_name not in captured_sections and section_name not in ["Background", "How to play", "How They Play", "Playable factions"]:
            if not is_game_content(section_name):
                continue
            content = section_data.get("content", "")
            items = section_data.get("list_items", [])
            if content or items:
                additional["other_information"][section_name] = {
                    "description": clean_wiki_markup(content),
                    "details": items or []
                }

    return {
        "meta": meta,
        "overview": overview,
        "mechanics": mechanics,
        "legendary_lords": legendary_lords,
        "units": units,
        "additional": additional
    }

def save_final_database(race_id, data):
    """Save with 6 files per race"""
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

    saved_size = 0
    for filename, content in files.items():
        filepath = race_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        saved_size += len(json.dumps(content))

    print(f"  {race_id}: {saved_size} chars | Tags: {len(data['meta']['tags'])} | Keywords: {len(data['meta']['keywords'])}")

def main():
    print("="*70)
    print("FINAL RAG DATABASE BUILDER")
    print("Complete data + Clean markup + Enriched metadata")
    print("="*70)

    parsed_dir = Path("scripts/parsed_data")

    for parsed_file in sorted(parsed_dir.glob("*.json")):
        race_id = parsed_file.stem
        print(f"\nProcessing: {race_id.upper()}")

        with open(parsed_file, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)

        final_data = extract_game_data(parsed_data, race_id)
        save_final_database(race_id, final_data)

    print("\n" + "="*70)
    print("SUCCESS! Complete RAG database with enriched metadata!")
    print("="*70)

if __name__ == "__main__":
    main()
