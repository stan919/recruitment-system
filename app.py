"""
职引未来 - 高校毕业生就业服务平台
极简版 - 仅保留主页和登录注册功能
"""
# 必须在最前面加载环境变量
import load_env

from flask import Flask, render_template, jsonify, request, session, redirect, url_for, Response
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from markupsafe import escape
from datetime import timedelta, datetime
from collections import defaultdict
import config
import os
from contextlib import contextmanager
from werkzeug.utils import secure_filename

# 导入用户数据库模型
from models_user import User, get_session as UserSession, Base as UserBase
from models_job import JobPosition
from models_resume import Resume, JobApplication, get_session as ResumeSession, init_db as init_resume_db
from models_company import Company, AuditLog, get_session as CompanySession, init_db as init_company_db
from auth import AuthManager

# 构建数据库 URL
DATABASE_URL = f"mysql+pymysql://{config.DATABASE_CONFIG['user']}:{config.DATABASE_CONFIG['password']}@{config.DATABASE_CONFIG['host']}:{config.DATABASE_CONFIG['port']}/{config.DATABASE_CONFIG['database']}?charset=utf8mb4"

# 创建数据库引擎（单例模式）
from sqlalchemy import create_engine, and_, inspect, text
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    echo=False
)
SessionLocal = scoped_session(sessionmaker(bind=engine))

# 配置日志
import logging
from logging.handlers import RotatingFileHandler
import os

# 确保日志目录存在
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志处理器
file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'app.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

# 添加控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

app = Flask(__name__)
app.config['SECRET_KEY'] = config.FLASK_CONFIG['SECRET_KEY']
app.config['DEBUG'] = config.FLASK_CONFIG['DEBUG']
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制文件大小为 16MB

# 添加日志配置
if app.config['DEBUG']:
    app.logger.addHandler(console_handler)
else:
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

# 启用 CORS
CORS(app)

# CSRF 保护已在 Flask 表单中通过 {{ form.csrf_token }} 实现
# API 使用 Session 认证，不需要额外的 CSRF 保护
# csrf = CSRFProtect()
# csrf.init_app(app)

# 初始化数据库表
try:
    UserBase.metadata.create_all(engine)
    init_resume_db()
    init_company_db()
    print("数据库表初始化完成")
except Exception as e:
    print(f"数据库初始化警告：{e}")


def ensure_database_compatibility():
    """兼容历史库结构：补齐代码依赖但旧库中缺失的关键字段。"""
    try:
        db_inspector = inspect(engine)
        columns_map = {
            table: {col['name'] for col in db_inspector.get_columns(table)}
            for table in ['companies', 'conversations', 'messages', 'job_applications']
            if db_inspector.has_table(table)
        }

        alter_sql = []

        company_columns = columns_map.get('companies', set())
        if 'recruitment_manifesto' not in company_columns:
            alter_sql.append(
                "ALTER TABLE companies ADD COLUMN recruitment_manifesto TEXT NULL COMMENT '招聘宣言'"
            )

        conversation_columns = columns_map.get('conversations', set())
        if 'company_name' not in conversation_columns:
            alter_sql.append(
                "ALTER TABLE conversations ADD COLUMN company_name VARCHAR(200) NOT NULL DEFAULT '' COMMENT '公司名称'"
            )
        if 'job_name' not in conversation_columns:
            alter_sql.append(
                "ALTER TABLE conversations ADD COLUMN job_name VARCHAR(100) NULL COMMENT '职位名称'"
            )

        message_columns = columns_map.get('messages', set())
        if 'message_type' not in message_columns:
            alter_sql.append(
                "ALTER TABLE messages ADD COLUMN message_type VARCHAR(20) NULL COMMENT '消息类型'"
            )

        application_columns = columns_map.get('job_applications', set())
        if 'applicant_name' not in application_columns:
            alter_sql.append(
                "ALTER TABLE job_applications ADD COLUMN applicant_name VARCHAR(100) NULL COMMENT '申请时姓名快照'"
            )
        if 'applicant_phone' not in application_columns:
            alter_sql.append(
                "ALTER TABLE job_applications ADD COLUMN applicant_phone VARCHAR(30) NULL COMMENT '申请时手机号快照'"
            )
        if 'applicant_email' not in application_columns:
            alter_sql.append(
                "ALTER TABLE job_applications ADD COLUMN applicant_email VARCHAR(120) NULL COMMENT '申请时邮箱快照'"
            )

        if alter_sql:
            with engine.begin() as conn:
                for stmt in alter_sql:
                    conn.execute(text(stmt))
            print(f"数据库兼容性修复完成，共执行 {len(alter_sql)} 条 DDL")

        # 旧数据回填：将历史申请中为空的快照字段补齐并固定，避免后续受简历改动影响
        if db_inspector.has_table('job_applications') and db_inspector.has_table('resumes'):
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE job_applications ja
                    LEFT JOIN resumes r ON ja.resume_id = r.id
                    LEFT JOIN users u ON ja.user_id = u.id
                    SET
                        ja.applicant_name = COALESCE(ja.applicant_name, r.name, u.username),
                        ja.applicant_phone = COALESCE(ja.applicant_phone, r.phone, u.phone),
                        ja.applicant_email = COALESCE(ja.applicant_email, r.email, u.email)
                    WHERE
                        ja.applicant_name IS NULL
                        OR ja.applicant_phone IS NULL
                        OR ja.applicant_email IS NULL
                """))
    except Exception as e:
        print(f"数据库兼容性修复警告：{e}")


ensure_database_compatibility()


# 速率限制 - 记录登录尝试
login_attempts = defaultdict(list)
RATE_LIMIT_WINDOW = 300  # 5 分钟
MAX_LOGIN_ATTEMPTS = 10  # 最多 10 次尝试

# ==================== 工具函数 ====================

@contextmanager
def get_db_session():
    """数据库会话上下文管理器"""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def get_actual_city(city_code):
    """获取实际城市名"""
    return config.CITY_MAPPING.get(city_code, city_code)


def get_profession_keyword(profession):
    """获取专业关键词"""
    return config.PROFESSION_KEYWORDS.get(profession, '')


def get_redirect_by_session_role():
    """根据当前登录模式返回默认跳转地址。"""
    if session.get('is_admin'):
        return '/admin'
    if session.get('is_company'):
        return '/company'
    return '/'


# ==================== 认证相关 API ====================

@app.route('/health')
def health_check():
    """健康检查 API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/login')
def login():
    """登录页面"""
    return render_template('login.html')


@app.route('/register')
def register():
    """注册页面"""
    return render_template('register.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    """用户登录 API"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    is_company = data.get('is_company', False)
    is_admin = data.get('is_admin', False)
    remember = data.get('remember', False)
    
    if not username or not password:
        return jsonify({'success': False, 'message': '请输入用户名和密码'}), 400
    
    # 速率限制检查
    now = datetime.now()
    # 清理过期的记录
    login_attempts[username] = [t for t in login_attempts[username] if (now - t).total_seconds() < RATE_LIMIT_WINDOW]
    
    # 检查是否超过限制
    if len(login_attempts[username]) >= MAX_LOGIN_ATTEMPTS:
        return jsonify({'success': False, 'message': '尝试次数过多，请稍后再试'}), 429
    
    user, error = AuthManager.authenticate(username, password)
    
    if user:
        # 登录成功后清空该账号的失败计数，避免误触发限流
        login_attempts.pop(username, None)

        # 如果是企业登录，检查是否为企业管埋员
        if is_company and not user.is_company_admin:
            return jsonify({'success': False, 'message': '该账号不是企业管理员'}), 401
        
        # 如果是管理员登录，检查是否为超级管埋员
        if is_admin and not user.is_admin:
            return jsonify({'success': False, 'message': '该账号不是超级管理员'}), 401
        
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        session['is_company'] = is_company
        session['is_admin'] = is_admin
        
        if remember:
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=30)
        
        # 根据登录类型重定向到不同页面
        if is_admin:
            redirect_url = '/admin'
        elif is_company:
            redirect_url = '/company'
        else:
            redirect_url = '/'
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': user.to_dict(),
            'redirect': redirect_url
        })
    else:
        # 仅对失败登录计数
        login_attempts[username].append(now)
        return jsonify({'success': False, 'message': error or '登录失败'}), 401


@app.route('/api/register', methods=['POST'])
def api_register():
    """用户注册 API"""
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'success': False, 'message': '请填写必填项'}), 400
    
    if len(username) < 3 or len(username) > 20:
        return jsonify({'success': False, 'message': '用户名长度必须在 3-20 个字符之间'}), 400
    
    if len(password) < 8:
        return jsonify({'success': False, 'message': '密码长度至少 8 位'}), 400
    
    user, error = AuthManager.create_user(username, email, password, phone)
    
    if user:
        return jsonify({'success': True, 'message': '注册成功'})
    else:
        return jsonify({'success': False, 'message': error or '注册失败'}), 400


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """用户登出 API"""
    session.clear()
    return jsonify({'success': True, 'message': '已退出登录'})


