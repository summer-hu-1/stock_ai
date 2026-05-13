"""
User Service - 用户服务

V9 Service Layer 组件，提供用户相关的统一接口：
1. 用户认证
2. 用户配额管理
3. 用户数据查询
4. 用户权限管理

核心原则：
- UI 不直接调用 auth/db 模块，通过 Service Layer 访问
- 统一错误处理和日志记录
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

# 设置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UserService:
    """
    用户服务
    
    提供用户相关的统一接口，隔离 UI 和底层认证/数据库模块
    """
    
    def __init__(self):
        """初始化用户服务"""
        logger.info("🔧 初始化用户服务")
    
    def login(self, username: str, password: str) -> Dict:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            Dict: 登录结果
        """
        logger.info(f"🔐 用户登录: {username}")
        
        try:
            from auth.auth import login
            success, message = login(username, password)
            
            if success:
                logger.info(f"✅ 用户 {username} 登录成功")
            else:
                logger.warning(f"❌ 用户 {username} 登录失败: {message}")
            
            return {
                "success": success,
                "message": message
            }
        
        except Exception as e:
            logger.error(f"❌ 用户登录异常: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def logout(self):
        """
        用户登出
        """
        logger.info("🔐 用户登出")
        
        try:
            from auth.auth import logout
            logout()
            logger.info("✅ 用户登出成功")
        
        except Exception as e:
            logger.error(f"❌ 用户登出异常: {e}")
    
    def is_logged_in(self) -> bool:
        """
        检查登录状态
        
        Returns:
            bool: 是否已登录
        """
        try:
            from auth.auth import is_logged_in
            return is_logged_in()
        
        except Exception as e:
            logger.error(f"❌ 检查登录状态异常: {e}")
            return False
    
    def get_current_user(self) -> Optional[Dict]:
        """
        获取当前用户信息
        
        Returns:
            Dict: 用户信息
        """
        logger.debug(f"👤 获取当前用户")
        
        try:
            from auth.auth import get_current_user
            user = get_current_user()
            
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at
                }
            
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取当前用户异常: {e}")
            return None
    
    def get_user_quota_info(self) -> Dict:
        """
        获取用户配额信息
        
        Returns:
            Dict: 配额信息
        """
        logger.debug(f"📊 获取用户配额信息")
        
        try:
            from auth.auth import get_user_quota_info
            return get_user_quota_info()
        
        except Exception as e:
            logger.error(f"❌ 获取用户配额信息异常: {e}")
            return {
                "used": 0,
                "limit": 10,
                "unlimited": False
            }
    
    def can_analyze(self) -> Dict:
        """
        检查是否可以进行分析
        
        Returns:
            Dict: 是否可以分析
        """
        logger.debug(f"🔍 检查分析权限")
        
        try:
            from auth.auth import can_analyze
            can_do, message = can_analyze()
            
            return {
                "can_analyze": can_do,
                "message": message
            }
        
        except Exception as e:
            logger.error(f"❌ 检查分析权限异常: {e}")
            return {
                "can_analyze": False,
                "message": str(e)
            }
    
    def record_analysis_usage(self):
        """
        记录分析使用次数
        """
        logger.debug(f"📝 记录分析使用")
        
        try:
            from auth.auth import record_analysis_usage
            record_analysis_usage()
        
        except Exception as e:
            logger.error(f"❌ 记录分析使用异常: {e}")
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        根据ID获取用户信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict: 用户信息
        """
        logger.debug(f"👤 根据ID获取用户: {user_id}")
        
        try:
            from database.db import get_db, get_user_by_id
            
            db = next(get_db())
            user = get_user_by_id(db, user_id)
            
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at
                }
            
            return None
        
        except Exception as e:
            logger.error(f"❌ 根据ID获取用户异常: {e}")
            return None
    
    def get_all_users(self) -> list:
        """
        获取所有用户列表
        
        Returns:
            List: 用户列表
        """
        logger.debug(f"👥 获取所有用户")
        
        try:
            from database.db import get_db, get_all_users
            
            db = next(get_db())
            users = get_all_users(db)
            
            result = []
            for user in users:
                result.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at
                })
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 获取所有用户异常: {e}")
            return []
    
    def create_user(self, username: str, password: str, email: str = None, full_name: str = None) -> Dict:
        """
        创建用户
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱
            full_name: 全名
        
        Returns:
            Dict: 创建结果
        """
        logger.info(f"➕ 创建用户: {username}")
        
        try:
            import bcrypt
            from database.db import get_db, create_user, get_user_by_username
            
            db = next(get_db())
            
            # 检查用户是否已存在
            existing_user = get_user_by_username(db, username)
            if existing_user:
                return {
                    "success": False,
                    "message": "用户名已存在"
                }
            
            # 哈希密码
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            # 创建用户
            create_user(db, username, password_hash, email, full_name)
            
            logger.info(f"✅ 用户 {username} 创建成功")
            
            return {
                "success": True,
                "message": "用户创建成功"
            }
        
        except Exception as e:
            logger.error(f"❌ 创建用户异常: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def update_user(self, user_id: int, **kwargs) -> Dict:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            kwargs: 更新字段（email, full_name, is_active, is_admin）
        
        Returns:
            Dict: 更新结果
        """
        logger.info(f"✏️ 更新用户: {user_id}")
        
        try:
            from database.db import get_db, update_user
            
            db = next(get_db())
            
            # 过滤允许更新的字段
            allowed_fields = ['email', 'full_name', 'is_active', 'is_admin']
            update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_data:
                return {
                    "success": False,
                    "message": "没有有效的更新字段"
                }
            
            success = update_user(db, user_id, **update_data)
            
            if success:
                logger.info(f"✅ 用户 {user_id} 更新成功")
                return {
                    "success": True,
                    "message": "用户更新成功"
                }
            
            return {
                "success": False,
                "message": "用户不存在或更新失败"
            }
        
        except Exception as e:
            logger.error(f"❌ 更新用户异常: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def delete_user(self, user_id: int) -> Dict:
        """
        删除用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict: 删除结果
        """
        logger.info(f"🗑️ 删除用户: {user_id}")
        
        try:
            from database.db import get_db, delete_user
            
            db = next(get_db())
            
            success = delete_user(db, user_id)
            
            if success:
                logger.info(f"✅ 用户 {user_id} 删除成功")
                return {
                    "success": True,
                    "message": "用户删除成功"
                }
            
            return {
                "success": False,
                "message": "用户不存在或删除失败"
            }
        
        except Exception as e:
            logger.error(f"❌ 删除用户异常: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def toggle_user_active(self, user_id: int) -> Dict:
        """
        切换用户激活状态
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict: 切换结果
        """
        logger.info(f"🔄 切换用户状态: {user_id}")
        
        try:
            from database.db import get_db, toggle_user_active
            
            db = next(get_db())
            
            success, is_active = toggle_user_active(db, user_id)
            
            if success:
                logger.info(f"✅ 用户 {user_id} 状态已切换为 {'激活' if is_active else '禁用'}")
                return {
                    "success": True,
                    "message": f"用户已{'激活' if is_active else '禁用'}",
                    "is_active": is_active
                }
            
            return {
                "success": False,
                "message": "用户不存在"
            }
        
        except Exception as e:
            logger.error(f"❌ 切换用户状态异常: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def get_user_count(self) -> int:
        """
        获取用户数量
        
        Returns:
            int: 用户数量
        """
        try:
            from database.db import get_db, get_user_count
            
            db = next(get_db())
            count = get_user_count(db)
            return count
        
        except Exception as e:
            logger.error(f"❌ 获取用户数量异常: {e}")
            return 0


# 全局单例
_user_service_instance = None

def get_user_service() -> UserService:
    """获取用户服务单例"""
    global _user_service_instance
    if _user_service_instance is None:
        _user_service_instance = UserService()
    return _user_service_instance
