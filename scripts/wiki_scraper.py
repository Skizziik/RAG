"""
Fandom Wiki Scraper for Total War Warhammer III
Scrapes race data from the official Total War Warhammer wiki
"""

import requests
import json
import os
from pathlib import Path

# Base game races (without DLC)
BASE_GAME_RACES = [
    "Grand_Cathay",
    "Kislev",
    "Khorne",
    "Tzeentch",
    "Nurgle",
    "Slaanesh",
    "Daemons_of_Chaos",
    "Ogre_Kingdoms"
]

WIKI_API_URL = "https://totalwarwarhammer.fandom.com/api.php"

def fetch_wiki_page(page_title):
    """
    Fetch wiki page content using MediaWiki API
    """
    params = {
        'action': 'query',
        'titles': page_title,
        'prop': 'revisions',
        'rvprop': 'content',
        'rvslots': 'main',
        'format': 'json'
    }

    try:
        response = requests.get(WIKI_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract page content
        pages = data.get('query', {}).get('pages', {})
        page_id = list(pages.keys())[0]

        if page_id == '-1':
            print(f"Page not found: {page_title}")
            return None

        content = pages[page_id].get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('*', '')
        return content

    except Exception as e:
        print(f"Error fetching {page_title}: {e}")
        return None

def save_raw_data(race_name, content):
    """
    Save raw wiki markup to file
    """
    output_dir = Path("scripts/raw_data")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"{race_name.lower()}.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Saved: {output_file}")

def main():
    """
    Main scraper function
    """
    print("Starting Total War Warhammer III Wiki Scraper")
    print(f"Scraping {len(BASE_GAME_RACES)} base game races\n")

    for race in BASE_GAME_RACES:
        print(f"Fetching: {race}...")
        content = fetch_wiki_page(race)

        if content:
            save_raw_data(race, content)
        else:
            print(f"Skipped: {race}\n")

    print("\nScraping complete!")
    print(f"Raw data saved in: scripts/raw_data/")

if __name__ == "__main__":
    main()
