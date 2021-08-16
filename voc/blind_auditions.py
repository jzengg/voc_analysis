import requests
import re
from bs4 import BeautifulSoup

from voc.constants import pp, SEASON_1_URL
from voc.utils import get_background_color_from_style, process_table_row_spans

INVALID_NAME_COMPONENTS = [","]
COACH_AND_CONTESTANT_CHOICE_SELECTED_COLORS = ["#ffc40c", "#fdfc8f"]


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


def parse_coach_and_contestant_choice_cell(cells):
    judge_choices = [bool(cell.a) for cell in cells]
    selected_judge = next(
        (
            index
            for index, cell in enumerate(cells)
            if get_background_color_from_style(cell.attrs.get("style"))
            in COACH_AND_CONTESTANT_CHOICE_SELECTED_COLORS
        ),
        None,
    )
    return {"judge_choices": judge_choices, "selected_judge": selected_judge}


def get_season_results(season_soup):
    audition_results_tables = season_soup.find_all("table", class_="wikitable")[1:7]
    # judges = [
    #     s for s in audition_results_tables[0].tbody.find_all("tr")[1].stripped_strings
    # ]
    results = []
    for table in audition_results_tables:
        processed_table = process_table_row_spans(table, season_1_soup)
        for contestant_row in processed_table[1:]:
            if not contestant_row:
                continue
            # TODO rewrite parsers to handle season 1 vs season 2 format, by num cols?
            name_cell, song_cell, *coach_choices = contestant_row
            name_cell_data = parse_name_cell(name_cell)
            song_cell_data = parse_song_cell(song_cell)
            coach_and_contestant_choice_cell_data = (
                parse_coach_and_contestant_choice_cell(coach_choices)
            )
            contestant_row_data = {
                **name_cell_data,
                **song_cell_data,
                **coach_and_contestant_choice_cell_data,
            }
            results.append(contestant_row_data)
    return results


if __name__ == "__main__":
    season_1_response = requests.get(
        url=SEASON_1_URL,
    )
    season_1_soup = BeautifulSoup(season_1_response.content, "html.parser")
    results = get_season_results(season_1_soup)
    pp.pprint(results)
