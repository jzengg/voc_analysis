from voc.blind_auditions import get_blind_auditions_data
from voc.coaches import get_coach_data
from voc.constants import (
    pp,
)
from voc.season_overall_results import get_overall_results_data
from voc.utils import save_as_json


def join_all_data():
    overalL_results_data = get_overall_results_data()
    blind_auditions_data = get_blind_auditions_data()
    coach_data = get_coach_data()
    seasons_data = []
    for (season_overall_results_data, season_blind_auditions_data) in zip(overalL_results_data, blind_auditions_data):
        joined_data = {**season_overall_results_data, **season_blind_auditions_data}
        seasons_data.append(joined_data)
    joined_data = {'seasons_data': seasons_data, 'coaches_data': coach_data}
    return joined_data


if __name__ == "__main__":
    all_data = join_all_data()
    pp.pprint(all_data)
    save_as_json(all_data, "all_data")
