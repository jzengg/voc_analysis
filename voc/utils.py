import json
import re

import requests
from bs4 import BeautifulSoup

from voc.constants import ALL_SEASON_URLS


def get_background_color_from_style(styles: str) -> str:
    if not styles:
        return ""
    attr = next(
        (
            style
            for style in styles.split(";")
            if "background-color" in style or "background" in style
        ),
        None,
    )
    if not attr:
        return ""
    color = attr.split(":")[1].strip().lower()
    return color


# handle row spans in the table by inserting additional <td> as specified by rowspans
def process_table_row_spans(table, bs):
    tmp = table.find_all("tr")
    all_rows = tmp[1:]
    results = [[data for data in row.find_all("td")] for row in all_rows]
    # <td rowspan="2">2=</td>
    # list of tuple (Level of tr, Level of td, total Count, Text Value)
    # e.g.
    # [(1, 0, 2, u'2=')]
    # (<tr> is 1 , td sequence in tr is 0, reapted 2 times , value is 2=)
    for row_index, row in enumerate(results):
        for td_index in range(len(row)):
            td = row[td_index]
            if "rowspan" in td.attrs:
                num_rows = int(td["rowspan"])
                # tr value of rowspan in present in 1th place in results
                for i in range(1, num_rows):
                    # - Add value in next tr.
                    new_td = bs.new_tag("td")
                    results[row_index + i].insert(td_index, new_td)
    return results


def split_english_and_chinese_name(name_raw):
    *english_name_parts, chinese_name = re.split(r"\W+", name_raw)
    english_name = " ".join(english_name_parts)
    return {"english_name": english_name, "chinese_name": chinese_name}


def save_as_json(data, filename):
    with open(f"../data/{filename}.json", "w", encoding="utf8") as f:
        json.dump(data, f, indent=4, sort_keys=True, ensure_ascii=False)


def gen_all_season_data():
    # func = gen_all_season_data_live
    func = gen_all_season_data_offline
    return func()


def gen_all_season_data_live():
    season_urls = [*ALL_SEASON_URLS]
    for season_index, season_url in enumerate(season_urls):
        season_response = requests.get(
            url=season_url,
        )
        season_soup = BeautifulSoup(season_response.content, "html.parser")
        yield {
            "season_num": season_index + 1,
            "season_soup": season_soup,
            "season_url": season_url,
        }


def gen_all_season_data_offline():
    with open("../data/wiki_dump.json") as f:
        wiki_dump = json.load(f)
        for season_data in wiki_dump:
            season_content = season_data["season_content"]
            season_soup = BeautifulSoup(season_content, "html.parser")
            season_num = season_data["season_num"]
            season_url = season_data["season_url"]
            yield {
                "season_num": season_num,
                "season_soup": season_soup,
                "season_url": season_url,
            }
