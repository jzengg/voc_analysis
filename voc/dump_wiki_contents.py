import requests

from voc.constants import ALL_SEASON_URLS
from voc.utils import save_as_json


def dump_all_season_html():
    season_urls = [*ALL_SEASON_URLS]
    all_data = []
    for season_index, season_url in enumerate(season_urls):
        season_response = requests.get(
            url=season_url,
        )
        season_num = season_index + 1
        season_data = {
            "season_num": season_num,
            "season_content": season_response.text,
            "season_url": season_url,
        }
        all_data.append(season_data)
    return all_data


if __name__ == "__main__":
    all_data = dump_all_season_html()
    save_as_json(all_data, "wiki_dump")