@app.route('/api/user')
def api_user():
    """获取当前用户信息"""
    if 'user_id' in session:
        with get_db_session() as db_session:
            user = db_session.query(User).filter_by(id=session['user_id']).first()
            if user:
                return jsonify({
                    'logged_in': True,
                    'user': user.to_dict(),
                    'session_flags': {
                        'is_company': bool(session.get('is_company', False)),
                        'is_admin': bool(session.get('is_admin', False))
                    }
                })
    
    return jsonify({'logged_in': False}), 401


# ==================== 主页 ====================

@app.route('/')
def index():
    """首页 - 展示宣传主页"""
    # 获取热门职位（用于搜索）
    jobs = []
    try:
        with get_db_session() as db_session:
            jobs = db_session.query(JobPosition).filter_by(status='active').limit(20).all()
    except Exception as e:
        print(f"获取职位失败：{e}")
    
    return render_template('home.html', jobs=jobs)


@app.route('/dashboard')
def dashboard():
    """主页 - 跳转到宣传主页"""
    return redirect(url_for('index'))


@app.route('/insights')
def insights():
    """数据洞察页面"""
    return render_template('insights.html')


@app.route('/jobs/search')
def job_search():
    """职位搜索页面"""
    # 获取搜索参数
    keyword = request.args.get('keyword', '').strip()
    city = request.args.get('city', '').strip()
    profession = request.args.get('profession', '').strip()
    min_salary = request.args.get('min_salary', type=int)
    max_salary = request.args.get('max_salary', type=int)
    
    # 如果有搜索参数，直接查询结果
    jobs = []
    if keyword or city or profession or min_salary or max_salary:
        try:
            db_session = SessionLocal()
            
            # 构建查询条件
            conditions = []
            
            # 关键词搜索
            if keyword:
                conditions.append(
                    (JobPosition.job_name.like(f'%{keyword}%')) |
                    (JobPosition.company_name.like(f'%{keyword}%')) |
                    (JobPosition.description.like(f'%{keyword}%')) |
                    (JobPosition.skill_tags.like(f'%{keyword}%'))
                )
            
            # 城市筛选
            if city:
                actual_city = get_actual_city(city)
                conditions.append(JobPosition.city == actual_city)
            
            # 专业方向筛选（通过技能标签）
            if profession:
                keyword_text = get_profession_keyword(profession)
                if keyword_text:
                    conditions.append(
                        (JobPosition.skill_tags.like(f'%{keyword_text}%')) |
                        (JobPosition.job_name.like(f'%{keyword_text}%'))
                    )
            
            # 薪资范围
            if min_salary:
                conditions.append(JobPosition.min_salary >= min_salary)
            if max_salary:
                conditions.append(JobPosition.max_salary <= max_salary)
            
            # 查询职位
            query = db_session.query(JobPosition).filter(JobPosition.status == 'active')
            if conditions:
                query = query.filter(and_(*conditions))
            
            jobs = query.order_by(JobPosition.id.desc()).limit(100).all()
            
            # 转换为字典
            jobs = [{
                'id': job.id,
                'job_name': job.job_name,
                'company_name': job.company_name,
                'city': job.city,
                'education': job.education,
                'experience': job.experience,
                'min_salary': job.min_salary,
                'max_salary': job.max_salary,
                'skill_tags': job.skill_tags,
            } for job in jobs]
            
            db_session.close()
        except Exception as e:
            print(f"获取职位失败：{e}")
        finally:
            db_session.close()
    
    return render_template('job_search.html', jobs=jobs)


@app.route('/job/<int:job_id>')
def job_detail(job_id):
    """职位详情页面"""
    return render_template('job_detail.html', job_id=job_id)


