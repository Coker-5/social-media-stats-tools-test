import os
from datetime import datetime
from pathlib import Path
from framework.base_spider import BaseSpider, log
from shipinhao.parse_sph import parse_sph_notes
from tools.data_clean import cleaning

# 获取当前文件所在目录的父目录，用于 statics 存储
BASE_DIR = Path(__file__).parent.parent


class ShipinhaoSpider(BaseSpider):
    """视频号爬虫类，继承自 BaseSpider"""

    def spider_sph_account(self):
        """采集账号维度数据"""
        log.info(f"[{self.project_name}] 开始采集视频号账号维度数据...")
        self.tab.get(url='https://channels.weixin.qq.com/platform/')
        self.tab.wait(6)

        # --- 粉丝数据 ---
        fans_elements = self.tab.eles('.finder-info-num', timeout=2)
        if len(fans_elements) > 1:
            fans_num = fans_elements[1].text
            fans_num = cleaning([fans_num])[0]
        else:
            fans_num = 0

        # --- 浏览数据 ---
        data_elements = self.tab.eles('.data')
        values = [ele.text.strip() for ele in data_elements]
        numbers = cleaning(values)

        account_data = {
            "粉丝": int(fans_num),
            "净增关注": int(numbers[0]) if len(numbers) > 0 else 0,
            "新增播放": int(numbers[1]) if len(numbers) > 1 else 0,
            "新增点赞": int(numbers[2]) if len(numbers) > 2 else 0,
            "新增评论": int(numbers[3]) if len(numbers) > 3 else 0,
        }

        log.info(account_data)
        self.save_to_bitable(data=account_data, config_path=['shipinhao', 'accounts'])
        return account_data

    def spider_sph_notes(self):
        # 数据中心-视频数据
        log.info("开始采集帖子维度数据...")
        self.tab.get(url='https://channels.weixin.qq.com/platform/statistic/post')
        self.tab.wait(6)

        container = self.tab.ele('.wujie_iframe', timeout=2).shadow_root
        single_mv_btn = container.ele('.weui-desktop-tab__nav', timeout=2)
        if single_mv_btn:
            single_mv_btn.click()
            self.tab.wait(2)
        last_month_btn = container.ele("text:近30天", timeout=2)
        if last_month_btn:
            last_month_btn.click()
            self.tab.wait(2)
        self.tab.wait(2)

        notes_datas = []

        current_file_path = Path(__file__).parent
        statics_dir = current_file_path / "statics"
        os.makedirs(statics_dir, exist_ok=True)

        file_name = f"{datetime.now().strftime('%Y_%m_%d_%H%M')}-视频号-帖子详情数据.csv"
        download_btn = container.ele(".filter-extra", timeout=2)
        mission = download_btn.click.to_download(save_path=str(statics_dir), rename=file_name)
        mission.wait(show=False)

        notes_datas = parse_sph_notes(file_path=str(statics_dir / file_name))

        log.info(notes_datas)

        self.save_to_bitable(data=notes_datas, config_path=['shipinhao', 'notes'])
        return notes_datas


if __name__ == '__main__':
    from DrissionPage import Chromium
    from tools.config_loader import get_project_config

    tab = Chromium().latest_tab
    p_name = "TEST"
    p_config = get_project_config(p_name)

    spider = ShipinhaoSpider(tab=tab, project_name=p_name, project_config=p_config)
    # spider.spider_sph_account()
    spider.spider_sph_notes()
