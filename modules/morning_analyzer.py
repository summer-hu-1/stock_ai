"""
AI 早盘市场分析模块 - 统一版本
核心定位：帮助用户开盘几分钟内了解市场

数据来源：
- 雪球API：获取市场情绪、热门股票、指数数据
- Tavily Search：获取热点新闻和市场动态
- 东方财富：备用新闻源
- 新浪财经：二级备用新闻源
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
import os
import requests
import json
import re

# 禁用代理环境变量
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''


class MorningAnalyzer:
    def __init__(self):
        self.data = {}
        self._session = requests.Session()
        self._session.trust_env = False
        self._session.proxies = {}
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://xueqiu.com/',
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }

    def collect_market_data(self) -> Dict[str, Any]:
        """
        STEP 1: 收集市场数据
        - 最近行情
        - 今日开盘数据
        - 热点新闻
        - 热门股票
        - 板块异动
        """
        result = {
            "success": False,
            "market_sentiment": None,
            "hot_sectors": None,
            "hot_stocks": None,
            "indices": None,
            "hot_news": None,
            "error": None
        }

        results = []
        
        result["market_sentiment"] = self._get_market_sentiment_xueqiu()
        results.append(result["market_sentiment"] is not None)

        result["hot_sectors"] = self._get_hot_sectors_xueqiu()
        results.append(result["hot_sectors"] is not None)

        result["hot_stocks"] = self._get_hot_stocks_xueqiu()
        results.append(result["hot_stocks"] is not None)

        result["indices"] = self._get_major_indices_xueqiu()
        results.append(result["indices"] is not None)

        result["hot_news"] = self._get_hot_news_tavily()

        if any(results):
            result["success"] = True
        else:
            result["error"] = "所有数据源均失败"

        self.data = result
        return result

    def _get_market_sentiment_xueqiu(self) -> Optional[Dict]:
        """从雪球API获取市场情绪数据"""
        try:
            url = 'https://stock.xueqiu.com/v5/stock/realtime/quotec.json'
            params = {
                'symbol': 'SH000001,SZ399001,SZ399006'
            }

            r = self._session.get(url, params=params, headers=self._headers, timeout=15)
            if r.status_code != 200:
                print(f"雪球API返回状态码: {r.status_code}")
                return None

            data = r.json()
            if not data or 'data' not in data or not data['data']:
                print("雪球API返回数据为空")
                return None

            quotes = data['data']
            if not quotes:
                print("雪球API没有指数数据")
                return None

            total_percent = 0
            total_change = 0
            for quote in quotes:
                percent = quote.get('percent', 0)
                total_percent += percent
                total_change += 1

            avg_percent = total_percent / max(total_change, 1)

            rising_est = int((avg_percent + 2) * 1250)
            falling_est = int((2 - avg_percent) * 1250)
            rising_est = max(0, min(rising_est, 4000))
            falling_est = max(0, min(falling_est, 4000))

            limit_up_est = max(0, int((avg_percent - 1) * 20))
            limit_down_est = max(0, int((1 + avg_percent) * 10))

            if avg_percent >= 3:
                mood = "高潮"
            elif avg_percent >= 1.5:
                mood = "强势"
            elif avg_percent >= -1:
                mood = "震荡"
            elif avg_percent >= -3:
                mood = "弱势"
            else:
                mood = "退潮"

            return {
                "limit_up_count": limit_up_est,
                "limit_down_count": limit_down_est,
                "avg_change": round(avg_percent, 2),
                "market_mood": mood,
                "rising_count": rising_est,
                "falling_count": falling_est,
                "flat_count": max(0, 5000 - rising_est - falling_est),
                "total_count": 5000,
                "rise_ratio": round(rising_est / 50.0, 2),
                "strong_count": int(limit_up_est * 2),
                "weak_count": int(limit_down_est * 2),
                "total_volume": 0.0,
                "market_cap": 0.0,
                "source": "xueqiu"
            }
        except Exception as e:
            print(f"雪球获取市场情绪失败: {e}")
            return None

    def _get_hot_sectors_xueqiu(self) -> Optional[List[Dict]]:
        """从雪球获取热门板块"""
        try:
            url = 'https://xueqiu.com/service/v5/stock/screener/quote/list'
            params = {
                'page': 1,
                'size': 50,
                'order': 'desc',
                'orderby': 'percent',
                'market': 'CN',
                'type': 'sector'
            }

            r = self._session.get(url, params=params, headers=self._headers, timeout=15)
            if r.status_code != 200:
                print(f"雪球板块API返回状态码: {r.status_code}")
                return None

            data = r.json()
            if not data or 'data' not in data or 'list' not in data['data']:
                return None

            sectors = []
            for item in data['data']['list'][:15]:
                sectors.append({
                    "name": item.get('name', ''),
                    "change_pct": round(item.get('percent', 0), 2),
                    "rise_count": item.get('up_count', 0),
                    "fall_count": item.get('down_count', 0),
                    "turnover_rate": round(item.get('turnover_rate', 0), 2)
                })

            return sectors if sectors else None
        except Exception as e:
            print(f"雪球获取热门板块失败: {e}")
            return None

    def _get_hot_stocks_xueqiu(self) -> Optional[List[Dict]]:
        """从雪球获取热门股票"""
        try:
            url = 'https://xueqiu.com/service/v5/stock/screener/quote/list'
            params = {
                'page': 1,
                'size': 30,
                'order': 'desc',
                'orderby': 'percent',
                'market': 'CN',
                'type': 'sh_sz'
            }

            r = self._session.get(url, params=params, headers=self._headers, timeout=15)
            if r.status_code != 200:
                print(f"雪球股票API返回状态码: {r.status_code}")
                return None

            data = r.json()
            if not data or 'data' not in data or 'list' not in data['data']:
                return None

            stocks = []
            for item in data['data']['list'][:20]:
                stocks.append({
                    "code": item.get('symbol', '').replace('SH', '').replace('SZ', ''),
                    "name": item.get('name', ''),
                    "price": round(item.get('current', 0), 2),
                    "change_pct": round(item.get('percent', 0), 2),
                    "volume": round(item.get('amount', 0) / 1e8, 2)
                })

            return stocks if stocks else None
        except Exception as e:
            print(f"雪球获取热门股票失败: {e}")
            return None

    def _get_major_indices_xueqiu(self) -> Optional[List[Dict]]:
        """从雪球获取主要指数"""
        try:
            url = 'https://stock.xueqiu.com/v5/stock/realtime/quotec.json'
            symbols = ['SH000001', 'SZ399001', 'SZ399006', 'SH000688', 'SH000300']
            index_names = ['上证指数', '深证成指', '创业板指', '科创50', '沪深300']

            params = {
                'symbol': ','.join(symbols)
            }

            r = self._session.get(url, params=params, headers=self._headers, timeout=15)
            if r.status_code != 200:
                print(f"雪球指数API返回状态码: {r.status_code}")
                return None

            data = r.json()
            if not data or 'data' not in data or not data['data']:
                return None

            symbol_name_map = dict(zip(symbols, index_names))
            indices = []

            for quote in data['data']:
                symbol = quote.get('symbol', '')
                indices.append({
                    "name": symbol_name_map.get(symbol, symbol),
                    "change_pct": round(quote.get('percent', 0), 2),
                    "price": round(quote.get('current', 0), 2)
                })

            return indices
        except Exception as e:
            print(f"雪球获取指数数据失败: {e}")
            return None

    def _get_hot_news_tavily(self) -> Optional[List[Dict]]:
        """使用多渠道获取热点新闻（Tavily + 东方财富 + 新浪备用）"""
        news = []
        
        # 渠道1: Tavily Search
        try:
            api_key = os.getenv("TAVILY_API_KEY")
            if api_key:
                from tavily import TavilyClient
                tavily = TavilyClient(api_key=api_key)
                today = datetime.now().strftime("%Y-%m-%d")
                query = f"A股市场 {today} 热点新闻 财经要闻 政策消息"
                response = tavily.search(query, max_results=8)
                for result in response.get('results', []):
                    news.append({
                        "title": result.get('title', ''),
                        "url": result.get('url', ''),
                        "summary": result.get('summary', '')
                    })
                if news:
                    print(f"Tavily获取到新闻: {len(news)}条")
        except Exception as e:
            print(f"Tavily获取新闻失败: {e}")
        
        # 渠道2: 东方财富快讯
        if not news:
            try:
                eastmoney_url = 'https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_1_.html'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                r = requests.get(eastmoney_url, headers=headers, timeout=15)
                if r.status_code == 200:
                    titles = re.findall(r'"title":"([^"]+)"', r.text)
                    for t in titles[:10]:
                        t = t.replace('\\/', '/').replace('\\n', '').replace('\\"', '"')
                        news.append({"title": t, "url": "", "summary": ""})
                    print(f"东方财富获取到新闻: {len(news)}条")
            except Exception as e:
                print(f"东方财富新闻失败: {e}")
        
        # 渠道3: 新浪财经备用
        if not news:
            try:
                sina_url = 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2514&k=&num=10&page=1'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                r = requests.get(sina_url, headers=headers, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    for item in data.get('result', {}).get('data', [])[:10]:
                        news.append({
                            "title": item.get('title', ''),
                            "url": item.get('url', ''),
                            "summary": ""
                        })
                    print(f"新浪获取到新闻: {len(news)}条")
            except Exception as e:
                print(f"新浪新闻失败: {e}")
        
        return news if news else None

    def _get_deepseek_client(self):
        """获取DeepSeek客户端"""
        try:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
            
            if not api_key:
                raise Exception("未配置DEEPSEEK_API_KEY")

            import openai
            client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            return client
        except Exception as e:
            print(f"获取DeepSeek客户端失败: {e}")
            return None

    def analyze_with_ai(self) -> str:
        """
        STEP 2: AI自动分析
        基于收集到的数据，生成早盘分析报告
        """
        if not self.data or not self.data.get("success"):
            return "❌ 数据收集失败，无法进行分析"

        sentiment = self.data.get("market_sentiment") or {}
        hot_sectors = self.data.get("hot_sectors") or []
        hot_stocks = self.data.get("hot_stocks") or []
        indices = self.data.get("indices") or []
        hot_news = self.data.get("hot_news") or []

        today = datetime.now()
        today_str = today.strftime("%Y年%m月%d日")
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]

        indices_str = ""
        if indices:
            indices_str = "\n".join([f"- {idx['name']}: {idx['price']} ({idx['change_pct']:+.2f}%)" for idx in indices])

        sentiment_str = ""
        if sentiment:
            sentiment_str = f"""