@app.route('/api/jobs/search')
def search_jobs():
    """职位搜索 API - 支持多条件筛选"""
    keyword = request.args.get('keyword', '').strip()
    city = request.args.get('city', '').strip()
    profession = request.args.get('profession', '').strip()
    education = request.args.get('education', '').strip()
    experience = request.args.get('experience', '').strip()
    min_salary = request.args.get('min_salary', type=int)
    max_salary = request.args.get('max_salary', type=int)
    
    try:
        db_session = SessionLocal()
        
        # 构建查询条件
        conditions = []
        
        # 关键词搜索（职位名、公司名、描述、技能）
        if keyword:
            conditions.append(
                (JobPosition.job_name.like(f'%{keyword}%')) |
                (JobPosition.company_name.like(f'%{keyword}%')) |
                (JobPosition.description.like(f'%{keyword}%')) |
                (JobPosition.skill_tags.like(f'%{keyword}%'))
            )
        
        # 城市筛选
        if city:
            actual_city = get_actual_city(city)
            conditions.append(JobPosition.city == actual_city)
        
        # 专业方向筛选（通过技能标签）
        if profession:
            keyword_text = get_profession_keyword(profession)
            if keyword_text:
                conditions.append(
                    (JobPosition.skill_tags.like(f'%{keyword_text}%')) |
                    (JobPosition.job_name.like(f'%{keyword_text}%'))
                )
        
        # 学历要求
        if education:
            conditions.append(JobPosition.education == education)
        
        # 经验要求
        if experience:
            conditions.append(JobPosition.experience == experience)
        
        # 薪资范围
        if min_salary:
            conditions.append(JobPosition.min_salary >= min_salary)
        if max_salary:
            conditions.append(JobPosition.max_salary <= max_salary)
        
        # 查询职位
        query = db_session.query(JobPosition).filter(JobPosition.status == 'active')
        if conditions:
            query = query.filter(and_(*conditions))
        
        jobs = query.order_by(JobPosition.id.desc()).limit(100).all()
        
        result = [{
            'id': job.id,
            'job_name': job.job_name,
            'company_name': job.company_name,
            'city': job.city,
            'education': job.education,
            'experience': job.experience,
            'min_salary': job.min_salary,
            'max_salary': job.max_salary,
            'skill_keywords': job.skill_tags,
        } for job in jobs]
        
        db_session.close()
        return jsonify({'success': True, 'jobs': result, 'total': len(result)})
        
    except Exception as e:
        print(f"搜索职位失败：{e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db_session.close()


@app.route('/api/jobs/<int:job_id>')
def get_job_detail(job_id):
    """获取单个职位详情 API"""
    try:
        db_session = SessionLocal()
        
        job = db_session.query(JobPosition).filter_by(id=job_id).first()
        
        if not job:
            return jsonify({'success': False, 'message': '职位不存在'}), 404

        # 非活跃职位默认不对普通访问者暴露，仅管理员/企业模式可查看
        if job.status != 'active' and not (session.get('is_admin') or session.get('is_company')):
            return jsonify({'success': False, 'message': '职位不存在'}), 404
        
        result = {
            'id': job.id,
            'job_name': job.job_name,
            'company_name': job.company_name,
            'min_salary': job.min_salary,
            'max_salary': job.max_salary,
            'salary_text': job.salary_text,
            'city': job.city,
            'district': job.district,
            'experience': job.experience,
            'education': job.education,
            'skill_tags': job.skill_tags,
            'description': job.description,
            'industry': job.industry,
            'company_size': job.company_size,
            'source': job.source,
            'is_campus': bool(job.is_campus),
            'publish_date': job.publish_date,
            'crawl_time': job.crawl_time.strftime('%Y-%m-%d %H:%M:%S') if job.crawl_time else None
        }
        
        db_session.close()
        return jsonify({'success': True, 'job': result})
        
    except Exception as e:
        print(f"获取职位详情失败：{e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db_session.close()


@app.route('/applications')
def applications():
    """投递记录页面——仅普通用户访问"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 使用本次登录模式判断门户，避免跨角色登录后误跳转登录页
    if session.get('is_admin'):
        return redirect('/admin')
    if session.get('is_company'):
        return redirect('/company')
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_active:
            session.clear()
            return redirect('/login?message=登录已失效，请重新登录')
    
    return render_template('applications.html')


@app.route('/profile')
def profile():
    """个人中心页面——仅普通用户访问"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 使用本次登录模式判断门户，避免跨角色登录后误跳转登录页
    if session.get('is_admin'):
        return redirect('/admin')
    if session.get('is_company'):
        return redirect('/company')
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_active:
            session.clear()
            return redirect('/login?message=登录已失效，请重新登录')
        
        if user:
            with get_db_session() as resume_session:
                # 获取投递记录数量
                applications_count = resume_session.query(JobApplication).filter_by(
                    user_id=session['user_id']
                ).count()
                
                return render_template('profile.html', 
                                       user=user,
                                       applications_count=applications_count)
    
    return redirect(url_for('login'))


@app.route('/admin')
def admin_panel():
    """管理员后台"""
    if 'user_id' not in session:
        return redirect('/login')
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return redirect('/login')
        
        return render_template('admin.html')


@app.route('/api/account/settings', methods=['POST'])
def account_settings():
    """账户设置 API"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    graduation_year = data.get('graduation_year')
    education = data.get('education', '')
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    # 验证必填项
    if not username or not email:
        return jsonify({'success': False, 'message': '用户名和邮箱为必填项'}), 400
    
    if len(username) < 3 or len(username) > 20:
        return jsonify({'success': False, 'message': '用户名长度必须在 3-20 个字符之间'}), 400
    
    from werkzeug.security import check_password_hash, generate_password_hash
    
    user_session = UserSession()
    try:
        user = user_session.query(User).filter_by(id=session['user_id']).first()
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 检查用户名是否已被其他用户使用
        existing_user = user_session.query(User).filter(
            User.username == username,
            User.id != session['user_id']
        ).first()
        if existing_user:
            return jsonify({'success': False, 'message': '用户名已被使用'}), 400
        
        # 检查邮箱是否已被其他用户使用
        existing_email = user_session.query(User).filter(
            User.email == email,
            User.id != session['user_id']
        ).first()
        if existing_email:
            return jsonify({'success': False, 'message': '邮箱已被使用'}), 400
        
        # 如果要修改密码，验证当前密码
        if current_password and new_password:
            if not check_password_hash(user.password_hash, current_password):
                return jsonify({'success': False, 'message': '当前密码错误'}), 400
            
            if len(new_password) < 8:
                return jsonify({'success': False, 'message': '新密码长度至少 8 位'}), 400
            
            # 更新密码
            user.password_hash = generate_password_hash(new_password)
        
        # 更新用户信息
        user.username = username
        user.email = email
        user.phone = phone if phone else None
        user.graduation_year = int(graduation_year) if graduation_year else None
        user.education = education if education else None
        
        user_session.commit()
        
        # 更新 session 中的用户名
        session['username'] = user.username
        session['email'] = user.email
        
        return jsonify({'success': True, 'message': '保存成功'})
        
    except Exception as e:
        print(f"保存账户设置失败：{e}")
        return jsonify({'success': False, 'message': '保存失败，请重试'}), 500
    finally:
        user_session.close()


# ==================== 简历相关 API ====================

@app.route('/api/resume', methods=['GET'])
def get_resume():
    """获取用户简历——仅普通用户"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 检查是否为管理员或企业 HR
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if user and (user.is_company_admin or user.is_admin):
            return jsonify({'success': False, 'message': '未注册或者账号密码错误'}), 403
    
    resume_session = ResumeSession()
    try:
        resume = resume_session.query(Resume).filter_by(user_id=session['user_id']).first()
        if resume:
            return jsonify({'success': True, 'resume': resume.to_dict()})
        else:
            return jsonify({'success': True, 'resume': None})
    except Exception as e:
        print(f"获取简历失败：{e}")
        return jsonify({'success': False, 'message': '获取简历失败'}), 500
    finally:
        resume_session.close()


@app.route('/api/resume', methods=['POST'])
def save_resume():
    """保存/更新简历——仅普通用户"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 检查是否为管理员或企业 HR
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if user and (user.is_company_admin or user.is_admin):
            return jsonify({'success': False, 'message': '未注册或者账号密码错误'}), 403
    
    data = request.get_json()
    resume_session = ResumeSession()
    try:
        resume = resume_session.query(Resume).filter_by(user_id=session['user_id']).first()
        
        if not resume:
            # 创建新简历
            resume = Resume(user_id=session['user_id'])
            resume_session.add(resume)
        
        # 更新简历信息
        resume.name = data.get('name') or ''
        resume.phone = data.get('phone') or ''
        resume.email = data.get('email') or ''
        resume.education = data.get('education') or ''
        resume.graduation_year = data.get('graduation_year') or None
        resume.school = data.get('school') or ''
        resume.major = data.get('major') or ''
        resume.work_experience = data.get('work_experience') or ''
        resume.project_experience = data.get('project_experience') or ''
        resume.skills = data.get('skills') or ''
        resume.self_introduction = data.get('self_introduction') or ''
        resume.expected_city = data.get('expected_city') or ''
        resume.expected_salary = data.get('expected_salary') or ''
        resume.career_preference = data.get('career_preference') or ''
        
        # 检查简历是否完善（只要有基本信息就算完善）
        if resume.name and resume.phone and resume.email:
            resume.is_complete = 1
        
        resume_session.commit()
        
        return jsonify({'success': True, 'message': '简历保存成功', 'resume': resume.to_dict()})
    except Exception as e:
        resume_session.rollback()
        print(f"保存简历失败：{e}")
        return jsonify({'success': False, 'message': '保存失败'}), 500
    finally:
        resume_session.close()


@app.route('/api/resume/upload', methods=['POST'])
def upload_resume():
    """上传简历附件——仅普通用户"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 检查是否为管理员或企业 HR
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if user and (user.is_company_admin or user.is_admin):
            return jsonify({'success': False, 'message': '未注册或者账号密码错误'}), 403
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    
    # 检查文件大小（最大 10MB）
    file.seek(0, 2)  # 移动到文件末尾
    file_size = file.tell()
    file.seek(0)  # 重置文件指针
    
    if file_size > 10 * 1024 * 1024:
        return jsonify({'success': False, 'message': '文件大小不能超过 10MB'}), 400
    
    # 检查文件类型
    allowed_extensions = {'pdf', 'doc', 'docx'}
    original_filename = file.filename
    if '.' not in original_filename:
        return jsonify({'success': False, 'message': '无效的文件名'}), 400
    
    ext = original_filename.rsplit('.', 1)[1].lower()
    
    if ext not in allowed_extensions:
        return jsonify({'success': False, 'message': '仅支持 PDF 和 Word 格式'}), 400
    
    # 验证文件内容（检查文件头）
    file_bytes = file.read(1024)  # 读取前 1KB
    file.seek(0)  # 重置文件指针
    
    # PDF 文件头：%PDF
    # DOCX 文件头：PK (ZIP 格式)
    # DOC 文件头：\xD0\xCF\x11\xE0
    if ext == 'pdf' and not file_bytes.startswith(b'%PDF'):
        return jsonify({'success': False, 'message': '无效的 PDF 文件'}), 400
    elif ext in ['docx'] and not file_bytes.startswith(b'PK'):
        return jsonify({'success': False, 'message': '无效的 Word 文件'}), 400
    
    # 创建上传目录
    basedir = os.path.abspath(os.path.dirname(__file__))
    upload_dir = os.path.join(basedir, 'uploads', 'resumes')
    os.makedirs(upload_dir, exist_ok=True)
    
    # 保存文件（使用安全文件名）
    import uuid
    safe_original = secure_filename(original_filename)  # 清理原始文件名
    if not safe_original:
        safe_original = 'resume_' + str(uuid.uuid4().hex)[:8] + '.' + ext
    unique_filename = f"{uuid.uuid4().hex}_{safe_original}"
    filepath = os.path.join(upload_dir, unique_filename)
    file.save(filepath)
    
    # 更新简历
    resume_session = ResumeSession()
    try:
        resume = resume_session.query(Resume).filter_by(user_id=session['user_id']).first()
        
        if not resume:
            resume = Resume(user_id=session['user_id'])
            resume_session.add(resume)
        
        resume.has_attachment = 1
        resume.attachment_path = filepath
        resume.attachment_name = original_filename
        resume.attachment_type = ext
        resume_session.commit()
        
        return jsonify({'success': True, 'message': '上传成功', 'filename': original_filename})
    except Exception as e:
        resume_session.rollback()
        print(f"上传简历失败：{e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': '上传失败'}), 500
    finally:
        resume_session.close()


@app.route('/api/resume/attachment', methods=['DELETE'])
def delete_resume_attachment():
    """删除简历附件"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    resume_session = ResumeSession()
    try:
        resume = resume_session.query(Resume).filter_by(user_id=session['user_id']).first()
        
        if not resume:
            return jsonify({'success': False, 'message': '没有简历可删除'}), 404
        
        # 删除文件
        if resume.attachment_path and os.path.exists(resume.attachment_path):
            try:
                os.remove(resume.attachment_path)
            except Exception as e:
                print(f"删除文件失败：{e}")
        
        # 更新数据库
        resume.has_attachment = 0
        resume.attachment_path = None
        resume.attachment_name = None
        resume.attachment_type = None
        resume_session.commit()
        
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        resume_session.rollback()
        print(f"删除简历失败：{e}")
        return jsonify({'success': False, 'message': '删除失败'}), 500
    finally:
        resume_session.close()


@app.route('/api/resume/attachment/preview')
def preview_resume_attachment():
    """预览简历附件"""
    if 'user_id' not in session:
        return redirect('/login')
    
    resume_session = ResumeSession()
    try:
        resume = resume_session.query(Resume).filter_by(user_id=session['user_id']).first()
        
        if not resume or not resume.attachment_path:
            return jsonify({'error': '没有简历'}), 404
        
        # 检查文件是否存在
        if not os.path.exists(resume.attachment_path):
            return jsonify({'error': '文件不存在'}), 404
        
        # 读取文件并返回
        with open(resume.attachment_path, 'rb') as f:
            file_data = f.read()
        
        # 根据文件类型设置 MIME
        if resume.attachment_type == 'pdf':
            mime_type = 'application/pdf'
        elif resume.attachment_type in ['doc', 'docx']:
            mime_type = 'application/msword' if resume.attachment_type == 'doc' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            mime_type = 'application/octet-stream'
        
        from flask import Response
        return Response(
            file_data,
            mimetype=mime_type,
            headers={
                'Content-Disposition': 'inline; filename="resume.pdf"'
            }
        )
    except Exception as e:
        print(f"预览简历失败：{e}")
        return jsonify({'error': '预览失败'}), 500
    finally:
        resume_session.close()


@app.route('/api/resume/download/<int:resume_id>')
def download_resume_by_id(resume_id):
    """根据 ID 下载简历（用于企业管理员）"""
    if 'user_id' not in session:
        return redirect('/login')
    
    resume_session = ResumeSession()
    try:
        resume = resume_session.query(Resume).filter_by(id=resume_id).first()
        
        if not resume or not resume.attachment_path:
            return jsonify({'error': '简历不存在'}), 404
        
        # 检查文件是否存在
        if not os.path.exists(resume.attachment_path):
            return jsonify({'error': '文件不存在'}), 404
        
        from flask import send_file
        return send_file(
            resume.attachment_path,
            as_attachment=True,
            download_name=resume.attachment_name or 'resume.pdf'
        )
    except Exception as e:
        print(f"下载简历失败：{e}")
        return jsonify({'error': '下载失败'}), 500
    finally:
        resume_session.close()


@app.route('/api/resume/attachment/download')
def download_resume_attachment():
    """下载简历附件——仅普通用户"""
    if 'user_id' not in session:
        return redirect('/login')
    
    # 检查是否为管理员或企业 HR
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if user and (user.is_company_admin or user.is_admin):
            return jsonify({'error': '未注册或者账号密码错误'}), 403
    
    resume_session = ResumeSession()
    try:
        resume = resume_session.query(Resume).filter_by(user_id=session['user_id']).first()
        
        if not resume or not resume.attachment_path:
            return jsonify({'error': '没有简历'}), 404
        
        # 检查文件是否存在
        if not os.path.exists(resume.attachment_path):
            return jsonify({'error': '文件不存在'}), 404
        
        # 读取文件并返回
        with open(resume.attachment_path, 'rb') as f:
            file_data = f.read()
        
        # 获取原始文件名
        file_name = os.path.basename(resume.attachment_path)
        
        from flask import Response, send_file
        return send_file(
            resume.attachment_path,
            as_attachment=True,
            download_name=file_name
        )
    except Exception as e:
        print(f"下载简历失败：{e}")
        return jsonify({'error': '下载失败'}), 500
    finally:
        resume_session.close()


@app.route('/api/application/submit', methods=['POST'])
def submit_application():
    """提交职位申请——仅普通用户"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 检查是否为管理员或企业 HR
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if user and (user.is_company_admin or user.is_admin):
            return jsonify({'success': False, 'message': '未注册或者账号密码错误'}), 403
    
    data = request.get_json()
    job_id = data.get('job_id')
    job_name = data.get('job_name', '')
    company_name = data.get('company_name', '')
    expected_salary = data.get('expected_salary', '')
    reason = data.get('reason', '')
    other_info = data.get('other_info', '')
    
    if not job_id:
        return jsonify({'success': False, 'message': '职位信息不完整'}), 400
    
    resume_session = ResumeSession()
    try:
        # 获取用户简历
        resume = resume_session.query(Resume).filter_by(user_id=session['user_id']).first()
        
        if not resume:
            return jsonify({'success': False, 'message': '请先创建简历'}), 400
        
        # 创建申请记录
        application = JobApplication(
            user_id=session['user_id'],
            resume_id=resume.id,
            job_id=job_id,
            job_name=job_name,
            company_name=company_name,
            applicant_name=resume.name or (user.username if user else None),
            applicant_phone=resume.phone or (user.phone if user else None),
            applicant_email=resume.email or (user.email if user else None),
            expected_salary=expected_salary,
            reason=reason,
            other_info=other_info
        )
        
        resume_session.add(application)
        resume_session.commit()
        
        return jsonify({'success': True, 'message': '申请提交成功'})
    except Exception as e:
        resume_session.rollback()
        print(f"提交申请失败：{e}")
        return jsonify({'success': False, 'message': '提交失败'}), 500
    finally:
        resume_session.close()


@app.route('/api/applications')
def get_applications():
    """获取用户的投递记录——仅普通用户"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 检查是否为管理员或企业 HR
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if user and (user.is_company_admin or user.is_admin):
            return jsonify({'success': False, 'message': '未注册或者账号密码错误'}), 403
    
    resume_session = ResumeSession()
    try:
        applications = resume_session.query(JobApplication).filter_by(
            user_id=session['user_id']
        ).order_by(JobApplication.applied_at.desc()).all()
        
        result = [app.to_dict() for app in applications]
        return jsonify({'success': True, 'applications': result, 'total': len(result)})
    except Exception as e:
        print(f"获取投递记录失败：{e}")
        return jsonify({'success': False, 'message': '获取失败'}), 500
    finally:
        resume_session.close()


@app.route('/api/application/<int:app_id>')
def get_application_detail(app_id):
    """获取申请详情——仅普通用户"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 检查是否为管理员或企业 HR
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if user and (user.is_company_admin or user.is_admin):
            return jsonify({'success': False, 'message': '未注册或者账号密码错误'}), 403
    
    resume_session = ResumeSession()
    try:
        application = resume_session.query(JobApplication).filter_by(
            id=app_id,
            user_id=session['user_id']
        ).first()
        
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'}), 404
        
        return jsonify({'success': True, 'application': application.to_dict()})
    except Exception as e:
        print(f"获取申请详情失败：{e}")
        return jsonify({'success': False, 'message': '获取失败'}), 500
    finally:
        resume_session.close()


@app.route('/api/application/<int:app_id>/withdraw', methods=['POST'])
def withdraw_application(app_id):
    """撤回申请——仅普通用户"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 检查是否为管理员或企业 HR
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if user and (user.is_company_admin or user.is_admin):
            return jsonify({'success': False, 'message': '未注册或者账号密码错误'}), 403
    
    resume_session = ResumeSession()
    try:
        application = resume_session.query(JobApplication).filter_by(
            id=app_id,
            user_id=session['user_id']
        ).first()
        
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'}), 404
        
        # 只有已提交或已查看的申请可以撤回
        if application.status not in ['submitted', 'viewed']:
            return jsonify({'success': False, 'message': '当前状态无法撤回'}), 400
        
        # 删除申请记录
        resume_session.delete(application)
        resume_session.commit()
        
        return jsonify({'success': True, 'message': '申请已撤回'})
    except Exception as e:
        resume_session.rollback()
        print(f"撤回申请失败：{e}")
        return jsonify({'success': False, 'message': '撤回失败'}), 500
    finally:
        resume_session.close()


@app.route('/api/application/<int:app_id>', methods=['PUT'])
def update_application(app_id):
    """更新申请——仅普通用户"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    # 检查是否为管理员或企业 HR
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if user and (user.is_company_admin or user.is_admin):
            return jsonify({'success': False, 'message': '未注册或者账号密码错误'}), 403
    
    data = request.get_json()
    
    resume_session = ResumeSession()
    try:
        user = resume_session.query(User).filter_by(id=session['user_id']).first()
        application = resume_session.query(JobApplication).filter_by(
            id=app_id,
            user_id=session['user_id']
        ).first()
        
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'}), 404
        
        # 更新申请信息
        if 'expected_salary' in data:
            application.expected_salary = data['expected_salary']
        if 'reason' in data:
            application.reason = data['reason']
        if 'other_info' in data:
            application.other_info = data['other_info']

        # 同步本次申请的申请人快照（只影响当前申请，不影响其他历史申请）
        resume = resume_session.query(Resume).filter_by(user_id=session['user_id']).first()
        if resume:
            application.applicant_name = resume.name or application.applicant_name or (user.username if user else None)
            application.applicant_phone = resume.phone or application.applicant_phone or (user.phone if user else None)
            application.applicant_email = resume.email or application.applicant_email or (user.email if user else None)
        
        resume_session.commit()
        
        return jsonify({'success': True, 'message': '修改成功'})
    except Exception as e:
        resume_session.rollback()
        print(f"更新申请失败：{e}")
        return jsonify({'success': False, 'message': '修改失败'}), 500
    finally:
        resume_session.close()


@app.route('/company')
def company_panel():
    """企业管理员后台 - 必须勾选"企业登录"才能访问"""
    if 'user_id' not in session:
        return redirect('/login')
    
    # 关键：检查登录时是否选择了企业登录
    is_company_login = session.get('is_company', False)
    
    if not is_company_login:
        # 如果是企业 HR 账号但没勾选企业登录，提示重新登录
        with get_db_session() as db_session:
            user = db_session.query(User).filter_by(id=session['user_id']).first()
            if user and user.is_company_admin:
                return redirect('/login?message=请使用企业登录方式登录')
        return redirect('/login')
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_company_admin:
            return redirect('/login')
        
        return render_template('company.html')


@app.route('/company/settings')
def company_settings_page():
    """企业设置页面"""
    if 'user_id' not in session:
        return redirect('/login')
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_company_admin:
            return redirect('/login')
        
        return render_template('company_settings.html')


@app.route('/api/company/settings')
def get_company_settings():
    """获取公司设置"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_company_admin or not user.company_name:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        company_name = user.company_name
        company = db_session.query(Company).filter_by(company_name=company_name).first()
        
        if company:
            company_data = company.to_dict()
            company_data['recruitment_declaration'] = company_data.get('recruitment_manifesto')
            return jsonify({'success': True, 'company': company_data})
        else:
            # 如果没有公司记录，返回默认值
            return jsonify({
                'success': True,
                'company': {
                    'company_name': company_name,
                    'english_name': None,
                    'short_name': None,
                    'credit_code': None,
                    'established_date': None,
                    'industry': None,
                    'website': None,
                    'phone': None,
                    'email': None,
                    'address': None,
                    'description': None,
                    'recruitment_manifesto': None,
                    'recruitment_declaration': None,
                    'logo_path': None,
                    'enable_employer_brand': False,
                    'culture_video_url': None,
                    'employee_stories': None,
                    'resume_retention_days': 365,
                    'interview_record_archive_days': 180,
                    'gdpr_compliance': False,
                    'consent_popup_enabled': True,
                    'data_export_enabled': True,
                    'data_deletion_enabled': True,
                    'audit_log_enabled': True,
                    'audit_log_retention_days': 90,
                    'phone_mask_enabled': True,
                    'email_mask_enabled': False
                }
            })


@app.route('/api/company/settings', methods=['PUT'])
def update_company_settings():
    """更新公司设置"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_company_admin or not user.company_name:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        company_name = user.company_name
        data = request.get_json()
        
        # 查找或创建公司记录
        company = db_session.query(Company).filter_by(company_name=company_name).first()
        if not company:
            company = Company(company_name=company_name)
            db_session.add(company)
        
        # 更新字段
        if 'company_name' in data:
            company.company_name = data['company_name']
        if 'english_name' in data:
            company.english_name = data['english_name']
        if 'short_name' in data:
            company.short_name = data['short_name']
        if 'credit_code' in data:
            company.credit_code = data['credit_code']
        if 'established_date' in data:
            company.established_date = data['established_date']
        if 'industry' in data:
            company.industry = data['industry']
        if 'website' in data:
            company.website = data['website']
        if 'phone' in data:
            company.phone = data['phone']
        if 'email' in data:
            company.email = data['email']
        if 'address' in data:
            company.address = data['address']
        if 'description' in data:
            company.description = data['description']
        if 'recruitment_manifesto' in data:
            company.recruitment_manifesto = data['recruitment_manifesto']
        elif 'recruitment_declaration' in data:
            company.recruitment_manifesto = data['recruitment_declaration']
        if 'logo_path' in data:
            company.logo_path = data['logo_path']
        if 'enable_employer_brand' in data:
            company.enable_employer_brand = data['enable_employer_brand']
        if 'culture_video_url' in data:
            company.culture_video_url = data['culture_video_url']
        if 'employee_stories' in data:
            company.employee_stories = data['employee_stories']
        if 'resume_retention_days' in data:
            company.resume_retention_days = data['resume_retention_days']
        if 'interview_record_archive_days' in data:
            company.interview_record_archive_days = data['interview_record_archive_days']
        if 'gdpr_compliance' in data:
            company.gdpr_compliance = data['gdpr_compliance']
        if 'consent_popup_enabled' in data:
            company.consent_popup_enabled = data['consent_popup_enabled']
        if 'data_export_enabled' in data:
            company.data_export_enabled = data['data_export_enabled']
        if 'data_deletion_enabled' in data:
            company.data_deletion_enabled = data['data_deletion_enabled']
        if 'audit_log_enabled' in data:
            company.audit_log_enabled = data['audit_log_enabled']
        if 'audit_log_retention_days' in data:
            company.audit_log_retention_days = data['audit_log_retention_days']
        if 'phone_mask_enabled' in data:
            company.phone_mask_enabled = data['phone_mask_enabled']
        if 'email_mask_enabled' in data:
            company.email_mask_enabled = data['email_mask_enabled']
        
        db_session.commit()
        
        # 记录审计日志
        if company.audit_log_enabled:
            audit_log = AuditLog(
                company_id=company.id,
                user_id=user.id,
                action='UPDATE_SETTINGS',
                module='company_settings',
                details=f'更新公司设置：{list(data.keys())}',
                ip_address=request.remote_addr
            )
            db_session.add(audit_log)
            db_session.commit()
        
        company_data = company.to_dict()
        company_data['recruitment_declaration'] = company_data.get('recruitment_manifesto')
        return jsonify({'success': True, 'message': '保存成功', 'company': company_data})


# ==================== 企业管理员相关 API ====================

@app.route('/api/company/dashboard')
def company_dashboard():
    """企业管理员 - 控制台统计"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_company_admin or not user.company_name:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        company_name = user.company_name
        
        # 统计数据
        total = db_session.query(JobApplication).filter_by(company_name=company_name).count()
        pending = db_session.query(JobApplication).filter_by(
            company_name=company_name,
            status='submitted'
        ).count()
        interview = db_session.query(JobApplication).filter_by(
            company_name=company_name,
            status='interview'
        ).count()
        offer = db_session.query(JobApplication).filter_by(
            company_name=company_name,
            status='offer'
        ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'pending': pending,
                'interview': interview,
                'offer': offer
            }
        })


@app.route('/api/company/applications')
def company_applications():
    """企业管理员 - 投递列表"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_company_admin or not user.company_name:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        company_name = user.company_name
        
        # 获取该公司的所有投递记录
        applications = db_session.query(JobApplication).filter_by(
            company_name=company_name
        ).order_by(JobApplication.applied_at.desc()).limit(200).all()
        
        result = []
        for app in applications:
            # 获取求职者信息
            resume = db_session.query(Resume).filter_by(id=app.resume_id).first()
            applicant = db_session.query(User).filter_by(id=app.user_id).first()
            
            app_data = {
                'id': app.id,
                'user_id': app.user_id,
                'name': app.applicant_name or (resume.name if resume else (applicant.username if applicant else '未知')),
                'phone': app.applicant_phone or (resume.phone if resume else (applicant.phone if applicant else '-')),
                'email': app.applicant_email or (resume.email if resume else (applicant.email if applicant else '-')),
                'job_id': app.job_id,
                'job_name': app.job_name,
                'company_name': app.company_name,
                'status': app.status,
                'applied_at': app.applied_at.isoformat() if app.applied_at else None,
                'resume_url': '/api/resume/download/' + str(app.resume_id) if resume and resume.has_attachment else None
            }
            result.append(app_data)
        
        return jsonify({
            'success': True,
            'applications': result
        })


@app.route('/api/company/jobs')
def company_jobs():
    """企业管理员 - 在招职位"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_company_admin or not user.company_name:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        company_name = user.company_name
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 获取该公司的所有职位（分页）
        jobs_query = db_session.query(JobPosition).filter_by(
            company_name=company_name
        ).order_by(JobPosition.id.desc())
        
        total = jobs_query.count()
        jobs = jobs_query.offset((page - 1) * per_page).limit(per_page).all()
        
        result = []
        for job in jobs:
            # 统计每个职位的投递数
            app_count = db_session.query(JobApplication).filter_by(
                job_id=job.id
            ).count()
            
            result.append({
                'id': job.id,
                'job_name': job.job_name,
                'min_salary': job.min_salary,
                'max_salary': job.max_salary,
                'city': job.city,
                'education': job.education,
                'experience': job.experience,
                'status': job.status,
                'application_count': app_count
            })
        
        return jsonify({
            'success': True,
            'jobs': result,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })


@app.route('/api/company/application/<int:app_id>/status', methods=['PUT'])
def company_update_application_status(app_id):
    """企业管理员 - 更新申请状态"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_company_admin or not user.company_name:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        data = request.get_json()
        new_status = data.get('status', '')
        
        if new_status not in ['submitted', 'viewed', 'interview', 'offer', 'rejected']:
            return jsonify({'success': False, 'message': '无效的状态'}), 400
        
        application = db_session.query(JobApplication).filter_by(id=app_id).first()
        
        if not application:
            return jsonify({'success': False, 'message': '申请不存在'}), 404
        
        # 确保只能修改本公司的申请
        if application.company_name != user.company_name:
            return jsonify({'success': False, 'message': '无权限修改'}), 403
        
        application.status = new_status
        db_session.commit()
        
        return jsonify({'success': True, 'message': '状态已更新'})


@app.route('/api/company/statistics')
def company_statistics():
    """企业管理员 - 详细统计数据"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    from datetime import datetime, timedelta
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_company_admin or not user.company_name:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        company_name = user.company_name
        now = datetime.now()
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 本周和月初时间
        week_start = now - timedelta(days=now.weekday())
        month_start = now.replace(day=1)
        
        # 获取所有投递
        all_apps = db_session.query(JobApplication).filter_by(
            company_name=company_name
        ).all()
        
        # 统计数据
        total = len(all_apps)
        week_new = sum(1 for app in all_apps if app.applied_at and app.applied_at >= week_start)
        month_new = sum(1 for app in all_apps if app.applied_at and app.applied_at >= month_start)
        
        # 状态统计
        status_count = {
            'submitted': sum(1 for app in all_apps if app.status == 'submitted'),
            'viewed': sum(1 for app in all_apps if app.status == 'viewed'),
            'interview': sum(1 for app in all_apps if app.status == 'interview'),
            'offer': sum(1 for app in all_apps if app.status == 'offer'),
            'rejected': sum(1 for app in all_apps if app.status == 'rejected')
        }
        
        # 平均处理时长（从 submitted 到 viewed/interview/offer/rejected）
        processed_apps = [app for app in all_apps if app.status != 'submitted' and app.applied_at]
        avg_process_days = 0
        if processed_apps:
            # 简化计算，假设处理时间为当前时间减去申请时间
            total_days = sum((now - app.applied_at).days for app in processed_apps)
            avg_process_days = round(total_days / len(processed_apps)) if processed_apps else 0
        
        # 简历完善率
        resume_ids = set(app.resume_id for app in all_apps if app.resume_id)
        complete_resumes = db_session.query(Resume).filter(
            Resume.id.in_(resume_ids),
            Resume.is_complete == 1
        ).count()
        resume_complete_rate = round(complete_resumes / len(resume_ids) * 100) if resume_ids else 0
        
        # 职位统计（分页）
        jobs_query = db_session.query(JobPosition).filter_by(company_name=company_name)
        total_jobs = jobs_query.count()
        jobs = jobs_query.order_by(JobPosition.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        job_stats = []
        for job in jobs:
            job_apps = [app for app in all_apps if app.job_id == job.id]
            job_total = len(job_apps)
            job_submitted = sum(1 for app in job_apps if app.status == 'submitted')
            job_interview = sum(1 for app in job_apps if app.status == 'interview')
            job_offer = sum(1 for app in job_apps if app.status == 'offer')
            job_rejected = sum(1 for app in job_apps if app.status == 'rejected')
            conversion_rate = round(job_offer / job_total * 100) if job_total > 0 else 0
            
            job_stats.append({
                'job_name': job.job_name,
                'total': job_total,
                'submitted': job_submitted,
                'interview': job_interview,
                'offer': job_offer,
                'rejected': job_rejected,
                'conversion_rate': conversion_rate
            })
        
        return jsonify({
            'success': True,
            'statistics': {
                'week_new': week_new,
                'month_new': month_new,
                'avg_process_days': avg_process_days,
                'resume_complete_rate': resume_complete_rate,
                'status_count': status_count,
                'job_stats': job_stats,
                'total_jobs': total_jobs,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_jobs + per_page - 1) // per_page
            }
        })


# ==================== 管理员相关 API ====================

@app.route('/api/admin/check')
def check_admin():
    """检查是否为管理员"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        return jsonify({'success': True, 'user': user.to_dict()})


@app.route('/api/admin/dashboard')
def admin_dashboard():
    """管理员控制台 - 数据统计"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        # 统计数据
        total_users = db_session.query(User).filter(User.is_admin == False).count()
        total_jobs = db_session.query(JobPosition).count()
        total_applications = db_session.query(JobApplication).count()
        pending_jobs = db_session.query(JobPosition).filter(JobPosition.status == 'pending').count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_jobs': total_jobs,
                'total_applications': total_applications,
                'pending_jobs': pending_jobs
            }
        })


@app.route('/api/admin/users')
def admin_users():
    """管理员 - 用户列表"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        keyword = request.args.get('keyword', '')
        
        query = db_session.query(User).filter(User.is_admin == False)
        if keyword:
            query = query.filter(
                (User.username.like(f'%{keyword}%')) |
                (User.phone.like(f'%{keyword}%')) |
                (User.email.like(f'%{keyword}%'))
            )
        
        users = query.order_by(User.id.desc()).all()
        
        return jsonify({
            'success': True,
            'users': [u.to_dict() for u in users]
        })


@app.route('/api/admin/users/<int:user_id>')
def admin_user_detail(user_id):
    """管理员 - 用户详情"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        target_user = db_session.query(User).filter_by(id=user_id).first()
        if not target_user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        return jsonify({
            'success': True,
            'user': target_user.to_dict()
        })


@app.route('/api/admin/users/<int:user_id>/status', methods=['PUT'])
def admin_update_user_status(user_id):
    """管理员 - 修改用户状态"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        admin = db_session.query(User).filter_by(id=session['user_id']).first()
        if not admin or not admin.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        data = request.get_json()
        target_user = db_session.query(User).filter_by(id=user_id).first()
        
        if not target_user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        target_user.is_active = data.get('is_active', True)
        db_session.commit()
        
        return jsonify({'success': True, 'message': '操作成功'})


@app.route('/api/admin/jobs')
def admin_jobs():
    """管理员 - 职位列表"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 30, type=int)
        status = request.args.get('status', '')
        
        # 查询
        query = db_session.query(JobPosition)
        if status:
            query = query.filter(JobPosition.status == status)
        
        # 总数（限制最多 500 条）
        total = min(query.count(), 500)
        
        # 分页查询（限制 500 条）
        offset = (page - 1) * per_page
        jobs = query.order_by(JobPosition.id.desc()).limit(min(per_page, 500 - offset)).offset(offset).all()
        
        return jsonify({
            'success': True,
            'jobs': [{
                'id': job.id,
                'job_name': job.job_name,
                'company_name': job.company_name,
                'min_salary': job.min_salary,
                'max_salary': job.max_salary,
                'city': job.city,
                'status': job.status,
                'publish_date': job.publish_date
            } for job in jobs],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })


@app.route('/api/admin/jobs/<int:job_id>/audit', methods=['PUT'])
def admin_audit_job(job_id):
    """管理员 - 审核职位"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        admin = db_session.query(User).filter_by(id=session['user_id']).first()
        if not admin or not admin.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        data = request.get_json()
        job = db_session.query(JobPosition).filter_by(id=job_id).first()
        
        if not job:
            return jsonify({'success': False, 'message': '职位不存在'}), 404
        
        result = data.get('result', 'approved')
        reason = data.get('reason', '')
        
        if result == 'approved':
            job.status = 'active'
        elif result == 'rejected':
            job.status = 'rejected'
            if reason:
                # 使用 markupsafe 转义 HTML 字符，防止 XSS 攻击
                safe_reason = str(escape(reason))
                job.description = (job.description or '') + f'\n\n【审核驳回原因】{safe_reason}'
        
        db_session.commit()
        
        return jsonify({'success': True, 'message': '审核完成'})


@app.route('/api/admin/applications')
def admin_applications():
    """管理员 - 投递记录"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        applications = db_session.query(JobApplication).order_by(JobApplication.id.desc()).limit(100).all()
        
        return jsonify({
            'success': True,
            'applications': [{
                'id': app.id,
                'user_id': app.user_id,
                'user_name': db_session.query(User).filter_by(id=app.user_id).first().username if db_session.query(User).filter_by(id=app.user_id).first() else '未知',
                'job_id': app.job_id,
                'job_name': app.job_name,
                'company_name': app.company_name,
                'status': app.status,
                'applied_at': app.applied_at.isoformat() if app.applied_at else None
            } for app in applications]
        })


@app.route('/api/admin/password', methods=['PUT'])
def admin_update_password():
    """管理员 - 修改密码"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    from werkzeug.security import generate_password_hash
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        data = request.get_json()
        password = data.get('password', '')
        
        if not password or len(password) < 8:
            return jsonify({'success': False, 'message': '密码长度至少 8 位'}), 400
        
        user.password_hash = generate_password_hash(password)
        db_session.commit()
        
        return jsonify({'success': True, 'message': '密码修改成功'})


# ==================== 企业管理模块 ====================

@app.route('/api/admin/companies')
def admin_companies():
    """管理员 - 企业列表"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 30, type=int)
        
        # 只按公司名分组，获取唯一公司列表（限制 500 条）
        companies = db_session.query(
            JobPosition.company_name
        ).filter(
            JobPosition.company_name.isnot(None),
            JobPosition.company_name != ''
        ).distinct().limit(500).all()
        
        # 总数
        total = len(companies)
        
        # 手动分页
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        companies_page = companies[start_idx:end_idx]
        
        company_list = []
        for company_tuple in companies_page:
            company_name = company_tuple[0]
            if company_name:
                # 获取该公司的所有职位
                jobs = db_session.query(JobPosition).filter_by(
                    company_name=company_name
                ).all()
                
                # 取第一个职位的行业和城市作为代表
                industry = jobs[0].industry if jobs and jobs[0].industry else '未设置'
                city = jobs[0].city if jobs and jobs[0].city else '未设置'
                
                company_list.append({
                    'company_name': company_name,
                    'industry': industry,
                    'city': city,
                    'job_count': len(jobs)
                })
        
        return jsonify({
            'success': True,
            'companies': company_list,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })


@app.route('/api/admin/companies/<company_name>')
def admin_company_detail(company_name):
    """管理员 - 企业详情"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        jobs = db_session.query(JobPosition).filter_by(
            company_name=company_name
        ).all()
        
        return jsonify({
            'success': True,
            'company': {
                'company_name': company_name,
                'jobs': [{
                    'id': job.id,
                    'job_name': job.job_name,
                    'salary': f'{job.min_salary}-{job.max_salary}',
                    'city': job.city,
                    'status': job.status
                } for job in jobs]
            }
        })


# ==================== 内容安全与风控 ====================

@app.route('/api/admin/sensitive-words', methods=['GET', 'POST'])
def admin_sensitive_words():
    """管理员 - 敏感词管理"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        if request.method == 'POST':
            data = request.get_json()
            # TODO: 创建敏感词表并保存
            return jsonify({'success': True, 'message': '敏感词已添加'})
        
        # 返回敏感词列表（暂时返回示例数据）
        words = [
            {'id': 1, 'word': '测试敏感词 1', 'type': '违禁词', 'created_at': '2026-01-01'},
            {'id': 2, 'word': '测试敏感词 2', 'type': '广告词', 'created_at': '2026-01-02'}
        ]
        
        return jsonify({'success': True, 'words': words})


@app.route('/api/admin/jobs/audit/batch', methods=['POST'])
def admin_batch_audit():
    """管理员 - 批量审核职位"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        data = request.get_json()
        job_ids = data.get('job_ids', [])
        result = data.get('result', 'approved')
        reason = data.get('reason', '')
        
        for job_id in job_ids:
            job = db_session.query(JobPosition).filter_by(id=job_id).first()
            if job:
                job.status = 'active' if result == 'approved' else 'rejected'
        
        db_session.commit()
        return jsonify({'success': True, 'message': f'批量审核完成，共{len(job_ids)}个职位'})


# ==================== 数据导出功能 ====================

@app.route('/api/admin/export/users')
def admin_export_users():
    """管理员 - 导出用户数据"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        users = db_session.query(User).all()
        
        # 生成 CSV 数据（手机号脱敏）
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '用户名', '邮箱', '手机（脱敏）', '学历', '毕业年份', '注册时间'])
        for u in users:
            # 手机号脱敏：保留前 3 位和后 4 位
            masked_phone = ''
            if u.phone and len(u.phone) >= 7:
                masked_phone = u.phone[:3] + '****' + u.phone[-4:]
            elif u.phone:
                masked_phone = '****'
            writer.writerow([u.id, u.username, u.email, masked_phone, u.education or '', u.graduation_year or '', u.created_at])
        
        return jsonify({
            'success': True,
            'message': '导出成功',
            'data': output.getvalue()
        })


@app.route('/api/admin/export/jobs')
def admin_export_jobs():
    """管理员 - 导出职位数据"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        jobs = db_session.query(JobPosition).all()
        
        # 生成 CSV 数据
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '职位名称', '公司', '薪资范围', '城市', '状态', '发布时间'])
        for job in jobs:
            writer.writerow([job.id, job.job_name, job.company_name, f'{job.min_salary}-{job.max_salary}', job.city, job.status, job.publish_date])
        
        return jsonify({
            'success': True,
            'message': '导出成功',
            'data': output.getvalue()
        })


