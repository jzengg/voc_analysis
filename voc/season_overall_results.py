import requests
import pprint
import itertools
from typing import List, Tuple, Dict

from bs4 import BeautifulSoup
from enum import Enum

pp = pprint.PrettyPrinter(indent=4)


class RankCategory(Enum):
    WINNER = 0
    RUNNER_UP = 1
    THIRD_PLACE = 2
    FOURTH_PLACE = 3
    ELIMINATED_IN_PLAYOFFS_ROUND_2 = 4
    ELIMINATED_IN_PLAYOFFS_ROUND_1 = 5
    ELIMINATED_IN_KNOCKOUTS = 6
    ELIMINATED_IN_BATTLES = 7
    NOT_CHOSEN = 8


COLOR_TO_RANK = {
    "#FFF44F": RankCategory.WINNER,
    "#B0E0E6": RankCategory.RUNNER_UP,
    "#B2EC5D": RankCategory.THIRD_PLACE,
    "#FBCEB1": RankCategory.FOURTH_PLACE,
    "#E8CCD7": RankCategory.ELIMINATED_IN_PLAYOFFS_ROUND_2,
    "FF9999": RankCategory.ELIMINATED_IN_PLAYOFFS_ROUND_1,
    "#A8E4A0": RankCategory.ELIMINATED_IN_KNOCKOUTS,
    "#FDFD96": RankCategory.ELIMINATED_IN_BATTLES,
}


def get_background_color_from_style(styles: str) -> str:
    return (
        next(
            style
            for style in styles.split(";")
            if "background-color" in style or "background" in style
        )
        .split(":")[1]
        .strip()
    )


def get_rank_from_style(styles: str) -> RankCategory:
    color = get_background_color_from_style(styles)
    rank = COLOR_TO_RANK[color]
    return rank


def get_season_results(season_soup) -> Tuple[List[Dict], List[str]]:
    results_summary_table = season_soup.find_all("table", class_="wikitable")[0]
    rows = results_summary_table.find_all("tr")
    judge_chunks = [rows[i : i + 3] for i in range(1, len(rows), 3)]
    judge_results = []
    judge_names = []

    for chunk in judge_chunks:
        judge_cell, contestant_cells_0, contestant_cells_1 = chunk
        judge_name = judge_cell.a.string.strip()
        if judge_name not in judge_names:
            judge_names.append(judge_name)
        contestant_cells = [
            *contestant_cells_0.find_all("td"),
            *contestant_cells_1.find_all("td"),
        ]
        results_raw = [
            {"style": cell.attrs["style"], "content": next(cell.stripped_strings)}
            for cell in contestant_cells
        ]
        results = [
            {
                "rank_category": get_rank_from_style(result["style"]),
                "name": result["content"],
                "judge_name": judge_name,
                "season": 1,
            }
            for result in results_raw
        ]
        judge_results.append(results)
    return list(itertools.chain.from_iterable(judge_results)), judge_names


if __name__ == "__main__":
    season_1_response = requests.get(
        url="https://en.wikipedia.org/wiki/The_Voice_of_China_(season_1)",
    )
    season_1_soup = BeautifulSoup(season_1_response.content, "html.parser")
    season_1_contestants, season_1_judges = get_season_results(season_1_soup)
    pp.pprint(season_1_contestants)
    pp.pprint(season_1_judges)
