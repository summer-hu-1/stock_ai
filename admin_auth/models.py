"""
admin_auth 数据模型 - Data Models
定义 Pydantic 模型用于输入输出
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    membership: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    role: str
    membership: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    vip_expire: Optional[datetime] = None
    token_balance: int
    daily_limit: int
    today_used: int

    class Config:
        from_attributes = True


class LogResponse(BaseModel):
    id: int
    username: str
    action: str
    stock_code: Optional[str] = None
    model_used: Optional[str] = None
    token_used: int
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisRecordResponse(BaseModel):
    id: int
    username: str
    stock_code: str
    stock_name: str
    analysis_type: str
    model_name: str
    token_used: int
    created_at: datetime

    class Config:
        from_attributes = True


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    today_analysis: int
    total_analysis: int