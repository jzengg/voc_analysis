from typing import List, Tuple, Dict

from enum import Enum

from voc.constants import pp
from voc.utils import (
    get_background_color_from_style,
    split_english_and_chinese_name,
    save_as_json,
    gen_all_season_data,
    get_contestant_id,
)


class RankCategory(int, Enum):
    WINNER = 0
    RUNNER_UP = 1
    THIRD_PLACE = 2
    FOURTH_PLACE = 3
    FIFTH_PLACE = 4
    SIXTH_PLACE = 5
    ELIMINATED_IN_PLAYOFFS_ROUND_2 = 6
    ELIMINATED_IN_PLAYOFFS_ROUND_1 = 7
    ELIMINATED_IN_KNOCKOUTS_ROUND_2 = 8
    ELIMINATED_IN_KNOCKOUTS_ROUND_1 = 9
    ELIMINATED_IN_BATTLES = 10
    NOT_CHOSEN = 11
    STOLEN_BY_ANOTHER_COACH = 12
    WITHDREW = 12


COLOR_TO_RANK = {
    "#fff44f": RankCategory.WINNER,
    "yellow": RankCategory.WINNER,
    "#b0e0e6": RankCategory.RUNNER_UP,
    "#b2ec5d": RankCategory.THIRD_PLACE,
    "#fbceb1": RankCategory.FOURTH_PLACE,
    "#e0e8ff": RankCategory.FIFTH_PLACE,
    "#dda0dd": RankCategory.SIXTH_PLACE,
    "plum": RankCategory.SIXTH_PLACE,
    "#e8ccd7": RankCategory.ELIMINATED_IN_PLAYOFFS_ROUND_2,
    "#ff9999": RankCategory.ELIMINATED_IN_PLAYOFFS_ROUND_1,
    "#f99": RankCategory.ELIMINATED_IN_PLAYOFFS_ROUND_1,
    "#ffbf8c": RankCategory.ELIMINATED_IN_KNOCKOUTS_ROUND_2,
    "#a8e4a0": RankCategory.ELIMINATED_IN_KNOCKOUTS_ROUND_1,
    # this color is also reused for eliminated during blind auditions?
    "#fdfd96": RankCategory.ELIMINATED_IN_BATTLES,
    "#fffdd0": RankCategory.STOLEN_BY_ANOTHER_COACH,
    "silver": RankCategory.WITHDREW,
}


def get_rank_from_style(styles: str) -> RankCategory:
    color = get_background_color_from_style(styles)
    rank = COLOR_TO_RANK[color]
    return rank


def get_season_results(season_soup, season_num) -> Tuple[List[Dict], List[str], Dict]:
    results_summary_table = season_soup.find_all("table", class_="wikitable")[0]
    rows = results_summary_table.find_all("tr")
    # skip table header
    rows = rows[1:]
    # coaches can have differing number of contestant rows so inspect the number of rows they take up first
    coach_row_spans = [
        int(tag.attrs.get("rowspan"))
        for tag in results_summary_table.find_all("th")
        if tag.attrs.get("rowspan")
    ]
    coach_chunks = []
    for chunk_size in coach_row_spans:
        coach_chunks.append(rows[:chunk_size])
        rows = rows[chunk_size:]

    coach_results = []
    contestant_id_to_results = {}
    coach_names = []

    for chunk in coach_chunks:
        coach_cell, *contestant_rows = chunk
        # not a real coach row, may be a footnote
        if not coach_cell.a:
            continue
        coach_name = coach_cell.a.string.strip()
        if coach_name not in coach_names:
            coach_names.append(coach_name)
        for row in contestant_rows:
            row_style = row.attrs.get("style", "")
            for cell in row.find_all("td"):
                try:
                    if "background" in row_style:
                        style = row_style
                    else:
                        style = cell.attrs.get("style")
                    result_raw = {
                        "style": style,
                        "content": next(cell.stripped_strings),
                    }
                # empty cell
                except StopIteration:
                    continue
                except Exception as e:
                    raise e
                rank = get_rank_from_style(result_raw["style"])
                # don't double count contestants that were stolen
                if rank == RankCategory.STOLEN_BY_ANOTHER_COACH:
                    continue
                if cell.a:
                    name_data = split_english_and_chinese_name(" ".join([s for s in cell.stripped_strings]))
                else:
                    name_data = split_english_and_chinese_name(result_raw["content"])
                result = {
                    "rank_category_value": rank,
                    "rank_category_name": RankCategory(rank).name,
                    **name_data,
                    "coach_name": coach_name,
                }
                contestant_id = get_contestant_id(
                    {**name_data, "season_num": season_num}
                )
                contestant_id_to_results[contestant_id] = result
                coach_results.append(result)
    return coach_results, coach_names, contestant_id_to_results


def get_overall_results_data():
    season_results = []
    for season_data in gen_all_season_data():
        season_soup = season_data["season_soup"]
        season_num = season_data["season_num"]
        season_url = season_data["season_url"]
        contestants, coaches, contestant_id_to_results = get_season_results(
            season_soup, season_num
        )
        season_results.append(
            {
                "contestant_overall_results": contestants,
                "contestant_id_to_results": contestant_id_to_results,
                "season_url": season_url,
                "season_num": season_num,
                "coaches": coaches,
            }
        )
    return season_results


if __name__ == "__main__":
    data = get_overall_results_data()
    pp.pprint(data)
    save_as_json(data, "season_overall_results")
