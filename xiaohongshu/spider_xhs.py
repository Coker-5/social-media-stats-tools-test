from DrissionPage import Chromium
from tools.feishu_bitable_uploader import FeishuBitableWriter
from tools.logstar import get_logger
from tools.config_loader import (BASE_TOKEN,TABLE_XHS_NOTES,TABLE_XHS_ACCOUNTS)

log = get_logger()
tab = None


# 账号维度数据
def spider_xhs_accounts():
    # 首页
    log.info("开始采集账号维度数据...")
    tab.get(url='https://creator.xiaohongshu.com/new/home')
    tab.wait(6)

    fans_num = 0
    likes_num = 0

    # 小红书主页偶尔会返回空html，增加重试机制次
    try_count = 0
    while True:
        fans_element = tab.ele('text=粉丝数', timeout=2)
        if try_count > 5:
            log.error("小红书主页访问错误！！！")
            break
        if fans_element:
            if fans_element:
                # 获取前一个兄弟元素（数值元素）
                fans_num = fans_element.prev().text

            # 找到"获赞与收藏"前面的数值
            likes_element = tab.ele('text=获赞与收藏', timeout=2)
            if likes_element:
                likes_num = likes_element.prev().text

            tab.wait(3)

            # 浏览数据
            # 近七天
            numbers = [elem.text for elem in tab.eles('.number')]
            play_count = numbers[0]  # 观看
            play_time = numbers[1]  # 观看总时长
            homepage_views = numbers[2]  # 主页访客
            likes = numbers[3]  # 点赞
            favorites = numbers[4]  # 收藏
            comments = numbers[5]  # 评论
            bullet = numbers[6]  # 弹幕
            followers = numbers[7]  # 笔记涨粉
            shares = numbers[8]  # 分享

            filter = tab.ele(".filter")
            filter.ele(".btn").click()
            tab.wait(3)

            # 近三十天
            numbers = [elem.text for elem in tab.eles('.number')]
            last_month_play_count = numbers[0]  # 观看
            last_month_play_time = numbers[1]  # 观看总时长
            last_month_homepage_views = numbers[2]  # 主页访客
            last_month_likes = numbers[3]  # 点赞
            last_month_favorites = numbers[4]  # 收藏
            last_month_comments = numbers[5]  # 评论
            last_month_bullet = numbers[6]  # 弹幕
            last_month_followers = numbers[7]  # 笔记涨粉
            last_month_shares = numbers[8]  # 分享

            accont_data = {
                "粉丝": int(fans_num),
                "获赞": int(likes_num),
                "近7天观看": int(play_count),
                "近7天观看总时长": int(play_time),
                "近7天主页访客": int(homepage_views),
                "近7天点赞": int(likes),
                "近7天收藏": int(favorites),
                "近7天分享": int(shares),
                "近7天评论": int(comments),
                "近7天弹幕": int(bullet),
                "近7天笔记涨粉": int(followers),

                "近30天观看": int(last_month_play_count),
                "近30天观看总时长": int(last_month_play_time),
                "近30天主页访客": int(last_month_homepage_views),
                "近30天点赞": int(last_month_likes),
                "近30天收藏": int(last_month_favorites),
                "近30天分享": int(last_month_shares),
                "近30天评论": int(last_month_comments),
                "近30天弹幕": int(last_month_bullet),
                "近30天笔记涨粉": int(last_month_followers),
            }

            log.info(accont_data)
            return accont_data
        else:
            tab.refresh()
            log.info(f"小红书重试第{try_count + 1}次")
            try_count += 1

