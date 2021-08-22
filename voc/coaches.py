import requests

from bs4 import BeautifulSoup

from voc.constants import pp, ALL_SEASON_URLS
from voc.utils import (
    save_as_json,
)


def get_coach_data():
    season_urls = [*ALL_SEASON_URLS]
    all_coaches = set()
    season_to_coaches = {}
    for season_index, season_url in enumerate(season_urls):
        season_response = requests.get(
            url=season_url,
        )
        season_soup = BeautifulSoup(season_response.content, "html.parser")
        results_summary_table = season_soup.find_all("table", class_="wikitable")[0]
        coaches = [
            next(tag.stripped_strings)
            for tag in results_summary_table.find_all("th")
            if tag.attrs.get("rowspan")
        ]
        human_season = season_index + 1
        all_coaches |= set(coaches)
        season_to_coaches[human_season] = coaches
    sorted_coaches = sorted(list(all_coaches))
    coach_data = {"all_coaches": sorted_coaches, "season_to_coaches": season_to_coaches}
    return coach_data


if __name__ == "__main__":
    coach_data = get_coach_data()
    pp.pprint(coach_data)
    save_as_json(coach_data, "coaches")
