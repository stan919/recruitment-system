"""
职位数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from models_user import Base


class JobPosition(Base):
    """职位表"""
    __tablename__ = 'job_positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='职位 ID')
    job_name = Column(String(100), nullable=False, comment='职位名称')
    company_name = Column(String(200), nullable=False, comment='公司名称')
    min_salary = Column(Integer, comment='最低薪资（元/月）')
    max_salary = Column(Integer, comment='最高薪资（元/月）')
    salary_text = Column(String(50), comment='薪资文本')
    city = Column(String(50), nullable=False, comment='城市')
    district = Column(String(50), comment='区县')
    experience = Column(String(50), comment='经验要求')
    education = Column(String(50), comment='学历要求')
    skill_tags = Column(String(500), comment='技能标签')
    description = Column(Text, comment='职位描述')
    industry = Column(String(100), comment='行业')
    company_size = Column(String(50), comment='公司规模')
    source = Column(String(50), default='manual', comment='数据来源')
    is_campus = Column(Integer, default=0, comment='是否校招')
    publish_date = Column(String(20), comment='发布日期')
    crawl_time = Column(DateTime, default=datetime.now, comment='爬取时间')
    status = Column(String(20), default='active', comment='状态：active-已上线，pending-待审核，inactive-已下线，rejected-已驳回')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'job_name': self.job_name,
            'company_name': self.company_name,
            'min_salary': self.min_salary,
            'max_salary': self.max_salary,
            'salary_text': self.salary_text,
            'city': self.city,
            'district': self.district,
            'experience': self.experience,
            'education': self.education,
            'skill_tags': self.skill_tags,
            'description': self.description,
            'industry': self.industry,
            'company_size': self.company_size,
            'source': self.source,
            'is_campus': bool(self.is_campus) if self.is_campus is not None else False,
            'publish_date': self.publish_date,
            'crawl_time': self.crawl_time.strftime('%Y-%m-%d %H:%M:%S') if self.crawl_time else None
        }
