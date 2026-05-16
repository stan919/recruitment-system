"""
更新 admin 账号为超级管理员
"""
# 先加载环境变量
import load_env
from models_user import User, get_session as UserSession

session = UserSession()
try:
    admin_user = session.query(User).filter_by(username='admin').first()
    if not admin_user:
        print("❌ admin 账户不存在")
    else:
        admin_user.is_admin = True
        session.commit()
        print("✅ admin 账户已升级为超级管理员！")
        print(f"   用户名：{admin_user.username}")
        print(f"   is_admin：{admin_user.is_admin}")
except Exception as e:
    session.rollback()
    print(f"❌ 更新失败：{e}")
finally:
    session.close()
