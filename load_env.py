"""
环境变量加载器
自动从 .env 文件加载环境变量
"""
import os
from pathlib import Path

_env_loaded = False  # 防止重复加载

def load_env():
    """从 .env 文件加载环境变量"""
    global _env_loaded
    
    # 如果已经加载过，直接返回
    if _env_loaded:
        return
    
    env_path = Path('.') / '.env'
    
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 解析 KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 只设置未存在的环境变量（命令行优先级更高）
                    if key not in os.environ:
                        os.environ[key] = value
                        print(f"✅ 已加载环境变量：{key}")
        
        print("\n✅ 环境变量加载完成")
        _env_loaded = True  # 标记已加载
    else:
        print("⚠️  未找到 .env 文件，使用默认配置")
        print("💡 建议运行：python setup_env.py 创建配置文件")
        _env_loaded = True

# 自动加载
load_env()
