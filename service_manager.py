#!/usr/bin/env python3
"""
市场快照服务管理器

功能：
1. 启动服务（后台运行）
2. 停止服务
3. 查看服务状态
4. 设置开机自启
5. 移除开机自启

使用方法：
python service_manager.py start    # 启动服务
python service_manager.py stop     # 停止服务
python service_manager.py status   # 查看状态
python service_manager.py enable   # 设置开机自启
python service_manager.py disable  # 移除开机自启
"""

import os
import sys
import subprocess
import plistlib
from argparse import ArgumentParser


class ServiceManager:
    """
    服务管理器
    """
    
    def __init__(self):
        self.project_dir = os.path.dirname(__file__)
        self.script_path = os.path.join(self.project_dir, 'auto_snapshot.py')
        self.log_file = os.path.join(self.project_dir, 'logs', 'auto_snapshot.log')
        self.pid_file = os.path.join(self.project_dir, 'logs', 'auto_snapshot.pid')
        self.plist_path = os.path.expanduser('~/Library/LaunchAgents/com.stock_ai.auto_snapshot.plist')
        
    def _get_pid(self):
        """获取进程ID"""
        if os.path.exists(self.pid_file):
            with open(self.pid_file, 'r') as f:
                pid = f.read().strip()
            try:
                pid = int(pid)
                # 检查进程是否存在
                os.kill(pid, 0)
                return pid
            except (ValueError, OSError):
                return None
        return None
    
    def start(self):
        """启动服务"""
        pid = self._get_pid()
        if pid:
            print(f"❌ 服务已在运行中 (PID: {pid})")
            return False
        
        print("🚀 启动市场快照定时服务...")
        
        # 创建日志目录
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # 启动后台进程
        cmd = [
            sys.executable, self.script_path, '--start-service'
        ]
        
        with open(self.log_file, 'a') as f:
            proc = subprocess.Popen(cmd, stdout=f, stderr=f, cwd=self.project_dir)
        
        # 保存PID
        with open(self.pid_file, 'w') as f:
            f.write(str(proc.pid))
        
        print(f"✅ 服务已启动 (PID: {proc.pid})")
        print(f"📄 日志文件: {self.log_file}")
        return True
    
    def stop(self):
        """停止服务"""
        pid = self._get_pid()
        if not pid:
            print("❌ 服务未运行")
            return False
        
        print(f"⏹️ 停止服务 (PID: {pid})")
        
        try:
            os.kill(pid, 15)  # SIGTERM
            time.sleep(2)
            
            # 检查是否停止成功
            try:
                os.kill(pid, 0)
                os.kill(pid, 9)  # SIGKILL
            except OSError:
                pass
            
            os.remove(self.pid_file)
            print("✅ 服务已停止")
            return True
            
        except Exception as e:
            print(f"❌ 停止服务失败: {e}")
            return False
    
    def status(self):
        """查看服务状态"""
        pid = self._get_pid()
        
        if pid:
            print(f"✅ 服务正在运行")
            print(f"   PID: {pid}")
            print(f"   日志: {self.log_file}")
            
            # 显示最近的日志
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    lines = f.readlines()[-5:]
                print("\n📝 最近日志:")
                for line in lines:
                    print(f"   {line.strip()}")
        else:
            print("❌ 服务未运行")
            
            # 显示最近的日志
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    lines = f.readlines()[-10:]
                print("\n📝 最近日志:")
                for line in lines:
                    print(f"   {line.strip()}")
    
    def enable_autostart(self):
        """设置开机自启"""
        print("🔧 设置开机自启...")
        
        plist_content = {
            'Label': 'com.stock_ai.auto_snapshot',
            'ProgramArguments': [
                sys.executable,
                self.script_path,
                '--start-service'
            ],
            'WorkingDirectory': self.project_dir,
            'StandardOutPath': self.log_file,
            'StandardErrorPath': self.log_file,
            'RunAtLoad': True,
            'KeepAlive': True,
            'StartInterval': 60,
            'EnvironmentVariables': {
                'PATH': '/usr/bin:/bin:/usr/local/bin'
            }
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.plist_path), exist_ok=True)
        
        # 写入plist文件
        with open(self.plist_path, 'wb') as f:
            plistlib.dump(plist_content, f)
        
        # 加载plist
        subprocess.run(['launchctl', 'load', self.plist_path])
        
        print(f"✅ 开机自启已设置")
        print(f"   plist文件: {self.plist_path}")
    
    def disable_autostart(self):
        """移除开机自启"""
        print("🔧 移除开机自启...")
        
        if os.path.exists(self.plist_path):
            # 卸载plist
            subprocess.run(['launchctl', 'unload', self.plist_path], capture_output=True)
            os.remove(self.plist_path)
            print("✅ 开机自启已移除")
        else:
            print("❌ 未设置开机自启")


def main():
    parser = ArgumentParser(description='市场快照服务管理器')
    parser.add_argument('command', choices=['start', 'stop', 'status', 'enable', 'disable'])
    
    args = parser.parse_args()
    
    manager = ServiceManager()
    
    if args.command == 'start':
        manager.start()
    elif args.command == 'stop':
        manager.stop()
    elif args.command == 'status':
        manager.status()
    elif args.command == 'enable':
        manager.enable_autostart()
    elif args.command == 'disable':
        manager.disable_autostart()


if __name__ == "__main__":
    import time
    main()
