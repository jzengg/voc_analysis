import json

import requests
from typing import List, Tuple, Dict

from bs4 import BeautifulSoup
from enum import Enum

from voc.constants import pp, ALL_SEASON_URLS
from voc.utils import get_background_color_from_style, split_english_and_chinese_name


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
    STOLEN_BY_ANOTHER_JUDGE = 12
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
    "#fffdd0": RankCategory.STOLEN_BY_ANOTHER_JUDGE,
    "silver": RankCategory.WITHDREW,
}


def get_rank_from_style(styles: str) -> RankCategory:
    color = get_background_color_from_style(styles)
    rank = COLOR_TO_RANK[color]
    return rank


def get_season_results(season_soup) -> Tuple[List[Dict], List[str]]:
    results_summary_table = season_soup.find_all("table", class_="wikitable")[0]
    rows = results_summary_table.find_all("tr")
    # skip table header
    rows = rows[1:]
    # judges can have differing number of contestant rows so inspect the number of rows they take up first
    judge_row_spans = [
        int(tag.attrs.get("rowspan"))
        for tag in results_summary_table.find_all("th")
        if tag.attrs.get("rowspan")
    ]
    judge_chunks = []
    for chunk_size in judge_row_spans:
        judge_chunks.append(rows[:chunk_size])
        rows = rows[chunk_size:]

    judge_results = []
    judge_names = []

    for chunk in judge_chunks:
        judge_cell, *contestant_rows = chunk
        # not a real judge row, may be a footnote
        if not judge_cell.a:
            continue
        judge_name = judge_cell.a.string.strip()
        if judge_name not in judge_names:
            judge_names.append(judge_name)
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
                if rank == RankCategory.STOLEN_BY_ANOTHER_JUDGE:
                    continue
                name_data = split_english_and_chinese_name(result_raw["content"])
                result = {
                    "rank_category_value": rank,
                    "rank_category_name": RankCategory(rank).name,
                    **name_data,
                    "judge_name": judge_name,
                }
                judge_results.append(result)
    return judge_results, judge_names


if __name__ == "__main__":
    season_urls = [*ALL_SEASON_URLS]
    season_results = []
    for season_url in season_urls:
        season_response = requests.get(
            url=season_url,
        )
        soup = BeautifulSoup(season_response.content, "html.parser")
        contestants, judges = get_season_results(soup)
        season_results.append(
            {"results": contestants, "wiki_url": season_url, "judges": judges}
        )
    with open("../data/season_overall_results.json", "w") as f:
        json.dump(season_results, f)
    pp.pprint(season_results)