@app.route('/api/admin/export/applications')
def admin_export_applications():
    """管理员 - 导出投递记录"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        applications = db_session.query(JobApplication).limit(1000).all()
        
        # 生成 CSV 数据（手机号脱敏）
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '求职者姓名', '手机号（脱敏）', '职位名称', '公司', '状态', '投递时间'])
        for app in applications:
            # 优先使用申请快照，避免历史导出受用户资料后续修改影响
            need_user_fallback = not app.applicant_name or not app.applicant_phone
            applicant_user = db_session.query(User).filter_by(id=app.user_id).first() if need_user_fallback else None

            applicant_phone = app.applicant_phone or (applicant_user.phone if applicant_user else '')
            masked_phone = ''
            if applicant_phone and len(applicant_phone) >= 7:
                masked_phone = applicant_phone[:3] + '****' + applicant_phone[-4:]
            elif applicant_phone:
                masked_phone = '****'

            applicant_name = app.applicant_name or (applicant_user.username if applicant_user else '未知')
            writer.writerow([app.id, applicant_name, masked_phone, app.job_name, app.company_name, app.status, app.applied_at])
        
        return jsonify({
            'success': True,
            'message': '导出成功',
            'data': output.getvalue()
        })


# ==================== 日志审计系统 ====================

@app.route('/api/admin/logs')
def admin_logs():
    """管理员 - 操作日志"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        # 返回示例日志数据（后续需要创建日志表）
        logs = [
            {'id': 1, 'user': 'admin', 'action': '登录系统', 'ip': '192.168.1.100', 'time': '2026-04-01 10:30:00'},
            {'id': 2, 'user': 'admin', 'action': '审核职位', 'ip': '192.168.1.100', 'time': '2026-04-01 11:20:00'},
            {'id': 3, 'user': 'admin', 'action': '导出用户数据', 'ip': '192.168.1.100', 'time': '2026-04-01 14:15:00'}
        ]
        
        return jsonify({'success': True, 'logs': logs})


