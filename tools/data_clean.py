def cleaning(data_list):
    clean_data = []
    for item in data_list:
        new_item=item.strip().replace(',', '').replace('%', '')
        clean_data.append(new_item.strip())
    return clean_data