"""
初始化企业管理员账户
"""
from models_user import User, get_session as UserSession
from werkzeug.security import generate_password_hash

def init_company_admin(username, email, password, company_name):
    """创建企业管理员账户"""
    session = UserSession()
    try:
        # 检查是否已存在
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            print(f"用户 {username} 已存在")
            return
        
        # 创建企业管理员
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_company_admin=True,
            company_name=company_name
        )
        
        session.add(user)
        session.commit()
        
        print(f"✅ 企业管理员创建成功！")
        print(f"   用户名：{username}")
        print(f"   邮箱：{email}")
        print(f"   企业：{company_name}")
        print(f"   密码：{password}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 创建失败：{e}")
    finally:
        session.close()


if __name__ == '__main__':
    # 创建示例企业管理员
    print("=" * 60)
    print("初始化企业管理员账户")
    print("=" * 60)
    
    # 示例 1: 腾讯科技
    init_company_admin(
        username='tencent_hr',
        email='hr@tencent.com',
        password='123456',
        company_name='腾讯科技'
    )
    
    # 示例 2: 阿里巴巴
    init_company_admin(
        username='alibaba_hr',
        email='hr@alibaba.com',
        password='123456',
        company_name='阿里巴巴'
    )
    
    # 示例 3: 字节跳动
    init_company_admin(
        username='bytedance_hr',
        email='hr@bytedance.com',
        password='123456',
        company_name='字节跳动'
    )
    
    print("=" * 60)
    print("完成！可以使用以上账号登录企业后台")
    print("登录时勾选【企业登录】选项")
    print("=" * 60)