# ==================== 系统配置管理 ====================

@app.route('/api/admin/settings', methods=['GET', 'PUT'])
def admin_settings():
    """管理员 - 系统设置"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': '无权限'}), 403
        
        if request.method == 'GET':
            # 返回系统配置
            return jsonify({
                'success': True,
                'settings': {
                    'site_name': '职引未来',
                    'max_resume_size': 5,
                    'enable_audit': True,
                    'maintenance_mode': False,
                    'allow_register': True,
                    'job_expire_days': 30
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            # 保存配置（暂时只返回成功）
            return jsonify({'success': True, 'message': '设置已保存'})


# ==================== 启动配置 ====================

def init_app():
    """初始化应用"""
    print("=" * 60)
    print("🚀 职引未来 - 高校毕业生就业服务平台")
    print("=" * 60)
    print(f"📍 服务地址：http://{config.FLASK_CONFIG['HOST']}:{config.FLASK_CONFIG['PORT']}")
    print("✨ 功能模块:")
    print("   🏠 主页 - 系统设计和功能展示")
    print("   📊 数据洞察 - 可视化分析图表")
    print("   🔐 登录注册 - 用户认证")
    print("   💬 聊天功能 - 实时沟通")
    print("=" * 60)


# ==================== 聊天功能 ====================

# 导入聊天模型
from models_chat import Conversation, Message, get_session, init_db as init_chat_db

# 初始化聊天数据库表
try:
    init_chat_db()
except Exception as e:
    print(f"聊天数据库初始化警告：{e}")


@app.route('/api/chat/conversations', methods=['GET'])
def get_conversations():
    """获取会话列表"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    chat_session = get_session()
    try:
        with get_db_session() as db_session:
            user = db_session.query(User).filter_by(id=session['user_id']).first()
            
            if not user or not user.is_active:
                return jsonify({'success': False, 'message': '用户不存在'}), 404

            is_company_mode = bool(session.get('is_company', False))
            
            if is_company_mode:
                if not user.is_company_admin:
                    return jsonify({'success': False, 'message': '当前不是企业登录状态'}), 403
                conversations = chat_session.query(Conversation).filter(
                    Conversation.company_name == user.company_name,
                    Conversation.is_active == True
                ).order_by(Conversation.updated_at.desc()).all()
            else:
                conversations = chat_session.query(Conversation).filter(
                    Conversation.user_id == session['user_id'],
                    Conversation.is_active == True
                ).order_by(Conversation.updated_at.desc()).all()

            result = []
            for conv in conversations:
                conv_data = conv.to_dict()

                # 企业端会话列表优先显示对应申请记录中的“申请时姓名快照”
                application_query = db_session.query(JobApplication).filter_by(
                    user_id=conv.user_id,
                    company_name=conv.company_name
                )

                if conv.job_id:
                    matched_application = application_query.filter_by(job_id=conv.job_id).order_by(JobApplication.applied_at.desc()).first()
                else:
                    # 无职位绑定时，取最早申请以保持会话展示名称稳定
                    matched_application = application_query.order_by(JobApplication.applied_at.asc()).first()

                if not matched_application:
                    matched_application = application_query.order_by(JobApplication.applied_at.desc()).first()

                applicant_name = None
                if matched_application and matched_application.applicant_name:
                    applicant_name = matched_application.applicant_name

                if not applicant_name and matched_application and matched_application.resume_id:
                    related_resume = db_session.query(Resume).filter_by(id=matched_application.resume_id).first()
                    if related_resume and related_resume.name:
                        applicant_name = related_resume.name

                if not applicant_name:
                    applicant = db_session.query(User).filter_by(id=conv.user_id).first()
                    applicant_name = applicant.username if applicant else f"用户{conv.user_id}"

                conv_data['user_name'] = applicant_name

                # 兼容旧数据：若会话表未维护最后一条消息，则从消息表兜底读取
                if not conv_data.get('last_message_content') or not conv_data.get('last_message_at'):
                    last_message = chat_session.query(Message).filter_by(
                        conversation_id=conv.id
                    ).order_by(Message.created_at.desc()).first()
                    if last_message:
                        if not conv_data.get('last_message_content'):
                            conv_data['last_message_content'] = last_message.content
                        if not conv_data.get('last_message_at'):
                            conv_data['last_message_at'] = (
                                last_message.created_at.isoformat() if last_message.created_at else conv_data.get('updated_at')
                            )

                if not conv_data.get('last_message_at'):
                    conv_data['last_message_at'] = conv_data.get('updated_at')

                result.append(conv_data)

            return jsonify({'success': True, 'conversations': result})
    
    except Exception as e:
        print(f"获取会话列表失败：{e}")
        return jsonify({'success': False, 'message': '获取失败'}), 500
    finally:
        chat_session.close()


