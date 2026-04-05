"""
用户认证管理器
"""
from models_user import User, get_session as UserSession
from werkzeug.security import generate_password_hash, check_password_hash


class AuthManager:
    """用户认证管理类"""
    
    @staticmethod
    def authenticate(username, password):
        """
        验证用户登录
        :param username: 用户名
        :param password: 密码
        :return: (user, error_message)
        """
        session = UserSession()
        try:
            user = session.query(User).filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if not user:
                return None, '用户不存在'
            
            if not check_password_hash(user.password_hash, password):
                return None, '密码错误'
            
            return user, None
        finally:
            session.close()
    
    @staticmethod
    def create_user(username, email, password, phone=''):
        """
        创建新用户
        :param username: 用户名
        :param email: 邮箱
        :param password: 密码
        :param phone: 手机号
        :return: (user, error_message)
        """
        session = UserSession()
        try:
            # 检查用户名是否已存在
            if session.query(User).filter_by(username=username).first():
                return None, '用户名已存在'
            
            # 检查邮箱是否已存在
            if session.query(User).filter_by(email=email).first():
                return None, '邮箱已被注册'
            
            # 创建新用户
            user = User(
                username=username,
                email=email,
                phone=phone if phone else None,
                password_hash=generate_password_hash(password)
            )
            
            session.add(user)
            session.commit()
            
            return user, None
        except Exception as e:
            session.rollback()
            return None, str(e)
        finally:
            session.close()
