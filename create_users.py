import sqlite3
import bcrypt

conn = sqlite3.connect('data/auth.db')
cursor = conn.cursor()

# 创建密码哈希
password = '123456'
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# 插入管理员用户
try:
    cursor.execute('INSERT INTO users (username, password_hash, email, name, role, membership, daily_limit, today_used, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                  ('admin', hashed, 'admin@stockai.com', '管理员', 'admin', 'vip', 999, 0, 1))
    conn.commit()
    print('✅ 管理员用户创建成功')
except Exception as e:
    print(f'管理员用户已存在: {e}')

# 插入普通用户
try:
    cursor.execute('INSERT INTO users (username, password_hash, email, name, role, membership, daily_limit, today_used, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                  ('testuser', hashed, 'test@stockai.com', '测试用户', 'member', 'free', 3, 0, 1))
    conn.commit()
    print('✅ 普通用户创建成功')
except Exception as e:
    print(f'普通用户已存在: {e}')

# 显示用户列表
cursor.execute('SELECT username, role, membership FROM users')
users = cursor.fetchall()
print('当前用户列表:')
for user in users:
    print(f'  - {user[0]}: 角色={user[1]}, 会员={user[2]}')

conn.close()