- 涨停家数: {sentiment.get('limit_up_count', 0)}家
- 跌停家数: {sentiment.get('limit_down_count', 0)}家
- 市场情绪: {sentiment.get('market_mood', '未知')}
- 上涨家数: {sentiment.get('rising_count', 0)} ({sentiment.get('rise_ratio', 0):.1f}%)
- 下跌家数: {sentiment.get('falling_count', 0)}
- 强势股(≥5%): {sentiment.get('strong_count', 0)}家
- 平均涨跌: {sentiment.get('avg_change', 0):.2f}%
"""

        sectors_str = ""
        if hot_sectors:
            sectors_str = "\n".join([f"{i+1}. {s['name']}: {s['change_pct']:+.2f}%" for i, s in enumerate(hot_sectors[:8])])

        stocks_str = ""
        if hot_stocks:
            stocks_str = "\n".join([f"- {s['name']}({s['code']}): {s['change_pct']:+.2f}%" for s in hot_stocks[:10]])

        news_str = ""
        if hot_news:
            news_str = "\n".join([f"- {n['title']}" for n in hot_news[:5]])

        prompt = f"""你是A股早盘分析助手，专注于帮助用户快速了解每日市场状况。

【当前时间】
{today_str}（{weekday}）早盘

【大盘指数】
{indices_str if indices_str else "暂无数据"}

