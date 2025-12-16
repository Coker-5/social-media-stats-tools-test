import re
from DrissionPage import Chromium
from tools.feishu_bitable_uploader import FeishuBitableWriter
from tools.logstar import get_logger
import config

log = get_logger()
tab = Chromium().latest_tab


# 账号维度数据
def spider_ks_accounts():
    global tab
    # 首页
    log.info("开始采集账号维度数据...")
    tab.get(url='https://cp.kuaishou.com/profile')
    tab.wait(6)

    # 粉丝数据
    fans_num = 0
    fans_element = tab.eles('.user-cnt__item', timeout=2)
    if fans_element:
        fans_num =fans_element[0].text
        fans_num = re.search(r'\d+', fans_num)[0]

    # 浏览数据
    # 近七天
    values = [div.text.strip().replace(',', '').replace('%', '')
              for div in tab.eles('.question-tips')]
    numbers = [item for item in values if '+' not in item]
    play_count = numbers[0]  # 播放量
    likes = numbers[1]  # 点赞
    followers = numbers[2]  # 净增粉丝量
    completion_rate = numbers[3]  # 完播率
    comments = numbers[4]  # 评论
    shares = numbers[5]  # 分享


    # 近三十天
    filter = tab.ele(".pop_value el-popover__reference")
    filter.click()
    options=tab.eles(".option")
    options[1].click()
    tab.wait(3)

    values = [div.text.strip().replace(',', '').replace('%', '')
              for div in tab.eles('.question-tips')]
    numbers = [item for item in values if '+' not in item]
    last_month_play_count = numbers[0]  # 播放量
    last_month_likes = numbers[1]  # 点赞
    last_month_followers = numbers[2]  # 净增粉丝量
    last_month_completion_rate = numbers[3]  # 完播率
    last_month_comments = numbers[4]  # 评论
    last_month_shares = numbers[5]  # 分享

    # 近九十天
    filter = tab.ele(".pop_value el-popover__reference")
    filter.click()
    options = tab.eles(".option")
    options[2].click()
    tab.wait(3)

    values = [div.text.strip().replace(',', '').replace('%', '')
              for div in tab.eles('.question-tips')]
    numbers = [item for item in values if '+' not in item]
    last_3month_play_count = numbers[0]  # 播放量
    last_3month_likes = numbers[1]  # 点赞量
    last_3month_followers = numbers[2]  # 净增粉丝量
    last_3month_completion_rate = numbers[3]  # 完播率
    last_3month_comments = numbers[4]  # 评论量
    last_3month_shares = numbers[5]  # 分享量


    accont_data = {
        "粉丝": int(fans_num),
        "近7天播放量": int(play_count),
        "近7天点赞量": int(likes),
        "近7天净增粉丝量": int(followers),
        "近7天完播率": completion_rate,
        "近7天评论量": int(comments),
        "近7天分享量": int(shares),

        "近30天播放量": int(last_month_play_count),
        "近30天点赞量": int(last_month_likes),
        "近30天净增粉丝量": int(last_month_followers),
        "近30天完播率": last_month_completion_rate,
        "近30天评论量": int(last_month_comments),
        "近30天分享量": int(last_month_shares),

        "近90天播放量": int(last_3month_play_count),
        "近90天点赞量": int(last_3month_likes),
        "近90天净增粉丝量": int(last_3month_followers),
        "近90天完播率": last_3month_completion_rate,
        "近90天评论量": int(last_3month_comments),
        "近90天分享量": int(last_3month_shares),
    }

    log.info(accont_data)
    return accont_data

