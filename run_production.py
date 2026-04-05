#!/usr/bin/env python
"""
生产环境启动脚本
使用 Gunicorn WSGI 服务器
"""
import os
from app import app

if __name__ == '__main__':
    # 尝试导入 gunicorn，如果没有安装则使用 Flask 内置服务器
    try:
        from gunicorn.app.wsgiapp import run as gunicorn_run
        
        print("=" * 70)
        print("🚀 职引未来 - 高校毕业生就业服务平台（生产环境）")
        print("=" * 70)
        print(f"📍 服务地址：http://0.0.0.0:{os.environ.get('PORT', 5000)}")
        print("✨ 使用 Gunicorn WSGI 服务器")
        print("=" * 70)
        
        # Gunicorn 配置
        os.environ['GUNICORN_CMD_ARGS'] = '--workers=4 --bind=0.0.0.0:5000 --timeout=120 --access-logfile=logs/access.log --error-logfile=logs/error.log'
        gunicorn_run()
        
    except ImportError:
        print("=" * 70)
        print("⚠️  未检测到 Gunicorn，使用 Flask 开发服务器")
        print("=" * 70)
        print("💡 建议安装：pip install gunicorn")
        print("=" * 70)
        
        # 使用 Flask 内置服务器
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=False,  # 生产环境关闭 debug
            threaded=True
        )
