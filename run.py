#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from app import app
from database import Database

def main():
    """启动应用程序"""
    try:
        # 创建必要的目录
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('static', exist_ok=True)
        
        # 初始化数据库
        print("🔧 初始化数据库...")
        db = Database()
        db.init_tables()
        
        # 启动应用
        print("\n🚀 系统启动成功！")
        print("=" * 50)
        print("📌 访问地址:")
        print("   首页入口: http://localhost:5000/")
        print("   提交页面: http://localhost:5000/submit")
        print("   管理员登录: http://localhost:5000/login")
        print("=" * 50)
        print("🔐 登录凭证:")
        print("   管理员账号: 123456")
        print("   管理员密码: 123456")
        print("=" * 50)
        print("\n按 Ctrl+C 停止服务\n")
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
