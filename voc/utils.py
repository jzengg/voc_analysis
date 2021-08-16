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
    color = attr.split(":")[1].strip()
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
