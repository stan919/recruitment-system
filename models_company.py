"""
公司模型
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import config

# 使用全局 Base（由 app.py 统一创建）
CompanyBase = declarative_base()

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


class Company(CompanyBase):
    """公司信息表"""
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(200), unique=True, nullable=False, comment='公司名称')
    
    # 基本信息
    english_name = Column(String(200), nullable=True, comment='英文名')
    short_name = Column(String(100), nullable=True, comment='简称')
    credit_code = Column(String(50), nullable=True, comment='统一社会信用代码/工商注册号')
    established_date = Column(Date, nullable=True, comment='成立时间')
    industry = Column(String(50), nullable=True, comment='行业分类')
    
    # 联系方式
    website = Column(String(200), nullable=True, comment='官网地址')
    phone = Column(String(20), nullable=True, comment='联系电话')
    email = Column(String(100), nullable=True, comment='联系邮箱')
    address = Column(String(500), nullable=True, comment='公司地址')
    
    # 介绍信息
    description = Column(Text, nullable=True, comment='企业简介')
    recruitment_manifesto = Column(Text, nullable=True, comment='招聘宣言')
    logo_path = Column(String(255), nullable=True, comment='Logo 路径')
    
    # 雇主品牌
    enable_employer_brand = Column(Boolean, default=False, comment='是否启用雇主品牌')
    culture_video_url = Column(String(500), nullable=True, comment='文化视频 URL')
    employee_stories = Column(Text, nullable=True, comment='员工故事')
    
    # 数据保留策略
    resume_retention_days = Column(Integer, default=365, comment='简历保存期限（天）')
    interview_record_archive_days = Column(Integer, default=180, comment='面试记录归档周期（天）')
    
    # 合规设置
    gdpr_compliance = Column(Boolean, default=False, comment='GDPR/个人信息保护法合规开关')
    consent_popup_enabled = Column(Boolean, default=True, comment='候选人同意书弹窗')
    data_export_enabled = Column(Boolean, default=True, comment='数据导出入口')
    data_deletion_enabled = Column(Boolean, default=True, comment='数据删除入口')
    
    # 审计日志
    audit_log_enabled = Column(Boolean, default=True, comment='审计日志开关')
    audit_log_retention_days = Column(Integer, default=90, comment='审计日志存储周期（天）')
    
    # 敏感字段脱敏
    phone_mask_enabled = Column(Boolean, default=True, comment='手机号脱敏')
    email_mask_enabled = Column(Boolean, default=False, comment='邮箱脱敏')
    
    # 系统字段
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f'<Company {self.company_name}>'
    
    def to_dict(self):
        """将对象转为字典"""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'english_name': self.english_name,
            'short_name': self.short_name,
            'credit_code': self.credit_code,
            'established_date': self.established_date.isoformat() if self.established_date else None,
            'industry': self.industry,
            'website': self.website,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'description': self.description,
            'recruitment_manifesto': self.recruitment_manifesto,
            'recruitment_declaration': self.recruitment_manifesto,
            'logo_path': self.logo_path,
            'enable_employer_brand': self.enable_employer_brand,
            'culture_video_url': self.culture_video_url,
            'employee_stories': self.employee_stories,
            'resume_retention_days': self.resume_retention_days,
            'interview_record_archive_days': self.interview_record_archive_days,
            'gdpr_compliance': self.gdpr_compliance,
            'consent_popup_enabled': self.consent_popup_enabled,
            'data_export_enabled': self.data_export_enabled,
            'data_deletion_enabled': self.data_deletion_enabled,
            'audit_log_enabled': self.audit_log_enabled,
            'audit_log_retention_days': self.audit_log_retention_days,
            'phone_mask_enabled': self.phone_mask_enabled,
            'email_mask_enabled': self.email_mask_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AuditLog(CompanyBase):
    """审计日志表"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, nullable=True, comment='公司 ID')
    user_id = Column(Integer, nullable=True, comment='用户 ID')
    action = Column(String(100), nullable=False, comment='操作类型')
    module = Column(String(50), nullable=True, comment='模块')
    details = Column(Text, nullable=True, comment='详细信息')
    ip_address = Column(String(50), nullable=True, comment='IP 地址')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    def __repr__(self):
        return f'<AuditLog {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'user_id': self.user_id,
            'action': self.action,
            'module': self.module,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# 创建表
def init_db():
    """初始化数据库表"""
    engine = get_engine()
    CompanyBase.metadata.create_all(engine)
    print("公司数据库表初始化完成")


if __name__ == '__main__':
    init_db()
