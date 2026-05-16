from models_user import User, get_session as UserSession
from werkzeug.security import generate_password_hash

session = UserSession()
try:
    # 检查是否已存在
    existing = session.query(User).filter_by(username='admin').first()
    if existing:
        print("⚠️ admin 账户已存在")
    else:
        admin_user = User(
            username='admin',
            email='admin@example.com',
            phone='',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        session.add(admin_user)
        session.commit()
        print("✅ admin 账户创建成功！")
        print("用户名：admin")
        print("密码：admin123")
except Exception as e:
    print(f"❌ 创建失败：{e}")
    session.rollback()
finally:
    session.close()
