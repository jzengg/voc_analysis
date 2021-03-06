import re

from voc.coaches import get_coach_data
from voc.constants import (
    pp,
)
from voc.utils import (
    get_background_color_from_style,
    process_table_row_spans,
    split_english_and_chinese_name,
    save_as_json,
    gen_all_season_data,
    get_contestant_id,
)

INVALID_NAME_COMPONENTS = [","]
COACH_AND_CONTESTANT_CHOICE_SELECTED_COLORS = ["#ffc40c", "#fdfc8f"]


def parse_unstructured_name_cell(cell):
    english_name_raw = next(child for child in cell.stripped_strings)
    # group names will have a ul
    if cell.ul:
        # handle groups with no chinese name
        english_name_raw = english_name_raw.replace(":", "")
        name_data = split_english_and_chinese_name(english_name_raw)
        english_name_raw = name_data["english_name"]
        # hack for this group which doesn't have chinese name in blind auditions but does in overall results
        if english_name_raw == "Jia Ning Group":
            chinese_name_raw = "佳宁组合"
        else:
            chinese_name_raw = name_data["chinese_name"]
    elif cell.span:
        chinese_name_raw = cell.span.string.strip()
    else:
        english_name_raw, chinese_name_raw = english_name_raw.split("(")
    english_name = english_name_raw.split("(")[0].strip()
    # hack for this group who's listed under a different name between the sections
    if english_name == "Shanye":
        english_name = "Li Haohan"
        chinese_name = "李昊瀚"
    else:
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
    if cell.sup:
        name_raw = next(cell.stripped_strings)
    elif cell.a:
        english_name_raw = next(cell.a.stripped_strings)
        chinese_name_raw = cell.a.next_sibling.string
        name_raw = f"{english_name_raw} {chinese_name_raw}"
    else:
        name_raw = next(cell.stripped_strings)
    name_data = split_english_and_chinese_name(name_raw)
    # name is different between sections
    # season 2
    if name_data["english_name"] == "Zhang Mu":
        name_data["chinese_name"] = "張目"
    # season 2
    if name_data["english_name"] == "Zhang Jiaming":
        name_data["chinese_name"] = "張珈銘"
    # season 8
    if name_data["chinese_name"] == "贾峥":
        name_data["chinese_name"] = "贾铮"
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


def parse_season_1_coach_and_contestant_choice_cells(cells, season_coaches):
    coach_choices = [
        {"coach_turned": bool(cell.a), "coach_name": season_coaches[index]}
        for index, cell in enumerate(cells)
    ]
    selected_coach = next(
        (
            season_coaches[index]
            for index, cell in enumerate(cells)
            if get_background_color_from_style(cell.attrs.get("style"))
            in COACH_AND_CONTESTANT_CHOICE_SELECTED_COLORS
        ),
        None,
    )
    return {"coach_choices": coach_choices, "selected_coach": selected_coach}


def parse_coach_and_contestant_choice_cells(cells, season_coaches):
    coach_choices = [
        {
            "coach_turned": next(cell.stripped_strings, "—") == "✔",
            "coach_name": season_coaches[index],
        }
        for index, cell in enumerate(cells)
    ]
    selected_coach = next(
        (
            season_coaches[index]
            for index, cell in enumerate(cells)
            if get_background_color_from_style(cell.attrs.get("style"))
            in COACH_AND_CONTESTANT_CHOICE_SELECTED_COLORS
        ),
        None,
    )
    return {"coach_choices": coach_choices, "selected_coach": selected_coach}


# season 1 combines data in name cell but it's broken out into dedicated columns in later seasons (age, hometown).
def parse_unstructured_contestant_row(contestant_row, season_coaches):
    name_cell, song_cell, *coach_choices = contestant_row
    name_cell_data = parse_unstructured_name_cell(name_cell)
    song_cell_data = parse_unstructured_song_cell(song_cell)
    coach_and_contestant_choice_cell_data = (
        parse_season_1_coach_and_contestant_choice_cells(coach_choices, season_coaches)
    )
    contestant_row_data = {
        **name_cell_data,
        **song_cell_data,
        **coach_and_contestant_choice_cell_data,
    }
    return contestant_row_data


def parse_structured_contestant_row(contestant_row, season_coaches):
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
        [coach_1, coach_2, coach_3, coach_4], season_coaches
    )
    contestant_row_data = {
        **age_cell_data,
        **location_cell_data,
        **name_cell_data,
        **song_cell_data,
        **coach_and_contestant_choice_cell_data,
    }
    return contestant_row_data


def get_season_results(season_soup, season_coaches, season_num):
    tables = season_soup.find_all("table", class_="wikitable")
    audition_results_tables = [
        table
        for table in tables
        if "Coach's and contestant's choices"
        in [s for s in table.tbody.tr.stripped_strings]
        or "Coach's and artist's choices"
        in [s for s in table.tbody.tr.stripped_strings]
    ]

    results = []
    contestant_id_to_results = {}
    for table in audition_results_tables:
        processed_table = process_table_row_spans(table, season_soup)
        for contestant_row in processed_table[1:]:
            if not contestant_row:
                continue
            if len(contestant_row) >= 8:
                contestant_row_data = parse_structured_contestant_row(
                    contestant_row, season_coaches
                )
            else:
                contestant_row_data = parse_unstructured_contestant_row(
                    contestant_row, season_coaches
                )
            name_data = {
                "english_name": contestant_row_data["english_name"],
                "chinese_name": contestant_row_data["chinese_name"],
                "season_num": season_num,
            }
            contestant_id = get_contestant_id(name_data)
            contestant_id_to_results[contestant_id] = contestant_row_data
            results.append(contestant_row_data)
    return results, contestant_id_to_results


def get_contestant_id_to_blind_auditions_data():
    coach_data = get_coach_data()
    contestant_id_to_blind_auditions_data = {}
    for season_data in gen_all_season_data():
        season_soup = season_data["season_soup"]
        season_num = season_data["season_num"]
        season_coaches = coach_data["season_num_to_coaches"][season_num]
        _, season_contestant_id_to_blind_auditions_data = get_season_results(
            season_soup, season_coaches, season_num
        )
        contestant_id_to_blind_auditions_data = {
            **contestant_id_to_blind_auditions_data,
            **season_contestant_id_to_blind_auditions_data,
        }
    return contestant_id_to_blind_auditions_data


def get_blind_auditions_data():
    season_results = []
    coach_data = get_coach_data()
    for season_data in gen_all_season_data():
        season_soup = season_data["season_soup"]
        season_num = season_data["season_num"]
        season_url = season_data["season_url"]
        season_coaches = coach_data["season_num_to_coaches"][season_num]
        results, _ = get_season_results(season_soup, season_coaches, season_num)
        season_results.append(
            {
                "blind_auditions_results": results,
                "season_url": season_url,
                "season_num": season_num,
                "coaches": season_coaches,
            }
        )
    return season_results


if __name__ == "__main__":
    data = get_blind_auditions_data()
    save_as_json(data, "blind_auditions")
    pp.pprint(data)
