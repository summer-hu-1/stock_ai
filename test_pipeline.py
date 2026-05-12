"""
测试 Pipeline 独立运行能力

验证标准：
1. 不启动 Streamlit 也能完成完整分析
2. 输出结构化的分析结果
3. 自动生成日志
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 初始化日志系统
from core.logging_config import setup_logging
setup_logging(level="INFO", log_file="logs/test_pipeline.log")

import logging
logger = logging.getLogger(__name__)

def test_pipeline():
    """测试 Pipeline 独立运行"""
    logger.info("🚀 开始测试 Pipeline...")
    
    try:
        # 创建 Pipeline 实例
        from core.analysis_pipeline import AnalysisPipeline
        pipeline = AnalysisPipeline()
        
        # 执行分析（使用有数据的股票）
        logger.info("🔍 正在分析股票: 600161")
        result = pipeline.analyze("600161")
        
        # 检查结果
        if result.get("success"):
            logger.info("✅ Pipeline分析成功！")
            
            # 打印结果结构
            print("\n" + "="*60)
            print("📊 分析结果结构")
            print("="*60)
            print(f"股票代码: {result['stock_code']}")
            print(f"综合评分: {result['score']}/100")
            print(f"风险等级: {result.get('risk_level', '未知')}")
            print(f"信号: {result.get('signal', '未知')}")
            print(f"耗时: {result.get('elapsed_time', 0):.2f}秒")
            print("\n📁 包含的分析模块:")
            print(f"  - 因子分析: {'✅' if result.get('factors') else '❌'}")
            print(f"  - 信号分析: {'✅' if result.get('signals') else '❌'}")
            print(f"  - 龙头识别: {'✅' if result.get('leaders') else '❌'}")
            print(f"  - 市场记忆: {'✅' if result.get('memory') else '❌'}")
            print(f"  - Agent分析: {'✅' if result.get('agent') else '❌'}")
            print("\n" + "="*60)
            
            # 验证是 dict 类型（后续会改成 dataclass）
            print(f"\n类型验证: {type(result)}")
            print(f"包含的键: {list(result.keys())}")
            
            return True
        else:
            logger.error(f"❌ Pipeline分析失败: {result.get('error')}")
            print(f"分析失败: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        print(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