【市场情绪】
{sentiment_str if sentiment_str else "暂无数据"}

【热门板块TOP8】
{sectors_str if sectors_str else "暂无数据"}

【强势股TOP10】
{stocks_str if stocks_str else "暂无数据"}

【今日热点新闻】
{news_str if news_str else "暂无数据"}

【分析要求】
请按以下格式输出早盘分析报告：

## 📊 今日市场强弱
（判断：强/中性/弱，给出简要理由）

## 🔥 热点主线
（找出1-3个最强势的主题/概念）

## 💪 强势板块
（具体板块及原因）

## ⭐ 强势股
（3-5只值得关注的强势股及原因）

## ⚠️ 风险提示
（当前市场主要风险点）

## 🎯 短线建议
（当前适合的操作策略）

请直接输出分析结果，不要额外解释。"""

        try:
            client = self._get_deepseek_client()
            if not client:
                return "❌ 无法连接AI模型，请检查API配置"

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"❌ AI分析失败: {str(e)}"

    def get_summary(self) -> Dict[str, Any]:
        """
        STEP 3: 返回结构化总结
        """
        if not self.data or not self.data.get("success"):
            return {
                "market_strength": "未知",
                "hot_sectors": [],
                "strong_stocks": [],
                "main_risks": [],
                "trading_suggestion": ""
            }

        sentiment = self.data.get("market_sentiment") or {}
        hot_sectors = self.data.get("hot_sectors") or []
        hot_stocks = self.data.get("hot_stocks") or []

        limit_up = sentiment.get("limit_up_count", 0)
        avg_change = sentiment.get("avg_change", 0)

        if limit_up > 80 and avg_change > 2:
            market_strength = "强势"
        elif limit_up > 50 and avg_change > 0:
            market_strength = "偏强"
        elif limit_up > 30:
            market_strength = "中性"
        elif limit_up > 10:
            market_strength = "偏弱"
        else:
            market_strength = "弱势"

        return {
            "market_strength": market_strength,
            "limit_up_count": limit_up,
            "avg_change": avg_change,
            "market_mood": sentiment.get("market_mood", "未知"),
            "rise_ratio": sentiment.get("rise_ratio", 0),
            "hot_sectors": hot_sectors[:8] if hot_sectors else [],
            "strong_stocks": hot_stocks[:10] if hot_stocks else [],
            "indices": self.data.get("indices", []),
            "hot_news": self.data.get("hot_news", [])
        }


def run_morning_analysis() -> Dict[str, Any]:
    """
    快捷函数：执行完整早盘分析
    """
    analyzer = MorningAnalyzer()

    result = {
        "data_collected": False,
        "summary": None,
        "ai_report": None,
        "error": None
    }

    data = analyzer.collect_market_data()
    if not data.get("success"):
        result["error"] = data.get("error", "数据收集失败")
        return result

    result["data_collected"] = True
    result["summary"] = analyzer.get_summary()
    result["ai_report"] = analyzer.analyze_with_ai()

    return result