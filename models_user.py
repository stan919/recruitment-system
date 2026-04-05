"""
用户模型
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import config

# 使用全局引擎（由 app.py 创建）
Base = declarative_base()

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


class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    email = Column(String(100), unique=True, nullable=False, comment='邮箱')
    phone = Column(String(20), unique=True, nullable=True, default=None, comment='手机号')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    avatar = Column(String(255), nullable=True, comment='头像 URL')
    major = Column(String(50), nullable=True, comment='专业')
    education = Column(String(50), nullable=True, comment='学历')
    graduation_year = Column(Integer, nullable=True, comment='毕业年份')
    target_city = Column(String(50), nullable=True, comment='期望工作城市')
    career_preference = Column(String(200), nullable=True, comment='职业偏好')
    is_active = Column(Boolean, default=True, comment='是否激活')
    is_admin = Column(Boolean, default=False, comment='是否管理员')
    is_company_admin = Column(Boolean, default=False, comment='是否企业管理员')
    company_name = Column(String(100), nullable=True, comment='所属企业')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """将对象转为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'major': self.major,
            'education': self.education,
            'graduation_year': self.graduation_year,
            'target_city': self.target_city,
            'career_preference': self.career_preference,
            'avatar': self.avatar,
            'is_admin': self.is_admin,
            'is_company_admin': self.is_company_admin,
            'company_name': self.company_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Favorite(Base):
    """收藏职位表"""
    __tablename__ = 'favorites'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户 ID')
    job_id = Column(Integer, comment='职位 ID')
    note = Column(String(500), comment='备注')
    created_at = Column(DateTime, default=datetime.now, comment='收藏时间')
    
    # 关联关系
    user = relationship("User", backref="favorites")
    
    def __repr__(self):
        return f'<Favorite {self.job_id} by User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_id': self.job_id,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Application(Base):
    """投递记录表"""
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户 ID')
    job_id = Column(Integer, comment='职位 ID')
    status = Column(String(20), default='submitted', comment='状态：submitted/viewed/interview/offer/rejected')
    applied_at = Column(DateTime, default=datetime.now, comment='投递时间')
    notes = Column(Text, comment='备注')
    
    user = relationship("User", backref="applications")
    
    def __repr__(self):
        return f'<Application {self.job_id} by User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_id': self.job_id,
            'status': self.status,
            'notes': self.notes,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None
        }


class ViewHistory(Base):
    """浏览历史表"""
    __tablename__ = 'view_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户 ID')
    job_id = Column(Integer, comment='职位 ID')
    viewed_at = Column(DateTime, default=datetime.now, comment='浏览时间')
    
    user = relationship("User", backref="view_history")
    
    def __repr__(self):
        return f'<ViewHistory {self.job_id} by User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_id': self.job_id,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None
        }
