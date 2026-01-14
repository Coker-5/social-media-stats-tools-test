from models.NoteInfo import db, NoteInfo
from datetime import datetime

class BaseOperator:
    """基础操作类，封装通用逻辑"""
    model = None

    @classmethod
    def get_db(cls):
        return db

class NotesInfoOperator(BaseOperator):
    """视频表专项操作"""
    model = NoteInfo

    @classmethod
    def batch_upsert(cls, video_list, platform):
        """批量更新或插入帖子数据"""
        if not video_list:
            return False

        data_to_insert = []
        for v in video_list:
            data_to_insert.append({
                'platform': platform,
                'item_id_plain': v['item_id_plain'],
                'title': v.get('title', ''),
                'publish_time': v['publish_time'],
                'item_link': v.get('item_link', ''),
                'comment_count': v.get('comment_count', 0),
                'updated_at': datetime.now()
            })

        # 使用原子操作和冲突处理
        with db.atomic():
            for i in range(0, len(data_to_insert), 50):
                batch = data_to_insert[i:i+50]
                cls.model.insert_many(batch).on_conflict(
                    conflict_target=[cls.model.platform, cls.model.item_id],
                    preserve=[cls.model.title, cls.model.comment_count, cls.model.update_time]
                ).execute()

    @classmethod
    def get_pending_videos(cls, platform, days=1):
        """获取指定平台近期需要更新评论的视频列表"""
        return cls.model.select().where(cls.model.platform == platform)
