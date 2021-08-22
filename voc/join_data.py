from voc.blind_auditions import (
    get_blind_auditions_data,
    get_contestant_id_to_blind_auditions_data,
)
from voc.coaches import get_coach_data
from voc.constants import (
    pp,
)
from voc.season_overall_results import (
    get_overall_results_data,
    get_contestant_id_to_overall_results_data,
)
from voc.utils import save_as_json


def join_all_data():
    overall_results_data = get_overall_results_data()
    blind_auditions_data = get_blind_auditions_data()
    coach_data = get_coach_data()
    seasons_data = []
    for (season_overall_results_data, season_blind_auditions_data) in zip(
        overall_results_data, blind_auditions_data
    ):
        joined_data = {**season_overall_results_data, **season_blind_auditions_data}
        seasons_data.append(joined_data)
    joined_data = {"seasons_data": seasons_data, "coaches_data": coach_data}
    return joined_data


def join_contestant_id_data():
    contestant_id_to_blind_auditions_data = get_contestant_id_to_blind_auditions_data()
    contestant_id_to_overall_results_data = get_contestant_id_to_overall_results_data()
    contestant_id_to_all_data = {}
    for (
        contestant_id,
        blind_auditions_data,
    ) in contestant_id_to_blind_auditions_data.items():
        _, _, season_num_component = contestant_id.split("|")
        season_num = int(season_num_component.split(":")[1])
        if contestant_id not in contestant_id_to_all_data:
            contestant_id_to_all_data[contestant_id] = {}
            contestant_id_to_all_data[contestant_id]["blind_auditions_data"] = {}
            contestant_id_to_all_data[contestant_id]["season_overall_results"] = {}
            contestant_id_to_all_data[contestant_id]["season_num"] = season_num
        for attr_name in [
            "english_name",
            "chinese_name",
            "age",
            "location",
            "selected_coach",
        ]:
            contestant_id_to_all_data[contestant_id][attr_name] = blind_auditions_data[
                attr_name
            ]
        for attr_name in ["coach_choices", "song_title"]:
            contestant_id_to_all_data[contestant_id]["blind_auditions_data"][
                attr_name
            ] = blind_auditions_data[attr_name]
        pp.pprint(contestant_id_to_all_data[contestant_id])
    for (
        contestant_id,
        overall_results_data,
    ) in contestant_id_to_overall_results_data.items():
        if contestant_id not in contestant_id_to_all_data:
            print(
                f"don't have auditions data for {contestant_id} but do have overall data"
            )
            contestant_id_to_all_data[contestant_id] = {"season_overall_results": {}}
        for attr_name in ["rank_category_value", "rank_category_name"]:
            contestant_id_to_all_data[contestant_id]["season_overall_results"][
                attr_name
            ] = overall_results_data[attr_name]
    return contestant_id_to_all_data


if __name__ == "__main__":
    contestant_id_to_data = join_contestant_id_data()

    all_data = join_all_data()
    all_data["contestant_id_to_data"] = contestant_id_to_data
    pp.pprint(all_data)
    save_as_json(all_data, "all_data")
