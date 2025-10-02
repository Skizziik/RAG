"""
Prepare RAG database for ChromaDB ingestion
Converts structured JSON files into chunks optimized for HuggingFace embeddings
"""

import json
from pathlib import Path

def create_chunks_from_race(race_dir):
    """
    Convert a race's JSON files into text chunks with metadata
    """
    race_id = race_dir.name
    chunks = []

    # Read metadata
    meta_file = race_dir / "_meta.json"
    if not meta_file.exists():
        return chunks

    with open(meta_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    # Base metadata for all chunks of this race
    base_metadata = {
        "race": race_id,
        "race_name": meta.get("name", ""),
        "faction_type": meta.get("faction_type", ""),
        "difficulty": meta.get("difficulty", ""),
        "playstyle": ",".join(meta.get("playstyle", [])),
        "keywords": ",".join(meta.get("keywords", []))
    }

    # OVERVIEW - Split into separate chunks to avoid large sizes
    overview_file = race_dir / "overview.json"
    if overview_file.exists():
        with open(overview_file, 'r', encoding='utf-8') as f:
            overview = json.load(f)

        # CHUNK 1: Background (lore/history)
        if overview.get("background"):
            background_text = overview['background']
            # If background is too large (>2500 chars), split into paragraphs
            if len(background_text) > 2500:
                paragraphs = background_text.split('. ')
                mid_point = len(paragraphs) // 2

                chunks.append({
                    "id": f"{race_id}_background_part1",
                    "text": f"Background - Part 1:\n\n{'. '.join(paragraphs[:mid_point])}.",
                    "metadata": {**base_metadata, "category": "background"}
                })
                chunks.append({
                    "id": f"{race_id}_background_part2",
                    "text": f"Background - Part 2:\n\n{'. '.join(paragraphs[mid_point:])}",
                    "metadata": {**base_metadata, "category": "background"}
                })
            else:
                chunks.append({
                    "id": f"{race_id}_background",
                    "text": f"Background:\n\n{background_text}",
                    "metadata": {**base_metadata, "category": "background"}
                })

        # CHUNK 2: Gameplay (how to play + key features)
        gameplay_parts = []
        if overview.get("how_to_play"):
            gameplay_parts.append(f"How to Play:\n\n{overview['how_to_play']}")
        if overview.get("key_features"):
            features = "\n- " + "\n- ".join(overview["key_features"])
            gameplay_parts.append(f"Key Features:{features}")

        if gameplay_parts:
            chunks.append({
                "id": f"{race_id}_gameplay",
                "text": "\n\n".join(gameplay_parts),
                "metadata": {**base_metadata, "category": "gameplay"}
            })

    # MECHANICS chunks
    mechanics_file = race_dir / "mechanics.json"
    if mechanics_file.exists():
        with open(mechanics_file, 'r', encoding='utf-8') as f:
            mechanics = json.load(f)

        # Unique mechanics
        for mech_name, mech_data in mechanics.get("unique_mechanics", {}).items():
            desc = mech_data.get("description", "")
            features = mech_data.get("features", [])

            if desc or features:
                text_parts = [f"Unique Mechanic: {mech_name}"]
                if desc:
                    text_parts.append(desc)
                if features:
                    text_parts.append("Features:\n- " + "\n- ".join(features))

                chunks.append({
                    "id": f"{race_id}_mechanic_{len(chunks)}",
                    "text": "\n\n".join(text_parts),
                    "metadata": {**base_metadata, "category": "mechanics", "subcategory": "unique"}
                })

        # General mechanics
        for mech_name, mech_data in mechanics.get("general_mechanics", {}).items():
            desc = mech_data.get("description", "")
            details = mech_data.get("details", [])

            if desc or details:
                text_parts = [f"General Mechanic: {mech_name}"]
                if desc:
                    text_parts.append(desc)
                if details:
                    text_parts.append("Details:\n- " + "\n- ".join(details))

                chunks.append({
                    "id": f"{race_id}_mechanic_{len(chunks)}",
                    "text": "\n\n".join(text_parts),
                    "metadata": {**base_metadata, "category": "mechanics", "subcategory": "general"}
                })

        # Magic
        for magic_name, magic_data in mechanics.get("magic", {}).items():
            desc = magic_data.get("description", "")
            lores = magic_data.get("lores", [])

            if desc or lores:
                text_parts = [f"Magic: {magic_name}"]
                if desc:
                    text_parts.append(desc)
                if lores:
                    text_parts.append("Lores of Magic:\n- " + "\n- ".join(lores))

                chunks.append({
                    "id": f"{race_id}_magic_{len(chunks)}",
                    "text": "\n\n".join(text_parts),
                    "metadata": {**base_metadata, "category": "magic"}
                })

    # BATTLE chunks
    battle_file = race_dir / "battle.json"
    if battle_file.exists():
        with open(battle_file, 'r', encoding='utf-8') as f:
            battle = json.load(f)

        for battle_name, battle_data in battle.get("combat_info", {}).items():
            desc = battle_data.get("description", "")
            details = battle_data.get("details", [])

            if desc or details:
                text_parts = [f"Battle Info: {battle_name}"]
                if desc:
                    text_parts.append(desc)
                if details:
                    text_parts.append("Details:\n- " + "\n- ".join(details))

                chunks.append({
                    "id": f"{race_id}_battle_{len(chunks)}",
                    "text": "\n\n".join(text_parts),
                    "metadata": {**base_metadata, "category": "battle"}
                })

    # UNITS chunks
    units_file = race_dir / "units.json"
    if units_file.exists():
        with open(units_file, 'r', encoding='utf-8') as f:
            units = json.load(f)

        for unit_name, unit_data in units.get("roster_info", {}).items():
            desc = unit_data.get("description", "")
            unit_types = unit_data.get("unit_types", [])

            if desc or unit_types:
                text_parts = [f"Unit Roster: {unit_name}"]
                if desc:
                    text_parts.append(desc)
                if unit_types:
                    text_parts.append("Unit Types:\n- " + "\n- ".join(unit_types))

                chunks.append({
                    "id": f"{race_id}_units_{len(chunks)}",
                    "text": "\n\n".join(text_parts),
                    "metadata": {**base_metadata, "category": "units"}
                })

    # LORDS/FACTIONS chunk
    lords_file = race_dir / "lords.json"
    if lords_file.exists():
        with open(lords_file, 'r', encoding='utf-8') as f:
            lords = json.load(f)

        factions = lords.get("factions", [])
        if factions:
            text = f"Playable Factions for {meta.get('name', race_id)}:\n\n"
            text += "\n".join(f"- {faction}" for faction in factions if faction.strip())

            if text.strip():
                chunks.append({
                    "id": f"{race_id}_factions",
                    "text": text,
                    "metadata": {**base_metadata, "category": "factions"}
                })

    return chunks

def main():
    print("="*70)
    print("PREPARING DATA FOR CHROMADB")
    print("Optimized for HuggingFace all-MiniLM-L6-v2 embeddings")
    print("="*70)

    races_dir = Path("races")

    if not races_dir.exists():
        print("ERROR: races/ directory not found!")
        return

    all_chunks = []

    for race_dir in sorted(races_dir.iterdir()):
        if not race_dir.is_dir():
            continue

        print(f"\nProcessing: {race_dir.name}")
        chunks = create_chunks_from_race(race_dir)
        all_chunks.extend(chunks)
        print(f"  Created {len(chunks)} chunks")

    # Save chunks
    output_file = Path("rag_chunks.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print(f"SUCCESS! Created {len(all_chunks)} chunks total")
    print(f"Saved to: {output_file}")
    print("="*70)
    print("\nNext steps:")
    print("1. Load this file into ChromaDB")
    print("2. Use metadata filters for race/category/faction_type")
    print("3. HuggingFace all-MiniLM-L6-v2 will create embeddings")

if __name__ == "__main__":
    main()
