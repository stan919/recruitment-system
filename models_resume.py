"""
简历模型
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import config

# 使用全局 Base（由 app.py 统一创建）
ResumeBase = declarative_base()

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


class Resume(ResumeBase):
    """简历表"""
    __tablename__ = 'resumes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, comment='用户 ID')
    
    # 基本信息
    name = Column(String(50), nullable=True, comment='姓名')
    phone = Column(String(20), nullable=True, comment='手机号')
    email = Column(String(100), nullable=True, comment='邮箱')
    
    # 教育经历
    education = Column(String(50), nullable=True, comment='学历')
    graduation_year = Column(Integer, nullable=True, comment='毕业年份')
    school = Column(String(100), nullable=True, comment='学校')
    major = Column(String(50), nullable=True, comment='专业')
    
    # 工作经历
    work_experience = Column(Text, nullable=True, comment='工作经历')
    project_experience = Column(Text, nullable=True, comment='项目经验')
    skills = Column(Text, nullable=True, comment='技能特长')
    
    # 自我介绍
    self_introduction = Column(Text, nullable=True, comment='自我介绍')
    
    # 期望工作
    expected_city = Column(String(50), nullable=True, comment='期望城市')
    expected_salary = Column(String(50), nullable=True, comment='期望薪资')
    career_preference = Column(String(200), nullable=True, comment='职业偏好')
    
    # 附件简历
    has_attachment = Column(Integer, default=0, comment='是否有附件：0-无，1-有')
    attachment_path = Column(String(255), nullable=True, comment='附件路径')
    attachment_name = Column(String(255), nullable=True, comment='附件原名')
    attachment_type = Column(String(20), nullable=True, comment='附件类型：pdf/word')
    
    # 状态
    is_complete = Column(Integer, default=0, comment='是否完善：0-不完善，1-完善')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f'<Resume {self.id} by User {self.user_id}>'
    
    def to_dict(self):
        """将对象转为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'education': self.education,
            'graduation_year': self.graduation_year,
            'school': self.school,
            'major': self.major,
            'work_experience': self.work_experience,
            'project_experience': self.project_experience,
            'skills': self.skills,
            'self_introduction': self.self_introduction,
            'expected_city': self.expected_city,
            'expected_salary': self.expected_salary,
            'career_preference': self.career_preference,
            'has_attachment': self.has_attachment,
            'attachment_name': self.attachment_name,
            'attachment_type': self.attachment_type,
            'is_complete': self.is_complete,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class JobApplication(ResumeBase):
    """职位申请表"""
    __tablename__ = 'job_applications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, comment='用户 ID')
    resume_id = Column(Integer, nullable=False, comment='简历 ID')
    job_id = Column(Integer, nullable=False, comment='职位 ID')
    job_name = Column(String(100), nullable=True, comment='职位名称')
    company_name = Column(String(100), nullable=True, comment='公司名称')

    # 申请快照（避免后续修改简历覆盖历史申请信息）
    applicant_name = Column(String(100), nullable=True, comment='申请时姓名快照')
    applicant_phone = Column(String(30), nullable=True, comment='申请时手机号快照')
    applicant_email = Column(String(120), nullable=True, comment='申请时邮箱快照')
    
    # 申请时填写的信息
    expected_salary = Column(String(50), nullable=True, comment='期望薪资')
    reason = Column(Text, nullable=True, comment='申请理由')
    other_info = Column(Text, nullable=True, comment='其他信息')
    
    # 状态
    status = Column(String(20), default='submitted', comment='状态：submitted/viewed/interview/offer/rejected')
    applied_at = Column(DateTime, default=datetime.now, comment='申请时间')
    notes = Column(Text, nullable=True, comment='备注')
    
    def __repr__(self):
        return f'<JobApplication {self.job_id} by User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'resume_id': self.resume_id,
            'job_id': self.job_id,
            'job_name': self.job_name,
            'company_name': self.company_name,
            'applicant_name': self.applicant_name,
            'applicant_phone': self.applicant_phone,
            'applicant_email': self.applicant_email,
            'expected_salary': self.expected_salary,
            'reason': self.reason,
            'status': self.status,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None
        }


# 创建表
def init_db():
    """初始化数据库表"""
    engine = get_engine()
    ResumeBase.metadata.create_all(engine)
    print("简历数据库表初始化完成")


if __name__ == '__main__':
    init_db()
