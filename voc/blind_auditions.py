import requests
import re
from bs4 import BeautifulSoup

from voc.constants import pp

INVALID_NAME_COMPONENTS = [","]


def parse_name_cell(cell):
    english_name_raw = next(child for child in cell.stripped_strings)
    if cell.span:
        chinese_name_raw = cell.span.string.strip()
    else:
        english_name_raw, chinese_name_raw = english_name_raw.split("(")
    english_name = english_name_raw.split("(")[0].strip()
    chinese_name = chinese_name_raw.replace(")", "").strip()
    age_location_raw = cell.sub
    age_location_components = [c for c in age_location_raw.stripped_strings]
    age_raw, *location_raw = age_location_components
    age = age_raw.split(",")[0]
    age = int(re.sub(r"[^0-9]", "", age))
    location = ", ".join(
        [
            component
            for component in location_raw
            if component not in INVALID_NAME_COMPONENTS
        ]
    )
    return {
        "age": age,
        "location": location,
        "english_name": english_name,
        "chinese_name": chinese_name,
    }


def parse_song_cell(cell):
    song_title_tag = cell.span or cell.a
    song_title = song_title_tag.string.strip()
    song_author = (
        [s for s in cell.sub.stripped_strings][-1].split("originally by")[-1].strip()
    )
    return {"song_author": song_author, "song_title": song_title}


if __name__ == "__main__":
    season_1_response = requests.get(
        url="https://en.wikipedia.org/wiki/The_Voice_of_China_(season_1)",
    )
    season_1_soup = BeautifulSoup(season_1_response.content, "html.parser")
    audition_results_tables = season_1_soup.find_all("table", class_="wikitable")[1:7]
    judges = [
        s for s in audition_results_tables[0].tbody.find_all("tr")[1].stripped_strings
    ]
    for table in audition_results_tables:
        episode_results = table.tbody.find_all("tr")[2:]
        for episode in episode_results:
            contestant_row = episode.find_all("td")
            if not contestant_row:
                continue
            name_cell, song_cell, *coach_choices = contestant_row
            name_cell_data = parse_name_cell(name_cell)
            song_cell_data = parse_song_cell(song_cell)
            pp.pprint(name_cell_data)
            pp.pprint(song_cell_data)
