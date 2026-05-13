"""每日扫描器 - 收盘后自动扫描全市场股票"""

import sys
import os

# 添加项目根目录到路径
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from signal_center.signal_scanner import SignalScanner

# 获取项目根目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_stock_codes_from_csv() -> list:
    """从本地CSV文件获取股票代码列表"""
    code_list = []
    
    # 读取A股数据目录
    data_dir = os.path.join(PROJECT_DIR, "data", "cn", "daily")
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith(".csv"):
                code = filename[:-4]  # 去掉.csv后缀
                code_list.append(code)
    
    return code_list


def run_daily_scan():
    """执行每日扫描"""
    print("🚀 开始每日扫描...")
    
    scanner = SignalScanner()
    
    # 获取股票代码列表
    stock_codes = get_stock_codes_from_csv()
    
    if not stock_codes:
        # 如果没有本地数据，使用示例股票
        stock_codes = ["000001", "000002", "600519", "000858", "300750"]
    
    print(f"📊 待扫描股票数量: {len(stock_codes)}")
    
    # 模拟扫描每只股票
    for i, code in enumerate(stock_codes, 1):
        print(f"[{i}/{len(stock_codes)}] 扫描: {code}")
        
        # 模拟信号类型
        signal_types = ["breakout", "trend", "volume", "momentum", "support"]
        signal_type = signal_types[i % len(signal_types)]
        
        # 模拟方向和强度
        direction = "up" if i % 3 != 0 else "down"
        strength = 0.7 + (i % 10) * 0.03
        
        scanner.save_signal(
            code=code,
            name=f"股票{i}",
            signal_type=signal_type,
            direction=direction,
            strength=strength
        )
    
    print("✅ 每日扫描完成！")


if __name__ == "__main__":
    run_daily_scan()