"""
MediaWiki Markup Parser for Total War Warhammer III
Parses raw wiki markup into structured JSON for RAG
"""

import re
import json
from pathlib import Path

def extract_text_from_tables(text):
    """
    Extract text content from MediaWiki tables {| ... |}
    Returns text with table content extracted
    """
    if not text:
        return ""

    def extract_table_text(match):
        table_content = match.group(1)
        extracted = []

        # Split by table rows (|-)
        rows = table_content.split('|-')

        for row in rows:
            # Remove table cell markers (| or !)
            lines = row.split('\n')
            for line in lines:
                # Remove leading | or !
                line = re.sub(r'^[\|!]+', '', line.strip())
                # Skip empty lines or style definitions
                if line and not line.startswith('class=') and not line.startswith('style=') and not line.startswith('colspan='):
                    extracted.append(line)

        return ' '.join(extracted)

    # Extract text from tables
    text = re.sub(r'\{\|(.*?)\|\}', extract_table_text, text, flags=re.DOTALL)

    return text

def clean_wiki_markup(text):
    """
    Remove wiki markup and clean text
    """
    if not text:
        return ""

    # First extract text from tables before cleaning
    text = extract_text_from_tables(text)

    # Remove file/image references
    text = re.sub(r'\[\[File:.*?\]\]', '', text)
    text = re.sub(r'\[\[Image:.*?\]\]', '', text)

    # Remove internal wiki links but keep text: [[Link|Text]] -> Text or [[Link]] -> Link
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)

    # Remove external links
    text = re.sub(r'\[http[^\]]+\]', '', text)

    # Remove bold/italic
    text = re.sub(r"'''", '', text)
    text = re.sub(r"''", '', text)

    # Remove HTML tags
    text = re.sub(r'<br\s*/?>', ' ', text)
    text = re.sub(r'<[^>]+>', '', text)

    # Remove {{template}} but keep {{Main|text}} content
    text = re.sub(r'\{\{Main\|([^\}]+)\}\}', r'\1', text)

    # Extract faction names from {{The X faction}} templates
    # {{The Northern Provinces faction}} -> "The Northern Provinces"
    text = re.sub(r'\{\{The ([^\}]+?) faction\}\}', r'The \1', text)

    # Remove remaining templates
    text = re.sub(r'\{\{[^\}]+\}\}', '', text)

    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def extract_infobox(content):
    """
    Extract data from {{Infobox}} template
    """
    infobox_match = re.search(r'\{\{Infobox[^}]*\n(.*?)\n\}\}', content, re.DOTALL)

    if not infobox_match:
        return {}

    infobox_content = infobox_match.group(1)
    data = {}

    # Extract key-value pairs
    for line in infobox_content.split('\n'):
        match = re.match(r'\|(\w+)\s*=\s*(.+)', line)
        if match:
            key = match.group(1).strip()
            value = clean_wiki_markup(match.group(2).strip())
            if value:
                data[key] = value

    return data

def extract_sections(content):
    """
    Extract wiki sections (== Section ==)
    """
    sections = {}
    current_section = None
    current_content = []

    for line in content.split('\n'):
        # Check for section headers
        section_match = re.match(r'^==+\s*(.+?)\s*==+', line)

        if section_match:
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()

            # Start new section
            current_section = section_match.group(1).strip()
            current_content = []
        elif current_section:
            current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections

def extract_list_items(text):
    """
    Extract bullet point lists from wiki markup
    """
    items = []
    for line in text.split('\n'):
        if line.strip().startswith('*'):
            item = clean_wiki_markup(line.strip()[1:].strip())
            if item:
                items.append(item)
    return items

def parse_race_page(raw_content, race_name):
    """
    Parse a race wiki page into structured data
    """
    # Extract infobox
    infobox = extract_infobox(raw_content)

    # Extract sections
    sections = extract_sections(raw_content)

    # Build structured data
    race_data = {
        "race_id": race_name.lower().replace(' ', '_'),
        "name": race_name.replace('_', ' '),
        "infobox": infobox,
        "sections": {}
    }

    # Parse specific sections
    for section_name, section_content in sections.items():
        cleaned_content = clean_wiki_markup(section_content)

        # Extract lists if present
        list_items = extract_list_items(section_content)

        race_data["sections"][section_name] = {
            "content": cleaned_content,
            "list_items": list_items if list_items else None
        }

    return race_data

def main():
    """
    Parse all raw wiki data
    """
    print("Starting MediaWiki Parser")

    raw_data_dir = Path("scripts/raw_data")
    output_dir = Path("scripts/parsed_data")
    output_dir.mkdir(exist_ok=True)

    if not raw_data_dir.exists():
        print("No raw data found. Run wiki_scraper.py first.")
        return

    for raw_file in raw_data_dir.glob("*.txt"):
        print(f"Parsing: {raw_file.name}...")

        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        race_name = raw_file.stem.replace('_', ' ').title()
        parsed_data = parse_race_page(raw_content, race_name)

        # Save parsed data
        output_file = output_dir / f"{raw_file.stem}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)

        print(f"Saved: {output_file}")

    print(f"\nParsing complete!")
    print(f"Parsed data saved in: {output_dir}/")

if __name__ == "__main__":
    main()
