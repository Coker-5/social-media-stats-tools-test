import re
from datetime import datetime, timedelta
from framework.base_spider import BaseSpider, log
from tools.data_clean import cleaning
from douyin.parse_dy import parse_douyin_notes


class DouyinSpider(BaseSpider):
    """抖音爬虫类，继承自 BaseSpider"""

    def spider_dy_account(self):
        """采集账号维度数据"""
        log.info(f"[ {self.project_name} ] 开始采集抖音账号维度数据...")
        self.tab.get(url='https://creator.douyin.com')
        self.tab.wait(6)

        # 粉丝数据
        parent_ele = self.tab.ele('.statics-kyUhqC')
        numbers = parent_ele.eles('.number-No6ev9')
        numbers_text = [i.text for i in numbers]
        numbers_text = cleaning(numbers_text)

        fans_num = numbers_text[1]  # 粉丝
        likes_num = numbers_text[2]  # 获赞

        # 浏览数据初始化
        play_count = homepage_views = likes = shares = comments = followers = 0
        yesterday_play_count = yesterday_homepage_views = yesterday_likes = yesterday_shares = yesterday_comments = yesterday_followers = 0

        # 近七天
        parent_ele = self.tab.eles('.number-vDKr2F')
        parent_ele_text = [i.text for i in parent_ele]
        parent_ele_text = cleaning(parent_ele_text)
        if parent_ele_text and len(parent_ele_text) > 3:
            play_count, homepage_views, likes, shares, comments, followers = parent_ele_text[:6]

        # 昨天
        self.tab.ele("@role=combobox").click()
        option = self.tab.eles("@role=option")
        option[0].click()
        self.tab.wait(3)

        parent_ele = self.tab.eles('.number-vDKr2F')
        parent_ele_text = [i.text for i in parent_ele]
        parent_ele_text = cleaning(parent_ele_text)
        if parent_ele_text and len(parent_ele_text) > 3:
            yesterday_play_count, yesterday_homepage_views, yesterday_likes, yesterday_shares, yesterday_comments, yesterday_followers = parent_ele_text[
                :6]

        account_data = {
            "粉丝": int(fans_num),
            "获赞": int(likes_num),
            "近7天播放量": int(play_count),
            "近7天主页访问量": int(homepage_views),
            "近7天点赞": int(likes),
            "近7天分享": int(shares),
            "近7天评论": int(comments),
            "近7天净增粉丝": int(followers),
            "昨日播放量": int(yesterday_play_count),
            "昨日主页访问量": int(yesterday_homepage_views),
            "昨日点赞": int(yesterday_likes),
            "昨日分享": int(yesterday_shares),
            "昨日评论": int(yesterday_comments),
            "昨日净增粉丝": int(yesterday_followers),
        }

        log.info(account_data)
        self.save_to_bitable(data=account_data, config_path=['douyin', 'accounts'])
        return account_data

    def spider_dy_notes(self):
        """采集帖子维度数据"""
        log.info(f"[{self.project_name}] 开始采集抖音帖子维度数据...")
        self.tab.get(url='https://creator.douyin.com/creator-micro/content/manage')
        self.tab.wait(2)
        self.tab.change_mode('s')

        has_more = True
        max_cursor = 0
        notes_datas = []

        while has_more:
            headers = {
                "accept": "*/*",
                "referer": "https://creator.douyin.com/creator-micro/content/manage",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            }
            url = "https://creator.douyin.com/janus/douyin/creator/pc/work_list"
            params = {"status": "0", "count": "12", "max_cursor": max_cursor, "scene": "star_atlas",
                      "device_platform": "android", "aid": "1128"}

            try:
                self.tab.get(url, headers=headers, params=params)
                if self.tab.response.ok:
                    notes_res = self.tab.response.json()
                    max_cursor = notes_res.get("max_cursor", 0)
                    has_more = notes_res.get('has_more', False)
                    page_notes = parse_douyin_notes(notes_res)
                    notes_datas.extend(page_notes)
            except Exception as e:
                log.error(f"获取笔记数据时出错: {e}")
                break
            finally:
                self.tab.wait(1.5)

        self.save_to_bitable(data=notes_datas, config_path=['douyin', 'notes'])
        return notes_datas

    def get_recent_month_videos(self, initial_cursor=None, days=720):
        """获取指定时间范围发布的视频"""
        one_month_ago = datetime.now() - timedelta(days=days)
        videos = []
        cursor = initial_cursor
        has_more = True
        request_count = 0
        max_requests = 100

        def parse_chinese_date(date_str: str) -> datetime:
            pattern = r'发布于(\d{4})年(\d{1,2})月(\d{1,2})日 (\d{1,2}):(\d{1,2})'
            match = re.search(pattern, date_str)
            if match:
                year, month, day, hour, minute = map(int, match.groups())
                return datetime(year, month, day, hour, minute)
            return datetime.min

        while has_more and request_count < max_requests:
            url = f'https://creator.douyin.com/aweme/v1/creator/item/list/?cursor={cursor or ""}&aid=2906'
            headers = {"User-Agent": "Mozilla/5.0...", "Referer": "https://creator.douyin.com/..."}  # 简略
            try:
                self.tab.get(url, headers=headers, timeout=30)
                data = self.tab.response.json()
                cursor = data['cursor']
                has_more = data['has_more']
                request_count += 1

                for item in data.get('item_info_list', []):
                    publish_time = parse_chinese_date(item['create_time'])
                    if publish_time >= one_month_ago:
                        videos.append({
                            'title': item['title'],
                            'publish_time': publish_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'item_link': item['item_link'],
                            'comment_count': item['comment_count'],
                        })
                    else:
                        has_more = False
                        break
                if not has_more: break
                self.tab.wait(2)
            except Exception as e:
                log.error(f"发生错误: {e}")
                break
        return videos

    def spider_dy_comments(self):
        """采集评论数据"""
        log.info("开始采集评论数据...")
        self.tab.get(url='https://creator.douyin.com/creator-micro/interactive/comment')
        self.tab.change_mode('s')
        video_items = self.get_recent_month_videos()
        log.info(video_items)
        return video_items


if __name__ == '__main__':
    from DrissionPage import Chromium
    from tools.config_loader import get_project_config

    tab = Chromium().latest_tab
    p_name = "TEST"
    p_config = get_project_config(p_name)

    spider = DouyinSpider(tab=tab, project_name=p_name, project_config=p_config)
    spider.spider_dy_account()
    spider.spider_dy_notes()