#!/usr/bin/env python
"""
快速配置脚本 - 一键设置环境变量
"""
import os
import sys

def setup_env():
    """设置环境变量"""
    print("=" * 70)
    print("⚙️  职引未来 - 快速配置工具")
    print("=" * 70)
    
    # 检查 .env 文件
    env_file = '.env'
    if not os.path.exists(env_file):
        print(f"\n📝 创建 {env_file} 配置文件...")
        
        # 生成随机 SECRET_KEY
        import secrets
        secret_key = secrets.token_hex(32)
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"""# Flask 密钥（生产环境必须修改）
SECRET_KEY={secret_key}

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_database_password_here
DB_NAME=job_navigation

# 服务器配置
PORT=5000
""")
        print(f"✅ 已创建 {env_file}")
        print(f"\n⚠️  请编辑 {env_file} 文件，设置正确的数据库密码！")
    else:
        print(f"\n✅ {env_file} 已存在")
    
    # 检查 logs 目录
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"✅ 已创建日志目录：{log_dir}")
    else:
        print(f"✅ 日志目录已存在：{log_dir}")
    
    # 检查 uploads 目录
    upload_dir = 'uploads/resumes'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        print(f"✅ 已创建上传目录：{upload_dir}")
    else:
        print(f"✅ 上传目录已存在：{upload_dir}")
    
    print("\n" + "=" * 70)
    print("✅ 配置完成！")
    print("=" * 70)
    print("\n下一步操作：")
    print(f"1. 编辑 {env_file} 文件，设置数据库密码")
    print("2. 运行：python app.py (开发环境)")
    print("   或：python run_production.py (生产环境)")
    print("=" * 70)

if __name__ == '__main__':
    setup_env()
