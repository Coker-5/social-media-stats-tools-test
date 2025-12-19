def cleaning(data_list):
    clean_data = []
    for item in data_list:
        new_item=item.strip().replace(',', '').replace('%', '')
        if "万" in new_item:
            new_item = new_item.replace("万", "")
            new_item = float(new_item) * 10000
        clean_data.append(new_item)
    return clean_data