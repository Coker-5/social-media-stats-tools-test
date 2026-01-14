from peewee import *
from datetime import datetime

# 数据库连接配置 (建议从你的 config.json 读取)
db = PostgresqlDatabase(
    'your_db_name',
    user='your_user',
    password='your_password',
    host='localhost',
    port=5432
)


class BaseModel(Model):
    # 记录该条记录在数据库中创建的时间（仅插入时生成）
    created_time = DateTimeField(default=datetime.now, help_text="创建时间")
    # 记录该条记录最后一次更新的时间（每次保存都会刷新）
    updated_time = DateTimeField(default=datetime.now, help_text="更新时间")

    class Meta:
        database = db


class NoteInfo(BaseModel):
    # 核心标识
    account = TextField(help_text="账户名称")
    platform = CharField(max_length=20, help_text="平台名称")
    item_id = CharField(max_length=100, help_text="ID", unique=True)

    # 内容信息
    title = TextField(null=True, help_text="帖子标题")
    publish_time = DateTimeField(help_text="发布时间")
    item_link = TextField(null=True, help_text="帖子链接")

    comment_count = IntegerField(default=0, help_text="评论数")

    update_time = DateTimeField(default=datetime.now)

    class Meta:
        # 联合唯一索引：确保同一个平台下的同一个视频不会重复插入
        indexes = (
            (('platform', 'item_id_plain'), True),
        )


# 初始化表
def init_db():
    db.connect()
    db.create_tables([NoteInfo], safe=True)
    db.close()
