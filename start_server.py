#!/usr/bin/env python3
import os
import sys

# 将项目根目录添加到Python路径
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# 设置环境变量让Flask监听所有接口
os.environ['FLASK_HOST'] = '0.0.0.0'
os.environ['FLASK_PORT'] = '5000'
os.environ['FLASK_DEBUG'] = 'False'

# 导入并启动应用
from app import app

if __name__ == "__main__":
    print("🚀 启动 PolyAgent 生产服务器...")
    print("🔗 服务地址: http://0.0.0.0:5000")
    print("🌍 外部访问: 可通过服务器IP地址访问")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False) 