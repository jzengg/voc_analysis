from voc.constants import pp
from voc.utils import (
    save_as_json, gen_all_season_num_and_soup,
)


def get_coach_data():
    all_coaches = set()
    season_to_coaches = {}
    for season_num, season_soup in gen_all_season_num_and_soup():
        results_summary_table = season_soup.find_all("table", class_="wikitable")[0]
        coaches = [
            next(tag.stripped_strings)
            for tag in results_summary_table.find_all("th")
            if tag.attrs.get("rowspan")
        ]
        all_coaches |= set(coaches)
        season_to_coaches[season_num] = coaches
    sorted_coaches = sorted(list(all_coaches))
    coach_data = {"all_coaches": sorted_coaches, "season_to_coaches": season_to_coaches}
    return coach_data


if __name__ == "__main__":
    coach_data = get_coach_data()
    pp.pprint(coach_data)
    save_as_json(coach_data, "coaches")