# 帖子维度数据
def spider_xhs_notes():
    # 数据看板-内容分析-笔记数据
    log.info("开始采集帖子维度数据...")
    tab.get(url='https://creator.xiaohongshu.com/statistics/data-analysis')
    tab.wait(2)
    tab.change_mode('s')

    notes_datas = []
    page_size = 10
    page_num = 1
    total_pages = 0

    url = "https://creator.xiaohongshu.com/api/galaxy/creator/datacenter/note/analyze/list"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "authorization;": "",
        "priority": "u=1, i",
        "referer": "https://creator.xiaohongshu.com/statistics/data-analysis",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "x-b3-traceid": "3c4a733a9a80d5cc",
        "x-s": "XYS_2UQhPsHCH0c1PjhhHjIj2erjwjQM89PjNsQhPjHCHDMYGUmOLUHVHdWAH0ijJnEAPerIPpuInBihadGF8rq9JgZ62rS8/BI9/rEeLB80qbbh/9iU4Lz/GAm9+A8w+LDAypkIJb4aL0+ctFRPG7Skt7mOPAQOa0qIJLI7PBYw/9bNpozdaBTCyMmtnfSHaaV68npQ87Yk+7SazfMszsTL87kV8jV3PAGILD+PqrIM/opi4nYI8dp38eGMPrh7Jnpz4SmypFRkweD6pMHF+/myapSbJbmHHjIj2ecjwjHjKc==",
        "x-s-common": "2UQAPsHCPUIjqArjwjHjNsQhPsHCH0rjNsQhPaHCH0c1PjhhHjIj2eHjwjQ+GnPW/MPjNsQhPUHCHdpdGUHVHdWFH0ijPshlPeH1PjHVHdWMH0ijP/SjPem0wnrM8e83wBu9PBS18dpEq7p9PgQSJBzjJnEdGd8lG9LE+BIAPeZIPerE+/clPjHVHdW9H0ijHjIj2eqjwjHjNsQhwsHCHDDAwoQH8B4AyfRI8FS98g+Dpd4daLP3JFSb/BMsn0pSPM87nrldzSzQ2bPAGdb7zgQB8nph8emSy9E0cgk+zSS1qgzianYt8Lc7/gYlqg4Dag8mqM4sG9Y7LozF89FF+DTp2dYQyemAPrlNq9kl49EE+Fzyag86q7YjLBkEndpmanYN8LzY+7+fppzLadbFLjTl4FbI8omwaL+iJLEQwrTCpd4/aL+d8nTM4rY7qg4raLpBqLSbN7+LapkkagYU/LS989pDqg4atA4ILoky/d+Dn/+S8dbFcLS3/fLApd4dqgbFqomM4oYN2f4APp4I8LSepS4QybrINMmFLLTn4FbQPMiUJ9MD8nSl498QcFbSpb8FqDSbtUTQznM1G98D8nkd2SSUJ9RA8db7/MkgJ9pD/rzrcfRdq9kyqrQQ2rTA8b8FGLS34fpfqg4aGDMPaL4f+rQQPA4A2obFzaRg/9phPBIFanYzqFSbwsTzJFYpagYTLrRCJnRQyn+G8pm7zDS9yLPUc04Azoi7q7Yn4BzQ408S8eq78pSxLD4QznzS+S4jzozc49kQyrkAP9RSqA8r4fpLLozwGML98LzM4ApQ4SS120Z98n8n478d8jRAzbm7cDDALFlQ2BMVq7bFq9bc47SAqFYjnDb98/+IN9prLo4haL+Sq9TrPBp/8LYkanD7q9kjJ7PA87QBanSD8/8M4A+Q4flEJS8F4n4c4AzQyrkA8b87LLS9+nL94gqManWAq9kM4Apwqg4oJM874LSe2SzQ4SQFLnpncL4VN7+kqgzBanYc4rSk8np84g468p40G7mp/7+rq9TManYa2gzc474Cqg4manTSqM4l4oplaLbApDG9qAbQGDlQz/mA+fpDq9Sc4B+0Lo4UaL+t8n8n498Qy94A+0mgJFSea9pDJURSpM8FPFDA+9pnqgqAwrQ8qDSiasTQcA8A2rS68/GE4fpDqDRAnpm7aLS9yFTQzLSAa7b7pFSkGFTQPURSPBk3Jdm+8BL9Lo4bagYrPobn4MkjJFESy9k6q7Yn4bpl4gcAanSoGLS9t7Y6pdc7zM87aFSe8BpDpAmSpbm7NFkM4FlQyr8zGdp7PFDAzAYjGgpPanS6qAr7ad+r8URSpSmFLg4QO/FjNsQhwaHCN/r7w/qh+eqh+jIj2erIH0iINsQhP/rjwjQ1J7QTGnIjKc==",
        "x-t": "1765250920396",
        "x-xray-traceid": "cd8093b7dd3be40146161bce823fa307"
    }
    params = {
        "type": "0",
        "page_size": page_size,
        "page_num": page_num
    }
    tab.get(url, headers=headers, params=params)
    if tab.response.ok:
        notes_res = tab.response.json()
        total = notes_res["data"]["total"]
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size  # 向上取整

    while page_num <= total_pages:
        try:
            url = "https://creator.xiaohongshu.com/api/galaxy/creator/datacenter/note/analyze/list"
            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "zh-CN,zh;q=0.9",
                "authorization;": "",
                "priority": "u=1, i",
                "referer": "https://creator.xiaohongshu.com/statistics/data-analysis",
                "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"macOS\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "x-b3-traceid": "3c4a733a9a80d5cc",
                "x-s": "XYS_2UQhPsHCH0c1PjhhHjIj2erjwjQM89PjNsQhPjHCHDMYGUmOLUHVHdWAH0ijJnEAPerIPpuInBihadGF8rq9JgZ62rS8/BI9/rEeLB80qbbh/9iU4Lz/GAm9+A8w+LDAypkIJb4aL0+ctFRPG7Skt7mOPAQOa0qIJLI7PBYw/9bNpozdaBTCyMmtnfSHaaV68npQ87Yk+7SazfMszsTL87kV8jV3PAGILD+PqrIM/opi4nYI8dp38eGMPrh7Jnpz4SmypFRkweD6pMHF+/myapSbJbmHHjIj2ecjwjHjKc==",
                "x-s-common": "2UQAPsHCPUIjqArjwjHjNsQhPsHCH0rjNsQhPaHCH0c1PjhhHjIj2eHjwjQ+GnPW/MPjNsQhPUHCHdpdGUHVHdWFH0ijPshlPeH1PjHVHdWMH0ijP/SjPem0wnrM8e83wBu9PBS18dpEq7p9PgQSJBzjJnEdGd8lG9LE+BIAPeZIPerE+/clPjHVHdW9H0ijHjIj2eqjwjHjNsQhwsHCHDDAwoQH8B4AyfRI8FS98g+Dpd4daLP3JFSb/BMsn0pSPM87nrldzSzQ2bPAGdb7zgQB8nph8emSy9E0cgk+zSS1qgzianYt8Lc7/gYlqg4Dag8mqM4sG9Y7LozF89FF+DTp2dYQyemAPrlNq9kl49EE+Fzyag86q7YjLBkEndpmanYN8LzY+7+fppzLadbFLjTl4FbI8omwaL+iJLEQwrTCpd4/aL+d8nTM4rY7qg4raLpBqLSbN7+LapkkagYU/LS989pDqg4atA4ILoky/d+Dn/+S8dbFcLS3/fLApd4dqgbFqomM4oYN2f4APp4I8LSepS4QybrINMmFLLTn4FbQPMiUJ9MD8nSl498QcFbSpb8FqDSbtUTQznM1G98D8nkd2SSUJ9RA8db7/MkgJ9pD/rzrcfRdq9kyqrQQ2rTA8b8FGLS34fpfqg4aGDMPaL4f+rQQPA4A2obFzaRg/9phPBIFanYzqFSbwsTzJFYpagYTLrRCJnRQyn+G8pm7zDS9yLPUc04Azoi7q7Yn4BzQ408S8eq78pSxLD4QznzS+S4jzozc49kQyrkAP9RSqA8r4fpLLozwGML98LzM4ApQ4SS120Z98n8n478d8jRAzbm7cDDALFlQ2BMVq7bFq9bc47SAqFYjnDb98/+IN9prLo4haL+Sq9TrPBp/8LYkanD7q9kjJ7PA87QBanSD8/8M4A+Q4flEJS8F4n4c4AzQyrkA8b87LLS9+nL94gqManWAq9kM4Apwqg4oJM874LSe2SzQ4SQFLnpncL4VN7+kqgzBanYc4rSk8np84g468p40G7mp/7+rq9TManYa2gzc474Cqg4manTSqM4l4oplaLbApDG9qAbQGDlQz/mA+fpDq9Sc4B+0Lo4UaL+t8n8n498Qy94A+0mgJFSea9pDJURSpM8FPFDA+9pnqgqAwrQ8qDSiasTQcA8A2rS68/GE4fpDqDRAnpm7aLS9yFTQzLSAa7b7pFSkGFTQPURSPBk3Jdm+8BL9Lo4bagYrPobn4MkjJFESy9k6q7Yn4bpl4gcAanSoGLS9t7Y6pdc7zM87aFSe8BpDpAmSpbm7NFkM4FlQyr8zGdp7PFDAzAYjGgpPanS6qAr7ad+r8URSpSmFLg4QO/FjNsQhwaHCN/r7w/qh+eqh+jIj2erIH0iINsQhP/rjwjQ1J7QTGnIjKc==",
                "x-t": "1765250920396",
                "x-xray-traceid": "cd8093b7dd3be40146161bce823fa307"
            }
            params = {
                "type": "0",
                "page_size": page_size,
                "page_num": page_num
            }
            tab.get(url, headers=headers, params=params)
            if tab.response.ok:
                notes_res = tab.response.json()
                notes_items = notes_res["data"]["note_infos"]
                for note in notes_items:
                    title = note["title"]
                    post_time = note["post_time"]
                    imp_count = note["imp_count"]
                    like_count = note.get("like_count", 0)
                    read_count = note.get("read_count", 0)
                    cover_click_rate = note.get("coverClickRate", 0)
                    comment_count = note.get("comment_count", 0)
                    share_count = note.get("share_count", 0)
                    fav_count = note.get("fav_count", 0)
                    view_time_avg = note.get("view_time_avg", 0)

                    note_data = {
                        "帖子名称": title,
                        "发布时间": post_time,
                        "曝光": int(imp_count),
                        "观看": int(read_count),
                        "点赞": int(like_count),
                        "评论": int(comment_count),
                        "分享": int(share_count),
                        "收藏": int(fav_count),
                        "封面点击率": str(int(cover_click_rate)*100),
                        "人均观看时长": int(view_time_avg),
                    }
                    log.info(note_data)
                    notes_datas.append(note_data)



        except Exception as e:
            log.error(e)
        finally:
            tab.wait(2)
            page_num += 1

    return notes_datas


# 保存数据
def save_datas(table_id, datas):
    base_token = BASE_TOKEN  # 多维表格的基础token

    writer = FeishuBitableWriter(base_token, table_id)
    writer.add_records(datas)


def spider_xiaohongshu(page_xiaohongshu):
    global tab
    tab = page_xiaohongshu
    accounts_data = spider_xhs_accounts()
    # 保存账号数据
    save_datas(table_id=TABLE_XHS_ACCOUNTS, datas=accounts_data)

    notes_datas = spider_xhs_notes()
    # 保存帖子数据
    save_datas(table_id=TABLE_XHS_NOTES, datas=notes_datas)

    final_data = {
        "数据平台": "小红书",
        "账号维度数据": accounts_data,
        "帖子维度数据": notes_datas,
    }
    log.info(final_data)
    return final_data


if __name__ == '__main__':
    tab = Chromium().latest_tab
    spider_xiaohongshu(tab)
