"""
检查企业管理员和申请记录的公司名是否匹配
"""
import load_env
from models_user import User, get_session as UserSession
from models_resume import JobApplication, ResumeSession

user_session = UserSession()
resume_session = ResumeSession()

try:
    # 1. 查看企业管理员的公司名
    print("=" * 60)
    print("企业管理员账号信息：")
    print("=" * 60)
    company_admins = user_session.query(User).filter_by(is_company_admin=True).all()
    for admin in company_admins:
        print(f"用户名：{admin.username}")
        print(f"公司名：{admin.company_name}")
        print(f"-" * 40)
    
    # 2. 查看申请记录的公司名
    print("\n" + "=" * 60)
    print("投递记录的公司名：")
    print("=" * 60)
    applications = resume_session.query(JobApplication).order_by(JobApplication.applied_at.desc()).limit(10).all()
    for app in applications:
        print(f"职位：{app.job_name}")
        print(f"公司名：{app.company_name}")
        print(f"-" * 40)
        
except Exception as e:
    print(f"错误：{e}")
finally:
    user_session.close()
    resume_session.close()
