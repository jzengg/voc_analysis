import requests
import re
from bs4 import BeautifulSoup

from voc.constants import (
    pp,
    ALL_SEASON_URLS,
)
from voc.utils import (
    get_background_color_from_style,
    process_table_row_spans,
    split_english_and_chinese_name,
    save_as_json,
)

INVALID_NAME_COMPONENTS = [","]
COACH_AND_CONTESTANT_CHOICE_SELECTED_COLORS = ["#ffc40c", "#fdfc8f"]


def parse_unstructured_name_cell(cell):
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


def parse_name_cell(cell):
    tag = cell.a or cell
    name_raw = next(tag.stripped_strings)
    name_data = split_english_and_chinese_name(name_raw)
    return name_data


def parse_age_cell(cell):
    age_raw = cell.string.strip()
    if not age_raw:
        return {"age": None}
    age_components = age_raw.split("/")
    try:
        age = int(age_components[0])
    except Exception as e:
        print(e)
        print(cell)
        age = None
    return {"age": age}


def parse_unstructured_song_cell(cell):
    text_not_in_span = cell.contents[0]
    text_not_in_span = text_not_in_span.strip()
    text_not_in_span = text_not_in_span.replace('"', "")
    text_not_in_span = text_not_in_span.replace("'", "")
    if text_not_in_span:
        song_title = text_not_in_span
    else:
        song_title_tag = cell.span or cell.a
        song_title = song_title_tag.string.strip()
    song_title = song_title.replace('"', "")
    song_title = song_title.replace("'", "")
    return {"song_title": song_title}


def parse_song_cell(cell):
    song_title_tag = cell.a or cell.span or cell
    song_title = song_title_tag.string.strip()
    song_title = song_title.replace('"', "")
    song_title = song_title.replace("'", "")
    return {"song_title": song_title}


def parse_location_cell(cell):
    try:
        location = next(cell.stripped_strings)
    except StopIteration:
        location = None
        print("no location found", cell)
    except Exception as e:
        raise e
    return {"location": location}


def parse_season_1_coach_and_contestant_choice_cells(cells):
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


def parse_coach_and_contestant_choice_cells(cells):
    judge_choices = [next(cell.stripped_strings, "—") == "✔" for cell in cells]
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


# season 1 combines data in name cell but it's broken out into dedicated columns in later seasons (age, hometown).
def parse_unstructured_contestant_row(contestant_row):
    name_cell, song_cell, *coach_choices = contestant_row
    name_cell_data = parse_unstructured_name_cell(name_cell)
    song_cell_data = parse_unstructured_song_cell(song_cell)
    coach_and_contestant_choice_cell_data = (
        parse_season_1_coach_and_contestant_choice_cells(coach_choices)
    )
    contestant_row_data = {
        **name_cell_data,
        **song_cell_data,
        **coach_and_contestant_choice_cell_data,
    }
    return contestant_row_data


def parse_structured_contestant_row(contestant_row):
    (
        name_cell,
        age_cell,
        hometown_cell,
        song_cell,
        coach_1,
        coach_2,
        coach_3,
        coach_4,
        *_,
    ) = contestant_row
    name_cell_data = parse_name_cell(name_cell)
    age_cell_data = parse_age_cell(age_cell)
    song_cell_data = parse_song_cell(song_cell)
    location_cell_data = parse_location_cell(hometown_cell)
    coach_and_contestant_choice_cell_data = parse_coach_and_contestant_choice_cells(
        [coach_1, coach_2, coach_3, coach_4]
    )
    contestant_row_data = {
        **age_cell_data,
        **location_cell_data,
        **name_cell_data,
        **song_cell_data,
        **coach_and_contestant_choice_cell_data,
    }
    return contestant_row_data


def get_season_results(season_soup):
    tables = season_soup.find_all("table", class_="wikitable")
    audition_results_tables = [
        table
        for table in tables
        if "Coach's and contestant's choices"
        in [s for s in table.tbody.tr.stripped_strings]
        or "Coach's and artist's choices"
        in [s for s in table.tbody.tr.stripped_strings]
    ]

    judges = [
        s for s in audition_results_tables[0].tbody.find_all("tr")[1].stripped_strings
    ]
    results = []
    for table in audition_results_tables:
        processed_table = process_table_row_spans(table, season_soup)
        for contestant_row in processed_table[1:]:
            if not contestant_row:
                continue
            if len(contestant_row) >= 8:
                contestant_row_data = parse_structured_contestant_row(contestant_row)
            else:
                contestant_row_data = parse_unstructured_contestant_row(contestant_row)
            results.append(contestant_row_data)
    return results, judges


if __name__ == "__main__":
    season_urls = [*ALL_SEASON_URLS]
    season_results = []
    for season_url in season_urls:
        season_response = requests.get(
            url=season_url,
        )
        soup = BeautifulSoup(season_response.content, "html.parser")
        results, judges = get_season_results(soup)
        season_results.append(
            {"results": results, "wiki_url": season_url, "judges": judges}
        )

    save_as_json(season_results, "blind_auditions")
    pp.pprint(season_results)
