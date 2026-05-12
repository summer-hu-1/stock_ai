"""
认证数据库初始化脚本
运行方式: python scripts/init_auth.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from database.db import init_db, get_db, create_user, get_user_count

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "123456"

def init_auth_db():
    print("=" * 50)
    print("🔧 认证数据库初始化")
    print("=" * 50)

    print("\n📦 初始化数据库表...")
    init_db()
    print("✅ 数据库表创建成功")

    db = next(get_db())
    user_count = get_user_count(db)

    if user_count == 0:
        print(f"\n📝 创建默认管理员账户...")
        print(f"   用户名: {DEFAULT_ADMIN_USERNAME}")
        print(f"   密码: {DEFAULT_ADMIN_PASSWORD}")

        password_hash = bcrypt.hashpw(
            DEFAULT_ADMIN_PASSWORD.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        create_user(
            db,
            username=DEFAULT_ADMIN_USERNAME,
            password_hash=password_hash,
            email="admin@example.com",
            name="管理员"
        )

        user_count = get_user_count(db)
        print(f"\n✅ 管理员账户创建成功！")
        print(f"   当前用户数: {user_count}")
    else:
        print(f"\nℹ️ 数据库中已有 {user_count} 个用户，跳过创建默认账户")

    print("\n" + "=" * 50)
    print("✅ 初始化完成！")
    print("=" * 50)
    print(f"\n🚀 启动应用: python -m streamlit run app.py")
    print(f"🔐 登录信息: admin / 123456")

if __name__ == "__main__":
    init_auth_db()
