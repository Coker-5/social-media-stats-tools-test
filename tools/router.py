# 导入登录函数
from douyin.login_dy import login_douyin
from xiaohongshu.login_xhs import login_xiaohongshu
from shipinhao.login_sph import login_shipinhao
from kuaishou.login_ks import login_kuaishou

# 导入爬虫类
from douyin.spider_dy import DouyinSpider
from xiaohongshu.spider_xhs import XHSSpider
from shipinhao.spider_sph import ShipinhaoSpider
from kuaishou.spider_ks import KuaishouSpider

# 建立映射表
TASK_ROUTER = {
    "douyin": {
        "login_func": login_douyin,
        "spider_class": DouyinSpider,
        "methods": {
            "account": "spider_dy_account",  # JSON key 对应 类方法名
            "notes": "spider_dy_notes"
        }
    },
    "xiaohongshu": {
        "login_func": login_xiaohongshu,
        "spider_class": XHSSpider,
        "methods": {
            "account": "spider_xhs_account",
            "notes": "spider_xhs_notes"
        }
    },
    "kuaishou": {
        "login_func": login_kuaishou,
        "spider_class": KuaishouSpider,
        "methods": {
            "account": "spider_ks_account",
            "notes": "spider_ks_notes"
        }
    },
    "shipinhao": {
        "login_func": login_shipinhao,
        "spider_class": ShipinhaoSpider,
        "methods": {
            "account": "spider_sph_account",
            "notes": "spider_sph_notes"
        }
    }
}