@app.route('/api/chat/conversations', methods=['POST'])
def create_conversation():
    """创建新会话"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    data = request.get_json(silent=True) or {}
    company_name = (data.get('company_name') or '').strip()
    job_id = data.get('job_id')
    job_name = (data.get('job_name') or '').strip()
    target_user_id = data.get('user_id')

    try:
        job_id = int(job_id) if job_id not in (None, '', 'null') else None
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': '职位参数无效'}), 400

    chat_session = get_session()
    try:
        with get_db_session() as db_session:
            user = db_session.query(User).filter_by(id=session['user_id']).first()
            if not user or not user.is_active:
                return jsonify({'success': False, 'message': '用户不存在'}), 404

            is_company_mode = bool(session.get('is_company', False))

            if is_company_mode:
                if not user.is_company_admin:
                    return jsonify({'success': False, 'message': '当前不是企业登录状态'}), 403
                try:
                    chat_user_id = int(target_user_id) if target_user_id else session['user_id']
                except (TypeError, ValueError):
                    return jsonify({'success': False, 'message': '用户参数无效'}), 400
                company_name = company_name or (user.company_name or '').strip()
                company_owner_id = user.id
            else:
                chat_user_id = session['user_id']

                # 普通用户兜底：若前端未传 company_name，尝试从职位表补齐
                if not company_name and job_id:
                    job = db_session.query(JobPosition).filter_by(id=job_id).first()
                    if job:
                        company_name = (job.company_name or '').strip()
                        if not job_name:
                            job_name = job.job_name or ''

                company_owner = None
                if company_name:
                    company_owner = db_session.query(User).filter_by(
                        is_company_admin=True,
                        company_name=company_name
                    ).order_by(User.id.asc()).first()

                if company_owner:
                    company_owner_id = company_owner.id
                else:
                    company_record = db_session.query(Company).filter_by(company_name=company_name).first() if company_name else None
                    company_owner_id = company_record.id if company_record else 0

            if not company_name:
                return jsonify({'success': False, 'message': '公司名称不能为空'}), 400

            # 企业模式：同候选人+同公司+同岗位复用会话；普通用户模式保持同公司复用
            existing_query = chat_session.query(Conversation).filter_by(
                user_id=chat_user_id,
                company_name=company_name
            )
            if is_company_mode and job_id:
                existing_query = existing_query.filter_by(job_id=job_id)

            existing = existing_query.order_by(Conversation.updated_at.desc()).first()
            if existing:
                if not existing.is_active:
                    existing.is_active = True
                # 保留创建时职位信息，但允许在为空时补齐
                if not existing.job_id and job_id:
                    existing.job_id = job_id
                if not existing.job_name and job_name:
                    existing.job_name = job_name
                existing.updated_at = datetime.now()
                chat_session.commit()
                return jsonify({'success': True, 'conversation': existing.to_dict(), 'created': False})

            # 创建新会话
            conversation = Conversation(
                user_id=chat_user_id,
                company_id=company_owner_id,
                company_name=company_name,
                job_id=job_id,
                job_name=job_name
            )
            chat_session.add(conversation)
            chat_session.commit()
            return jsonify({'success': True, 'conversation': conversation.to_dict(), 'created': True})
    except Exception as e:
        chat_session.rollback()
        print(f"创建会话失败：{e}")
        return jsonify({'success': False, 'message': '创建失败'}), 500
    finally:
        chat_session.close()


@app.route('/api/chat/messages/<int:conversation_id>', methods=['GET'])
def get_messages(conversation_id):
    """获取消息列表"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    chat_session = get_session()
    try:
        with get_db_session() as db_session:
            user = db_session.query(User).filter_by(id=session['user_id']).first()
            if not user or not user.is_active:
                return jsonify({'success': False, 'message': '用户不存在'}), 404

            is_company_mode = bool(session.get('is_company', False))

            conversation = chat_session.query(Conversation).filter_by(id=conversation_id).first()
            
            if not conversation or not conversation.is_active:
                return jsonify({'success': False, 'message': '会话不存在'}), 404
            
            if is_company_mode:
                if not user.is_company_admin:
                    return jsonify({'success': False, 'message': '当前不是企业登录状态'}), 403
                if conversation.company_name != user.company_name:
                    return jsonify({'success': False, 'message': '无权访问'}), 403
                if (conversation.company_unread_count or 0) > 0:
                    conversation.company_unread_count = 0
                    chat_session.commit()
            else:
                if conversation.user_id != session['user_id']:
                    return jsonify({'success': False, 'message': '无权访问'}), 403
                if (conversation.user_unread_count or 0) > 0:
                    conversation.user_unread_count = 0
                    chat_session.commit()

        messages = chat_session.query(Message).filter_by(
            conversation_id=conversation_id
        ).order_by(Message.created_at.asc()).all()
        
        result = [msg.to_dict() for msg in messages]
        return jsonify({'success': True, 'messages': result})
    
    except Exception as e:
        print(f"获取消息失败：{e}")
        return jsonify({'success': False, 'message': '获取失败'}), 500
    finally:
        chat_session.close()