# 帖子维度数据
def spider_ks_notes():
    """
    采集快手创作者中心的帖子数据
    返回帖子维度数据列表
    """
    log.info("开始采集帖子维度数据...")
    tab.get(url='https://cp.kuaishou.com/statistics/article')
    tab.wait(2)
    tab.change_mode('s')

    notes_datas = []
    page_size = 10
    page_num = 0  # 快手接口从0开始
    total_pages = 1
    has_more = True

    # 请求头
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://cp.kuaishou.com",
        "Referer": "https://cp.kuaishou.com/statistics/article",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "returnSetRootDomainLoginUrl": "true",
        "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\""
    }


    url = "https://cp.kuaishou.com/rest/cp/creator/analysis/pc/photo/list"

    while has_more and page_num < 50:
        try:
            # 构建请求数据
            data = {
                "orderType": 2,
                "sortType": 1,
                "type": 0,
                "count": page_size,
                "page": page_num,
                "kuaishou.web.cp.api_ph": "61bd1b1d511a4e8fad735372b6fe731a6db2"
            }

            data_json = json.dumps(data, separators=(',', ':'))

            # 发送POST请求
            response = tab.post(
                url,
                headers=headers,
                data=data_json
            )

            if response.status_code == 200:
                result = response.json()

                if result.get("result") == 1:  # 请求成功
                    photo_list = result.get("data", {}).get("photoList", {})
                    photo_items = photo_list.get("photoItems", [])
                    total_count = photo_list.get("totalCount", 0)

                    # 如果是第一页，计算总页数
                    if page_num == 0 and total_count > 0:
                        total_pages = (total_count + page_size - 1) // page_size
                        print(f"总共有 {total_count} 个帖子，共 {total_pages} 页")

                    # 处理当前页的数据
                    for item in photo_items:
                        # 提取帖子信息
                        title = item.get("title", "无标题")
                        photo_id = item.get("photoId", "")
                        publish_time = item.get("publishTime", 0)
                        play_count = item.get("playCount", 0)
                        like_count = item.get("likeCount", 0)
                        comment_count = item.get("commentCount", 0)
                        collect_count = item.get("collectCount", 0)
                        follow_count = item.get("followCount", 0)
                        fpr = item.get("fpr", 0.0)  # 完播率
                        video = item.get("video", False)

                        # 格式化发布时间
                        if publish_time:
                            publish_time_str = datetime.fromtimestamp(publish_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            publish_time_str = "未知时间"

                        # 构建帖子数据
                        note_data = {
                            "帖子ID": photo_id,
                            "帖子名称": title,
                            "发布时间": publish_time_str,
                            "发布时间戳": publish_time,
                            "曝光": 0,  # 接口未提供，暂设为0
                            "观看": int(play_count),
                            "点赞": int(like_count),
                            "评论": int(comment_count),
                            "分享": 0,  # 接口未提供，暂设为0
                            "收藏": int(collect_count),
                            "关注数": int(follow_count),  # 新增字段
                            "封面点击率": '0%',  # 接口未提供
                            "人均观看时长": 0,  # 接口未提供
                            "完播率": f"{fpr:.2%}",
                            "是否视频": "是" if video else "否",
                            "封面图": item.get("cover", ""),
                            "播放地址": item.get("playUrl", ""),
                            "视频时长(ms)": item.get("duration", 0)
                        }

                        # 如果有标签信息
                        photo_status_tags = item.get("photoStatusTags", [])
                        if photo_status_tags:
                            note_data["状态标签"] = photo_status_tags[0].get("tagText", "")

                        print(f"采集到: {title} | 观看: {play_count} | 点赞: {like_count} | 评论: {comment_count}")
                        notes_datas.append(note_data)

                    # 判断是否还有更多数据
                    if len(photo_items) < page_size or page_num >= total_pages - 1:
                        has_more = False
                    else:
                        page_num += 1
                        time.sleep(1)  # 避免请求过快

                else:
                    print(f"请求失败: {result.get('message', '未知错误')}")
                    break
            else:
                print(f"HTTP请求失败: {response.status_code}")
                break

        except Exception as e:
            print(f"采集第{page_num + 1}页时出错: {str(e)}")
            break

    print(f"采集完成，共采集到 {len(notes_datas)} 个帖子")
    return notes_datas


if __name__ == '__main__':
    # spider_ks_accounts()
    spider_ks_notes()