"""
修复 admin 用户角色脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin_auth.db import get_session
from admin_auth.repository import AdminRepository

db = get_session()
user = AdminRepository.get_user_by_username(db, "admin")
if user:
    print(f"当前用户: {user.username}, 角色: {user.role}")
    user.role = "admin"
    db.commit()
    print(f"已更新为: admin")
else:
    print("未找到 admin 用户")
db.close()