@app.route('/api/chat/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation_detail(conversation_id):
    """兼容企业端旧接口：返回会话消息列表。"""
    return get_messages(conversation_id)


@app.route('/api/chat/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """删除会话（软删除）。"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401

    chat_session = get_session()
    try:
        with get_db_session() as db_session:
            user = db_session.query(User).filter_by(id=session['user_id']).first()
            if not user or not user.is_active:
                return jsonify({'success': False, 'message': '用户不存在'}), 404

            conversation = chat_session.query(Conversation).filter_by(id=conversation_id).first()
            if not conversation or not conversation.is_active:
                return jsonify({'success': False, 'message': '会话不存在'}), 404

            is_company_mode = bool(session.get('is_company', False))
            if is_company_mode:
                if not user.is_company_admin:
                    return jsonify({'success': False, 'message': '当前不是企业登录状态'}), 403
                if conversation.company_name != user.company_name:
                    return jsonify({'success': False, 'message': '无权删除该会话'}), 403
            else:
                if conversation.user_id != session['user_id']:
                    return jsonify({'success': False, 'message': '无权删除该会话'}), 403

            conversation.is_active = False
            conversation.user_unread_count = 0
            conversation.company_unread_count = 0
            conversation.updated_at = datetime.now()
            chat_session.commit()

            return jsonify({'success': True, 'message': '会话已删除'})
    except Exception as e:
        chat_session.rollback()
        print(f"删除会话失败：{e}")
        return jsonify({'success': False, 'message': '删除失败'}), 500
    finally:
        chat_session.close()


@app.route('/api/chat/messages', methods=['POST'])
def send_message():
    """发送消息"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    data = request.get_json(silent=True) or {}
    conversation_id = data.get('conversation_id')
    content = data.get('content', '').strip()
    message_type = (data.get('message_type') or 'text').strip()
    
    if not conversation_id or not content:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    chat_session = get_session()
    try:
        with get_db_session() as db_session:
            user = db_session.query(User).filter_by(id=session['user_id']).first()
            if not user or not user.is_active:
                return jsonify({'success': False, 'message': '用户不存在'}), 404

            is_company_mode = bool(session.get('is_company', False))

            conversation = chat_session.query(Conversation).filter_by(id=conversation_id).first()
            
            if not conversation or not conversation.is_active:
                return jsonify({'success': False, 'message': '会话不存在'}), 404
            
            if is_company_mode:
                if not user.is_company_admin:
                    return jsonify({'success': False, 'message': '当前不是企业登录状态'}), 403
                if conversation.company_name != user.company_name:
                    return jsonify({'success': False, 'message': '无权发送消息'}), 403
                sender_type = 'company'
            else:
                if conversation.user_id != session['user_id']:
                    return jsonify({'success': False, 'message': '无权发送消息'}), 403
                sender_type = 'user'
            
            message = Message(
                conversation_id=conversation_id,
                sender_type=sender_type,
                sender_id=session['user_id'],
                message_type=message_type or 'text',
                content=content
            )
            
            chat_session.add(message)
            
            now = datetime.now()
            conversation.updated_at = now
            conversation.last_message_at = now
            conversation.last_message_content = content

            if sender_type == 'company':
                conversation.user_unread_count = (conversation.user_unread_count or 0) + 1
                conversation.company_unread_count = 0
            else:
                conversation.company_unread_count = (conversation.company_unread_count or 0) + 1
                conversation.user_unread_count = 0
            
            chat_session.commit()
            
            return jsonify({'success': True, 'message': message.to_dict()})
    
    except Exception as e:
        chat_session.rollback()
        print(f"发送消息失败：{e}")
        return jsonify({'success': False, 'message': '发送失败'}), 500
    finally:
        chat_session.close()


@app.route('/chat/company')
def company_chat():
    """企业 HR 聊天页面"""
    if 'user_id' not in session:
        return redirect('/login')
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_company_admin:
            return redirect('/login')
        
        return render_template('company_chat.html', user=user)


@app.route('/chat/user')
def user_chat():
    """普通用户聊天页面"""
    if 'user_id' not in session:
        return redirect('/login')

    # 使用本次登录模式判断门户，避免跨角色登录后误跳转登录页
    if session.get('is_admin'):
        return redirect('/admin')
    if session.get('is_company'):
        return redirect('/company')
    
    with get_db_session() as db_session:
        user = db_session.query(User).filter_by(id=session['user_id']).first()
        if not user or not user.is_active:
            session.clear()
            return redirect('/login?message=登录已失效，请重新登录')
        
        return render_template('user_chat.html', user=user)


if __name__ == '__main__':
    init_app()
    app.run(
        host=config.FLASK_CONFIG['HOST'],
        port=config.FLASK_CONFIG['PORT'],
        debug=config.FLASK_CONFIG['DEBUG']
    )
