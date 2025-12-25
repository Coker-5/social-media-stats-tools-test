import re


def cleaning(data_list):
    """
    清洗和规范化数字数据
    返回值说明：
    - 纯数字（包括小数）：返回原数字类型（int或float）
    - 带单位的数字：转换为整数
    - 百分比：返回小数（如0.5%返回0.5）
    """
    clean_data = []

    for item in data_list:
        if item is None:
            clean_data.append(0)
            continue

        # 转换为字符串并清理
        item_str = str(item).strip()

        # 如果为空字符串
        if not item_str:
            clean_data.append(0)
            continue

        # 特殊处理：处理"+"符号（如"+1000"表示增加）
        is_positive_increment = item_str.startswith('+')
        if is_positive_increment:
            item_str = item_str[1:]  # 移除+号

        # 移除逗号和空格
        item_str = item_str.replace(',', '').replace(' ', '')

        # 处理百分比（保留原始值，不乘以100）
        is_percent = '%' in item_str
        if is_percent:
            item_str = item_str.replace('%', '')
            # 百分比保留小数
            try:
                percent_value = float(item_str)
                clean_data.append(percent_value)  # 返回小数，如 0.5
                continue
            except ValueError:
                clean_data.append(0)
                continue

        # 单位转换
        multiplier = 1
        has_unit = False

        # 处理中文单位
        if '亿' in item_str:
            multiplier = 100000000
            item_str = item_str.replace('亿', '')
            has_unit = True
        elif '千万' in item_str:
            multiplier = 10000000
            item_str = item_str.replace('千万', '')
            has_unit = True
        elif '百万' in item_str:
            multiplier = 1000000
            item_str = item_str.replace('百万', '')
            has_unit = True
        elif '万' in item_str:
            multiplier = 10000
            item_str = item_str.replace('万', '')
            has_unit = True
        elif '千' in item_str:
            multiplier = 1000
            item_str = item_str.replace('千', '')
            has_unit = True

        # 处理英文单位
        item_str_lower = item_str.lower()
        if 'k' in item_str_lower:
            multiplier = 1000
            item_str = re.sub(r'k', '', item_str_lower, flags=re.IGNORECASE)
            has_unit = True
        elif 'w' in item_str_lower:
            multiplier = 10000
            item_str = re.sub(r'w', '', item_str_lower, flags=re.IGNORECASE)
            has_unit = True
        elif 'm' in item_str_lower:
            multiplier = 1000000
            item_str = re.sub(r'm', '', item_str_lower, flags=re.IGNORECASE)
            has_unit = True
        elif 'b' in item_str_lower:
            multiplier = 1000000000
            item_str = re.sub(r'b', '', item_str_lower, flags=re.IGNORECASE)
            has_unit = True

        # 提取数字（包括小数和负数）
        match = re.search(r'[-+]?\d*\.?\d+', item_str)
        if not match:
            clean_data.append(0)
            continue

        num_str = match.group()

        try:
            if has_unit:
                # 有单位的数字：转换为整数
                num = float(num_str) * multiplier
                # 四舍五入到整数
                num = int(round(num))
            else:
                # 没有单位的数字：保留原始类型
                if '.' in num_str:
                    # 小数：保留原样
                    num = float(num_str)
                else:
                    # 整数
                    num = int(num_str)

            clean_data.append(num)
        except (ValueError, TypeError) as e:
            # 记录转换失败的数据
            print(f"警告: 无法转换 '{item}' 为数字: {e}")
            clean_data.append(0)

    return clean_data