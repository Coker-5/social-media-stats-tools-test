import os
import warnings
from datetime import datetime
from pathlib import Path

from framework.base_spider import BaseSpider, log
from xiaohongshu.parse_xhs import parse_xhs_notes
from tools.data_clean import cleaning

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

BASE_DIR = Path(__file__).parent.parent


class XHSSpider(BaseSpider):
    """小红书爬虫类，继承自 BaseSpider"""

    def spider_xhs_account(self):
        """采集账号维度数据"""
        log.info(f"[{self.project_name}] 开始采集小红书账号维度数据...")
        self.tab.get(url='https://creator.xiaohongshu.com/new/home')
        self.tab.wait(6)

        fans_num = 0
        likes_num = 0
        try_count = 0

        while True:
            fans_element = self.tab.ele('text=粉丝数', timeout=2)
            if try_count > 5:
                log.error(f"[{self.project_name}] 小红书主页访问错误！！！")
                break

            if fans_element:
                fans_num = fans_element.prev().text
                likes_element = self.tab.ele('text=获赞与收藏', timeout=2)
                if likes_element:
                    likes_num = likes_element.prev().text

                self.tab.wait(3)

                # --- 近七天数据采集 ---
                creator_blocks = self.tab.eles('.creator-block  default-cursor')
                numbers_with_units_week = []
                for block in creator_blocks:
                    num_elem = block.ele('.number')
                    unit_elem = block.ele('.unit', timeout=0)
                    if num_elem:
                        num_text = num_elem.text + (unit_elem.text if unit_elem else "")
                        numbers_with_units_week.append(num_text)
                    else:
                        numbers_with_units_week.append("")

                numbers = cleaning(numbers_with_units_week)
                imp_count, play_count, cover_click_rate, full_view_rate = numbers[0:4]
                likes, comments, favorites, shares = numbers[4:8]
                rise_fans_count, new_followers, cancel_followers, homepage_views = numbers[8:12]

                # --- 近三十天数据采集 ---
                filter_btn = self.tab.ele("text:近30日")
                filter_btn.click()
                self.tab.wait(3)

                creator_blocks = self.tab.eles('.creator-block  default-cursor')
                numbers_with_units_month = []
                for block in creator_blocks:
                    num_elem = block.ele('.number')
                    unit_elem = block.ele('.unit', timeout=0)
                    if num_elem:
                        num_text = num_elem.text + (unit_elem.text if unit_elem else "")
                        numbers_with_units_month.append(num_text)
                    else:
                        numbers_with_units_month.append("")

                numbers = cleaning(numbers_with_units_month)
                last_month_imp_count = numbers[0]
                last_month_play_count = numbers[1]
                last_month_homepage_views = numbers[11]
                last_month_likes = numbers[4]
                last_month_favorites = numbers[6]
                last_month_comments = numbers[5]
                last_month_shares = numbers[7]
                last_month_rise_fans_count = numbers[8]
                last_month_new_followers = numbers[9]
                last_month_cancel_followers = numbers[10]
                last_month_cover_click_rate = numbers[2]
                last_month_full_view_rate = numbers[3]

                account_data = {
                    "粉丝": int(fans_num),
                    "获赞": int(likes_num),
                    "近7天曝光": int(imp_count), "近7天观看": int(play_count),
                    "近7天封面点击率": str(cover_click_rate), "近7天视频完播率": str(full_view_rate),
                    "近7天点赞": int(likes), "近7天评论": int(comments), "近7天收藏": int(favorites),
                    "近7天分享": int(shares), "近7天净涨粉": int(rise_fans_count),
                    "近7天新增关注": int(new_followers), "近7天取消关注": int(cancel_followers),
                    "近7天主页访客": int(homepage_views),
                    "近30天曝光": int(last_month_imp_count), "近30天观看": int(last_month_play_count),
                    "近30天封面点击率": str(last_month_cover_click_rate),
                    "近30天视频完播率": str(last_month_full_view_rate),
                    "近30天主页访客": int(last_month_homepage_views), "近30天点赞": int(last_month_likes),
                    "近30天收藏": int(last_month_favorites), "近30天分享": int(last_month_shares),
                    "近30天评论": int(last_month_comments), "近30天净涨粉": int(last_month_rise_fans_count),
                    "近30天新增关注": int(last_month_new_followers), "近30天取消关注": int(last_month_cancel_followers)
                }

                log.info(account_data)
                self.save_to_bitable(data=account_data, config_path=['xiaohongshu', 'accounts'])
                return account_data
            else:
                self.tab.refresh()
                log.info(f"[{self.project_name}] 小红书主页重试第{try_count + 1}次")
                try_count += 1
                self.tab.wait(5)

    def spider_xhs_notes(self):
        log.info(f"[{self.project_name}] 开始采集小红书帖子维度数据...")
        self.tab.get(url='https://creator.xiaohongshu.com/statistics/data-analysis')
        self.tab.wait(2)

        current_file_path = Path(__file__).parent
        statics_dir = current_file_path / "statics"
        os.makedirs(statics_dir, exist_ok=True)

        file_name = f"{datetime.now().strftime('%Y_%m_%d_%H%M')}-{self.project_name}-小红书-帖子详情数据.xlsx"
        download_btn = self.tab.ele("text:导出数据")

        mission = download_btn.click.to_download(save_path=str(statics_dir), rename=file_name)
        mission.wait(show=False)

        notes_datas = parse_xhs_notes(file_path=str(statics_dir / file_name))

        self.save_to_bitable(data=notes_datas, config_path=['xiaohongshu', 'notes'])
        return notes_datas


if __name__ == '__main__':
    from DrissionPage import Chromium
    from tools.config_loader import get_project_config

    tab = Chromium().latest_tab

    p_name = "TEST"
    p_config = get_project_config(p_name)

    spider = XHSSpider(tab=tab, project_name=p_name, project_config=p_config)
    spider.spider_xhs_account()
    spider.spider_xhs_notes()