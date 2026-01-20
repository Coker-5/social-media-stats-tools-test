import json
import time
from framework.base_spider import BaseSpider, log
from kuaishou.parse_ks import parse_ks_photo_list_data, parse_ks_photo_detail_data, format_note_data
from tools.data_clean import cleaning


class KuaishouSpider(BaseSpider):
    """快手爬虫类，继承自 BaseSpider"""

    def spider_ks_account(self):
        """采集账号维度数据"""
        log.info(f"[ {self.project_name} ] 开始采集快手账号维度数据...")
        self.tab.get(url='https://cp.kuaishou.com/profile')
        self.tab.wait(6)

        # --- 粉丝数据 ---
        fans_num = 0
        fans_element = self.tab.eles('.user-cnt__item', timeout=2)
        fans_element_text = [i.text for i in fans_element]
        fans_element_text = cleaning(fans_element_text)
        if fans_element_text:
            fans_num = fans_element_text[0]

        # --- 浏览数据/近七天 ---
        values = [div.text for div in self.tab.eles('.question-tips')]
        numbers = [item for item in values if '+' not in item]
        numbers = cleaning(numbers)
        play_count = numbers[0]
        likes = numbers[1]
        followers = numbers[2]
        completion_rate = numbers[3]
        comments = numbers[4]
        shares = numbers[5]

        # --- 近三十天  ---
        filter_btn = self.tab.ele(".pop_value el-popover__reference")
        filter_btn.click()
        options = self.tab.eles(".option")
        options[1].click()
        self.tab.wait(3)

        values = [div.text for div in self.tab.eles('.question-tips')]
        numbers = [item for item in values if '+' not in item]
        numbers = cleaning(numbers)
        last_month_play_count, last_month_likes, last_month_followers, last_month_completion_rate, last_month_comments, last_month_shares = numbers[
            :6]

        # --- 近九十天  ---
        filter_btn = self.tab.ele(".pop_value el-popover__reference")
        filter_btn.click()
        options = self.tab.eles(".option")
        options[2].click()
        self.tab.wait(3)

        values = [div.text for div in self.tab.eles('.question-tips')]
        numbers = [item for item in values if '+' not in item]
        numbers = cleaning(numbers)
        last_3month_play_count, last_3month_likes, last_3month_followers, last_3month_completion_rate, last_3month_comments, last_3month_shares = numbers[
            :6]

        # --- 昨天  ---
        self.tab.change_mode('s')
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://cp.kuaishou.com",
            "Referer": "https://cp.kuaishou.com/profile",
            "X-Requested-With": "XMLHttpRequest",
        }
        url = "https://cp.kuaishou.com/rest/cp/creator/analysis/pc/home/author/overview"
        post_data = {"timeType": 1, "kuaishou.web.cp.api_ph": "9097fe9244498e1c9b77fa80fd72d0545190"}
        response = self.tab.post(url, headers=headers, data=json.dumps(post_data, separators=(',', ':')))
        result_json = response.json()
        yesterday_nums = cleaning([item["trendData"][-1]["count"] for item in result_json["data"]["basicData"]])


        account_data = {
            "粉丝": int(fans_num),
            "昨日播放量": int(yesterday_nums[0]), "昨日点赞量": int(yesterday_nums[1]),
            "昨日净增粉丝量": int(yesterday_nums[2]),
            "昨日完播率": str(yesterday_nums[3]), "昨日评论量": int(yesterday_nums[4]),
            "昨日分享量": int(yesterday_nums[5]),
            "近7天播放量": int(play_count), "近7天点赞量": int(likes), "近7天净增粉丝量": int(followers),
            "近7天完播率": str(completion_rate), "近7天评论量": int(comments), "近7天分享量": int(shares),
            "近30天播放量": int(last_month_play_count), "近30天点赞量": int(last_month_likes),
            "近30天净增粉丝量": int(last_month_followers),
            "近30天完播率": str(last_month_completion_rate), "近30天评论量": int(last_month_comments),
            "近30天分享量": int(last_month_shares),
            "近90天播放量": int(last_3month_play_count), "近90天点赞量": int(last_3month_likes),
            "近90天净增粉丝量": int(last_3month_followers),
            "近90天完播率": str(last_3month_completion_rate), "近90天评论量": int(last_3month_comments),
            "近90天分享量": int(last_3month_shares),
        }

        log.info(account_data)

        # 调用基类方法，手动传入路径
        self.save_to_bitable(data=account_data, config_path=['kuaishou', 'accounts'])

        self.tab.change_mode('d')

        return account_data

    def spider_ks_notes(self):
        """采集帖子维度数据"""
        log.info(f"[{self.project_name}] 开始采集快手帖子维度数据...")
        self.tab.get(url='https://cp.kuaishou.com/statistics/article')
        self.tab.wait(2)
        self.tab.change_mode('s')

        notes_datas = []
        page_size, page_num, has_more = 10, 0, True
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://cp.kuaishou.com",
            "Referer": "https://cp.kuaishou.com/statistics/article",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        }
        list_url = "https://cp.kuaishou.com/rest/cp/creator/analysis/pc/photo/list"

        while has_more and page_num < 50:
            payload = {"orderType": 2, "sortType": 1, "type": 0, "count": page_size, "page": page_num,
                       "kuaishou.web.cp.api_ph": "61bd1b1d511a4e8fad735372b6fe731a6db2"}
            resp = self.tab.post(list_url, headers=headers, data=json.dumps(payload, separators=(',', ':')))

            if resp.status_code == 200:
                result = resp.json()
                basic_infos = parse_ks_photo_list_data(result)

                for info in basic_infos:
                    detail_url = "https://cp.kuaishou.com/rest/cp/creator/analysis/pc/photo/single/overview"
                    detail_payload = {"dataChangeType": 1, "photoId": info["photo_id"], "tabType": 1,
                                      "timeGranularity": 1,
                                      "kuaishou.web.cp.api_ph": "61bd1b1d511a4e8fad735372b6fe731a6db2"}
                    detail_resp = self.tab.post(detail_url, headers=headers,
                                                data=json.dumps(detail_payload, separators=(',', ':')))
                    trend_data = parse_ks_photo_detail_data(
                        detail_resp.json()) if detail_resp.status_code == 200 else {}

                    note_data = format_note_data(info, trend_data)
                    if note_data:
                        notes_datas.append(note_data)
                    time.sleep(0.5)

                if len(basic_infos) < page_size:
                    has_more = False
                else:
                    page_num += 1; time.sleep(1)
            else:
                has_more = False

        log.info(notes_datas)
        self.save_to_bitable(data=notes_datas, config_path=['kuaishou', 'notes'])
        return notes_datas


if __name__ == '__main__':
    from DrissionPage import Chromium
    from tools.config_loader import get_project_config

    tab = Chromium().latest_tab

    p_name = "TEST"
    p_config = get_project_config(p_name)

    spider = KuaishouSpider(tab=tab, project_name=p_name, project_config=p_config)

    spider.spider_ks_account()
    spider.spider_ks_notes()