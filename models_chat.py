"""
聊天消息模型
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import config

# 使用全局 Base（由 app.py 统一创建）
ChatBase = declarative_base()

# 延迟导入 engine 和 Session，避免循环依赖
_engine = None
_Session = None

def get_engine():
    global _engine
    if _engine is None:
        DATABASE_URL = f"mysql+pymysql://{config.DATABASE_CONFIG['user']}:{config.DATABASE_CONFIG['password']}@{config.DATABASE_CONFIG['host']}:{config.DATABASE_CONFIG['port']}/{config.DATABASE_CONFIG['database']}?charset=utf8mb4"
        _engine = create_engine(DATABASE_URL, echo=False)
    return _engine

def get_session():
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine())
    return _Session()


class Conversation(ChatBase):
    """会话表"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, comment='用户 ID（求职者）')
    company_id = Column(Integer, nullable=False, default=0, comment='企业标识（公司管理员用户 ID）')
    company_name = Column(String(200), nullable=False, default='', comment='公司名称')
    job_id = Column(Integer, nullable=True, comment='职位 ID')
    job_name = Column(String(100), nullable=True, comment='职位名称')
    last_message_at = Column(DateTime, nullable=True, comment='最后消息时间')
    last_message_content = Column(Text, nullable=True, comment='最后消息内容')
    user_unread_count = Column(Integer, nullable=True, default=0, comment='用户未读数')
    company_unread_count = Column(Integer, nullable=True, default=0, comment='企业未读数')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'company_name': self.company_name,
            'job_id': self.job_id,
            'job_name': self.job_name,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'last_message_content': self.last_message_content,
            'user_unread_count': self.user_unread_count or 0,
            'company_unread_count': self.company_unread_count or 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }


class Message(ChatBase):
    """消息表"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False, comment='会话 ID')
    sender_type = Column(String(20), nullable=False, comment='发送者类型：user（求职者）/company（企业 HR）')
    sender_id = Column(Integer, nullable=False, comment='发送者 ID（user_id 或 company_user_id）')
    message_type = Column(String(20), nullable=True, default='text', comment='消息类型：text/file/interview')
    content = Column(Text, nullable=False, comment='消息内容')
    file_url = Column(String(500), nullable=True, comment='附件 URL')
    file_name = Column(String(255), nullable=True, comment='附件名称')
    file_size = Column(Integer, nullable=True, comment='附件大小（字节）')
    interview_job_id = Column(Integer, nullable=True, comment='面试职位 ID')
    interview_time = Column(DateTime, nullable=True, comment='面试时间')
    interview_location = Column(String(255), nullable=True, comment='面试地点')
    interview_notes = Column(Text, nullable=True, comment='面试备注')
    created_at = Column(DateTime, default=datetime.now, comment='发送时间')
    is_read = Column(Boolean, default=False, comment='是否已读')
    read_at = Column(DateTime, nullable=True, comment='已读时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_type': self.sender_type,
            'sender_id': self.sender_id,
            'message_type': self.message_type,
            'content': self.content,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'interview_job_id': self.interview_job_id,
            'interview_time': self.interview_time.isoformat() if self.interview_time else None,
            'interview_location': self.interview_location,
            'interview_notes': self.interview_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 创建表
def init_db():
    """初始化数据库表"""
    engine = get_engine()
    ChatBase.metadata.create_all(engine)
    print("聊天数据库表初始化完成")


if __name__ == '__main__':
    init_db()
