# scrape colors from wiki page
# color_key_items = soup.find("div", class_="plainlist").ul.find_all("li")
# RANK_TO_COLOR_AND_LABEL = [
#     {
#         "color": get_background_color_from_style(color_item.span.attrs.get("style")),
#         "label": color_item.contents[2].strip(),
#     }
#     for color_item in color_key_items
# ]
# COLOR_TO_RANK = {
#     color_item["color"]: RankingCategory(index)
#     for index, color_item in enumerate(RANK_TO_COLOR_AND_LABEL)
# }