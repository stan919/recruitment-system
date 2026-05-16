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
        
        print(" ✅ 服务启动成功！")
        print(f"    访问地址：http://localhost:{os.environ.get('PORT', 5000)}")
        print(f"    ✨ 使用 Gunicorn WSGI 服务器")
        
        # Gunicorn 配置
        os.environ['GUNICORN_CMD_ARGS'] = '--workers=4 --bind=0.0.0.0:5000 --timeout=120 --access-logfile=logs/access.log --error-logfile=logs/error.log'
        gunicorn_run()
        
    except ImportError:
        try:
            # 在 Windows 环境下尝试使用高性能的 Waitress (支持并发)
            from waitress import serve
            print(" ✅ 服务启动成功！")
            print(f"    访问地址：http://localhost:{os.environ.get('PORT', 5000)}")
            print("    ⚡ 使用 Waitress WSGI 服务器")
            serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), threads=6)
        except ImportError:
            print(" ✅ 服务启动成功！")
            print(f"    访问地址：http://localhost:{os.environ.get('PORT', 5000)}")
            print("    ⚠️  使用 Flask 开发服务器（建议安装 waitress）")
            
            # 采用 Flask 内置单线程
            app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=False,  # 生产环境关闭 debug
            threaded=True
        )
