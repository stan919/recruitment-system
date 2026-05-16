"""
配置文件
"""
import os

# 数据库配置
DATABASE_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),  # 从环境变量读取
    'database': os.environ.get('DB_NAME', 'job_navigation'),
}

# Flask 配置
FLASK_CONFIG = {
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-key-change-in-production-' + __name__),
    'HOST': '127.0.0.1',
    'PORT': 5000,
    'DEBUG': False
}

# AI 配置
AI_CONFIG = {
    'BASE_URL': os.environ.get('AI_API_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
    'API_KEY': os.environ.get('AI_API_KEY', ''),
    'MODEL': os.environ.get('AI_API_MODEL', 'qwen-plus'),
    'TIMEOUT': int(os.environ.get('AI_API_TIMEOUT', 60)),
    'ATTACHMENT_TIMEOUT': int(os.environ.get('AI_ATTACHMENT_TIMEOUT', 30)),
    'TEMPERATURE': float(os.environ.get('AI_API_TEMPERATURE', 0.7)),
    'MAX_TOKENS': int(os.environ.get('AI_API_MAX_TOKENS', 1200)),
}

# 城市映射配置（前端传值到实际城市名）
CITY_MAPPING = {
    'bj': '北京',
    'sh': '上海',
    'gz': '广州',
    'sz': '深圳',
    'cd': '成都',
    'hz': '杭州',
    'nj': '南京',
    'wh': '武汉',
    'xa': '西安',
    'tj': '天津',
    'su': '苏州',
    'dg': '东莞'
}

# 专业方向关键词配置
PROFESSION_KEYWORDS = {
    'cs': '计算机',
    'se': '软件',
    'ai': '人工智能',
    'ee': '电子',
    'ba': '工商管理',
    'fi': '金融',
    'design': '设计',
    'marketing': '市场'
}

# 数据清洗 - 城市映射
CLEAN_CITY_MAPPING = {
    '北京': '北京',
    '北京市': '北京',
    '上海': '上海',
    '上海市': '上海',
    '广州': '广州',
    '深圳': '深圳',
    '杭州': '杭州',
}

# 数据清洗 - 学历映射
CLEAN_EDUCATION_MAPPING = {
    '不限': '不限',
    '高中': '高中',
    '中专': '中专',
    '大专': '大专',
    '本科': '本科',
    '学士': '本科',
    '硕士': '硕士',
    '研究生': '硕士',
    '博士': '博士',
}

# 数据清洗 - 经验映射
CLEAN_EXPERIENCE_MAPPING = {
    '不限': '不限',
    '应届生': '应届生',
    '在校生': '在校生',
    '1 年以下': '1 年以下',
    '1-3 年': '1-3 年',
    '3-5 年': '3-5 年',
    '5-10 年': '5-10 年',
    '10 年以上': '10 年以上',
}

# 停用词表
STOP_WORDS = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '我们', '公司', '提供'}
