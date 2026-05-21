"""
AI 早盘市场分析模块 - 多数据源增强版
核心定位：帮助用户开盘几分钟内了解市场，获取精确、高密度信息

数据源策略（按优先级）：
1. AkShare - 真实A股市场数据（涨停/跌停/上涨/下跌家数）
2. 东方财富API - 实时行情、板块热度
3. 新浪财经 - 指数快照
4. 雪球API - 估算/兜底数据
5. Tavily Search - 财经新闻热点
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
import os
import requests
import json
import re

# 禁用代理
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ[key] = ''


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

    # ============================================================
    # STEP 1: 多源数据采集（按优先级逐级降级）
    # ============================================================
    def collect_market_data(self) -> Dict[str, Any]:
        result = {
            "success": False,
            "market_sentiment": None,
            "hot_sectors": None,
            "hot_stocks": None,
            "indices": None,
            "hot_news": None,
            "data_source": "unknown",
            "error": None
        }

        # --- 市场情绪（多级降级） ---
        sources_tried = []
        
        # 1) AkShare（最可靠：真实涨停/跌停/涨跌家数）
        sentiment = self._get_market_sentiment_akshare()
        if sentiment:
            result["market_sentiment"] = sentiment
            result["data_source"] = "akshare"
            sources_tried.append("akshare ✅")
        else:
            sources_tried.append("akshare ❌")
        
        # 2) 东方财富（真实行情API）
        if not result["market_sentiment"]:
            sentiment = self._get_market_sentiment_eastmoney()
            if sentiment:
                result["market_sentiment"] = sentiment
                result["data_source"] = "eastmoney"
                sources_tried.append("eastmoney ✅")
            else:
                sources_tried.append("eastmoney ❌")
        
        # 3) 新浪财经（简单指数快照）
        if not result["market_sentiment"]:
            sentiment = self._get_market_sentiment_sina()
            if sentiment:
                result["market_sentiment"] = sentiment
                result["data_source"] = "sina"
                sources_tried.append("sina ✅")
            else:
                sources_tried.append("sina ❌")
        
        # 4) 雪球（估算数据，兜底）
        if not result["market_sentiment"]:
            sentiment = self._get_market_sentiment_xueqiu()
            if sentiment:
                result["market_sentiment"] = sentiment
                result["data_source"] = "xueqiu"
                sources_tried.append("xueqiu ✅ (估算)")
            else:
                sources_tried.append("xueqiu ❌")

        print(f"📊 数据源尝试: {' → '.join(sources_tried)}")

        # --- 热门板块 ---
        result["hot_sectors"] = self._get_hot_sectors_eastmoney() or self._get_hot_sectors_xueqiu()

        # --- 热门股票 ---
        result["hot_stocks"] = self._get_hot_stocks_xueqiu()

        # --- 大盘指数 ---
        result["indices"] = self._get_major_indices_xueqiu()

        # --- 热点新闻 ---
        result["hot_news"] = self._get_hot_news()

        if result["market_sentiment"]:
            result["success"] = True
        else:
            result["error"] = "所有数据源均不可用"

        self.data = result
        return result

    # ============================================================
    # 数据源1: AkShare（最可靠）
    # ============================================================
    def _get_market_sentiment_akshare(self) -> Optional[Dict]:
        """使用 AkShare 获取真实 A 股市场情绪数据"""
        try:
            import akshare as ak
            # 获取A股实时行情总览（包含涨跌家数、涨停跌停）
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return None

            total = len(df)
            rising = len(df[df['涨跌幅'] > 0])
            falling = len(df[df['涨跌幅'] < 0])
            flat = total - rising - falling

            strong = len(df[df['涨跌幅'] >= 5])
            weak = len(df[df['涨跌幅'] <= -5])
            
            # 涨停/跌停判断（涨跌幅 >= 9.8% 视为涨停）
            limit_up = len(df[df['涨跌幅'] >= 9.8])
            limit_down = len(df[df['涨跌幅'] <= -9.8])
            
            avg_change = round(df['涨跌幅'].mean(), 2)
            total_volume = round(df['成交额'].sum() / 1e8, 2) if '成交额' in df.columns else 0

            # 判断市场情绪
            rise_ratio = round(rising / max(total, 1) * 100, 1)
            if limit_up > 80 and rise_ratio > 60:
                mood = "高潮"
            elif limit_up > 50 and rise_ratio > 40:
                mood = "强势"
            elif limit_up > 20:
                mood = "震荡"
            elif limit_up > 5:
                mood = "弱势"
            else:
                mood = "退潮"

            print(f"✅ AkShare: 涨停{limit_up}/跌停{limit_down}, 上涨{rising}/{falling}, 情绪{mood}")

            return {
                "limit_up_count": limit_up,
                "limit_down_count": limit_down,
                "avg_change": avg_change,
                "market_mood": mood,
                "rising_count": rising,
                "falling_count": falling,
                "flat_count": flat,
                "total_count": total,
                "rise_ratio": rise_ratio,
                "strong_count": strong,
                "weak_count": weak,
                "total_volume": total_volume,
                "market_cap": 0.0,
                "data_source": "akshare",
                "炸板率": None,
            }
        except Exception as e:
            print(f"AkShare 获取失败: {e}")
            return None

    # ============================================================
    # 数据源2: 东方财富 API（实时行情）
    # ============================================================
    def _get_market_sentiment_eastmoney(self) -> Optional[Dict]:
        """使用东方财富公开 API 获取市场概况"""
        try:
            # 东方财富市场总貌接口
            url = 'https://push2.eastmoney.com/api/qt/clt/get'
            params = {
                'fields': 'f3,f6,f12,f14,f15,f16,f17,f20',
                'pn': '1', 'pz': '5000',
                'po': '1', 'np': '1',
                'fltt': '2', 'invt': '2',
                'fid': 'f3',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                'fields': 'f12,f14,f2,f3,f15,f16,f17,f20',
            }
            r = requests.get(url, params=params, headers=self._headers, timeout=15)
            if r.status_code != 200:
                return None
            
            data = r.json()
            if not data or 'data' not in data or 'diff' not in data['data']:
                return None
            
            stocks = data['data']['diff']
            total = len(stocks)
            rising = sum(1 for s in stocks if s.get('f3', 0) > 0)
            falling = sum(1 for s in stocks if s.get('f3', 0) < 0)
            flat = total - rising - falling
            
            limit_up = sum(1 for s in stocks if s.get('f3', 0) >= 9.8)
            limit_down = sum(1 for s in stocks if s.get('f3', 0) <= -9.8)
            
            avg_change = round(sum(s.get('f3', 0) for s in stocks) / max(total, 1), 2)
            rise_ratio = round(rising / max(total, 1) * 100, 1)
            
            if limit_up > 80 and rise_ratio > 60:
                mood = "高潮"
            elif limit_up > 50 and rise_ratio > 40:
                mood = "强势"
            elif limit_up > 20:
                mood = "震荡"
            elif limit_up > 5:
                mood = "弱势"
            else:
                mood = "退潮"

            print(f"✅ 东方财富: 涨停{limit_up}/跌停{limit_down}, 上涨{rising}/{falling}, 情绪{mood}")

            return {
                "limit_up_count": limit_up,
                "limit_down_count": limit_down,
                "avg_change": avg_change,
                "market_mood": mood,
                "rising_count": rising,
                "falling_count": falling,
                "flat_count": flat,
                "total_count": total,
                "rise_ratio": rise_ratio,
                "strong_count": sum(1 for s in stocks if s.get('f3', 0) >= 5),
                "weak_count": sum(1 for s in stocks if s.get('f3', 0) <= -5),
                "total_volume": 0.0,
                "market_cap": 0.0,
                "data_source": "eastmoney",
                "炸板率": None,
            }
        except Exception as e:
            print(f"东方财富获取失败: {e}")
            return None

    # ============================================================
    # 数据源3: 新浪财经（指数快照）
    # ============================================================
    def _get_market_sentiment_sina(self) -> Optional[Dict]:
        """使用新浪财经 API 获取基本指数数据来估算情绪"""
        try:
            # 新浪指数接口
            url = 'https://hq.sinajs.cn/list=sh000001,sz399001,sz399006,sh000688,sh000300'
            headers = {'Referer': 'https://finance.sina.com.cn'}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200:
                return None
            
            # 解析新浪返回的文本格式
            lines = r.text.strip().split('\n')
            changes = []
            for line in lines:
                parts = line.split('"')[1].split(',') if '"' in line else []
                if len(parts) >= 4:
                    try:
                        price = float(parts[1])
                        prev_close = float(parts[2])
                        change_pct = round((price - prev_close) / prev_close * 100, 2)
                        changes.append(change_pct)
                    except (ValueError, IndexError):
                        continue
            
            if not changes:
                return None
            
            avg_pct = round(sum(changes) / len(changes), 2)
            
            # 根据指数平均涨跌估算市场情绪
            rising_est = int((avg_pct + 2) * 1000)
            falling_est = int((2 - avg_pct) * 1000)
            limit_up_est = max(0, int((avg_pct) * 30))
            
            if avg_pct >= 3:
                mood = "高潮"
            elif avg_pct >= 1.5:
                mood = "强势"
            elif avg_pct >= -1:
                mood = "震荡"
            elif avg_pct >= -3:
                mood = "弱势"
            else:
                mood = "退潮"

            print(f"✅ 新浪: 指数平均涨跌{avg_pct}%, 情绪{mood}")

            return {
                "limit_up_count": limit_up_est,
                "limit_down_count": max(0, int((-avg_pct) * 10)),
                "avg_change": avg_pct,
                "market_mood": mood,
                "rising_count": rising_est,
                "falling_count": falling_est,
                "flat_count": max(0, 5000 - rising_est - falling_est),
                "total_count": 5000,
                "rise_ratio": round(rising_est / 50.0, 1),
                "strong_count": int(limit_up_est * 2),
                "weak_count": max(0, int((-avg_pct) * 20)),
                "total_volume": 0.0,
                "market_cap": 0.0,
                "data_source": "sina",
                "炸板率": None,
            }
        except Exception as e:
            print(f"新浪获取失败: {e}")
            return None

    # ============================================================
    # 数据源4: 雪球（兜底估算）
    # ============================================================
    def _get_market_sentiment_xueqiu(self) -> Optional[Dict]:
        """从雪球API获取市场情绪数据（估算值）"""
        try:
            url = 'https://stock.xueqiu.com/v5/stock/realtime/quotec.json'
            params = {'symbol': 'SH000001,SZ399001,SZ399006'}
            r = self._session.get(url, params=params, headers=self._headers, timeout=15)
            if r.status_code != 200:
                return None
            data = r.json()
            if not data or 'data' not in data or not data['data']:
                return None
            quotes = data['data']
            if not quotes:
                return None

            total_percent = 0
            total_change = 0
            for quote in quotes:
                total_percent += quote.get('percent', 0)
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

            print(f"⚠️ 雪球估算: 指数平均{avg_percent:.2f}%, 情绪{mood}")

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
                "data_source": "xueqiu",
                "炸板率": None,
            }
        except Exception as e:
            print(f"雪球获取失败: {e}")
            return None

    # ============================================================
    # 热门板块（东方财富优先 → 雪球兜底）
    # ============================================================
    def _get_hot_sectors_eastmoney(self) -> Optional[List[Dict]]:
        """从东方财富获取热门概念板块"""
        try:
            url = 'https://push2.eastmoney.com/api/qt/clt/get'
            params = {
                'pn': '1', 'pz': '30',
                'po': '1', 'np': '1',
                'fltt': '2', 'invt': '2',
                'fid': 'f3',  # 按涨跌幅排序
                'fs': 'm:90+t:3',  # 概念板块
                'fields': 'f12,f14,f3,f104,f105',
            }
            r = requests.get(url, params=params, headers=self._headers, timeout=15)
            if r.status_code != 200:
                return None
            data = r.json()
            if not data or 'data' not in data or 'diff' not in data['data']:
                return None
            
            sectors = []
            for item in data['data']['diff'][:15]:
                sectors.append({
                    "name": item.get('f14', ''),
                    "change_pct": round(item.get('f3', 0), 2),
                    "rise_count": item.get('f104', 0),
                    "fall_count": item.get('f105', 0),
                    "turnover_rate": 0,  # 东方财富板块接口不直接返回换手率
                })
            
            print(f"✅ 东方财富板块: {len(sectors)}个")
            return sectors if sectors else None
        except Exception as e:
            print(f"东方财富板块获取失败: {e}")
            return None

    def _get_hot_sectors_xueqiu(self) -> Optional[List[Dict]]:
        """从雪球获取热门板块（兜底）"""
        try:
            url = 'https://xueqiu.com/service/v5/stock/screener/quote/list'
            params = {
                'page': 1, 'size': 50,
                'order': 'desc', 'orderby': 'percent',
                'market': 'CN', 'type': 'sector'
            }
            r = self._session.get(url, params=params, headers=self._headers, timeout=15)
            if r.status_code != 200:
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
            print(f"雪球板块获取失败: {e}")
            return None

    # ============================================================
    # 热门股票
    # ============================================================
    def _get_hot_stocks_xueqiu(self) -> Optional[List[Dict]]:
        """从雪球获取热门股票"""
        try:
            url = 'https://xueqiu.com/service/v5/stock/screener/quote/list'
            params = {
                'page': 1, 'size': 30,
                'order': 'desc', 'orderby': 'percent',
                'market': 'CN', 'type': 'sh_sz'
            }
            r = self._session.get(url, params=params, headers=self._headers, timeout=15)
            if r.status_code != 200:
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
            print(f"雪球股票获取失败: {e}")
            return None

    # ============================================================
    # 指数数据
    # ============================================================
    def _get_major_indices_xueqiu(self) -> Optional[List[Dict]]:
        """从雪球获取主要指数"""
        try:
            url = 'https://stock.xueqiu.com/v5/stock/realtime/quotec.json'
            symbols = ['SH000001', 'SZ399001', 'SZ399006', 'SH000688', 'SH000300']
            index_names = ['上证指数', '深证成指', '创业板指', '科创50', '沪深300']
            params = {'symbol': ','.join(symbols)}
            r = self._session.get(url, params=params, headers=self._headers, timeout=15)
            if r.status_code != 200:
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
            print(f"雪球指数获取失败: {e}")
            return None

    # ============================================================
    # 热点新闻（多渠道路由）
    # ============================================================
    def _get_hot_news(self) -> Optional[List[Dict]]:
        """多渠道获取热点新闻：Tavily → 东方财富 → 新浪"""
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
                    print(f"Tavily新闻: {len(news)}条")
        except Exception as e:
            print(f"Tavily新闻失败: {e}")
        
        # 渠道2: 东方财富快讯
        if not news:
            try:
                eastmoney_url = 'https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_1_.html'
                r = requests.get(eastmoney_url, headers=self._headers, timeout=15)
                if r.status_code == 200:
                    titles = re.findall(r'"title":"([^"]+)"', r.text)
                    for t in titles[:10]:
                        t = t.replace('\\/', '/').replace('\\n', '').replace('\\"', '"')
                        news.append({"title": t, "url": "", "summary": ""})
                    print(f"东方财富新闻: {len(news)}条")
            except Exception as e:
                print(f"东方财富新闻失败: {e}")
        
        # 渠道3: 新浪财经备用
        if not news:
            try:
                sina_url = 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2514&k=&num=10&page=1'
                r = requests.get(sina_url, headers=self._headers, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    for item in data.get('result', {}).get('data', [])[:10]:
                        news.append({
                            "title": item.get('title', ''),
                            "url": item.get('url', ''),
                            "summary": ""
                        })
                    print(f"新浪新闻: {len(news)}条")
            except Exception as e:
                print(f"新浪新闻失败: {e}")
        
        return news if news else None

    # ============================================================
    # STEP 2: AI 分析（高密度、简洁、操盘导向）
    # ============================================================
    def _get_deepseek_client(self):
        """获取DeepSeek客户端"""
        try:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
            if not api_key:
                raise Exception("未配置DEEPSEEK_API_KEY")
            import openai
            return openai.OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            print(f"DeepSeek客户端失败: {e}")
            return None

    def analyze_with_ai(self) -> str:
        """基于收集到的数据生成高密度早盘操盘报告"""
        if not self.data or not self.data.get("success"):
            return "❌ 数据收集失败，无法进行分析"

        sentiment = self.data.get("market_sentiment") or {}
        hot_sectors = self.data.get("hot_sectors") or []
        hot_stocks = self.data.get("hot_stocks") or []
        indices = self.data.get("indices") or []
        hot_news = self.data.get("hot_news") or []
        data_source = self.data.get("data_source", "unknown")

        today = datetime.now()
        today_str = today.strftime("%Y年%m月%d日")
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]

        # 数据来源标签
        source_labels = {
            "akshare": "📡 AkShare 实时全市场数据",
            "eastmoney": "📡 东方财富 实时行情API",
            "sina": "📡 新浪财经 指数数据",
            "xueqiu": "⚠️ 雪球估算数据（仅供参考）",
            "unknown": "❓ 未知数据源"
        }

        # 指数行
        indices_str = "\n".join(
            [f"- {idx['name']}: {idx['price']} ({idx['change_pct']:+.2f}%)" for idx in indices]
        ) if indices else "暂无"

        # 情绪行
        if sentiment:
            sentiment_str = (
                f"- 涨停: **{sentiment.get('limit_up_count', 0)}**家 | "
                f"跌停: **{sentiment.get('limit_down_count', 0)}**家\n"
                f"- 上涨: **{sentiment.get('rising_count', 0)}**家({sentiment.get('rise_ratio', 0)}%) | "
                f"下跌: **{sentiment.get('falling_count', 0)}**家\n"
                f"- 强势股(≥5%): **{sentiment.get('strong_count', 0)}**家 | "
                f"弱势股(≤-5%): **{sentiment.get('weak_count', 0)}**家\n"
                f"- 情绪判定: **{sentiment.get('market_mood', '未知')}** | "
                f"平均涨跌: **{sentiment.get('avg_change', 0)}%**"
            )
        else:
            sentiment_str = "暂无"

        # 板块
        sectors_str = "\n".join([
            f"{i+1}. {s['name']}: {s['change_pct']:+.2f}% (涨{s.get('rise_count', 0)}/跌{s.get('fall_count', 0)})"
            for i, s in enumerate(hot_sectors[:8])
        ]) if hot_sectors else "暂无"

        # 个股
        stocks_str = "\n".join([
            f"- {s['name']}({s['code']}): {s['change_pct']:+.2f}%, 成交{s.get('volume', 0)}亿"
            for s in (hot_stocks or [])[:10]
        ]) if hot_stocks else "暂无"

        # 新闻
        news_str = "\n".join([f"- {n['title']}" for n in (hot_news or [])[:5]]) if hot_news else "暂无"

        prompt = f"""你是A股职业操盘手级别的早盘分析助手。目标：开盘3分钟内让用户做出交易决策。

【时间】{today_str}（{weekday}）早盘
【数据来源】{source_labels.get(data_source, '未知')}
【数据精度】{data_source} {'✅ 真实全市场数据' if data_source in ('akshare', 'eastmoney') else '⚠️ 部分估算'}

【大盘指数】
{indices_str}

【市场情绪】
{sentiment_str}

【强势板块TOP8】
{sectors_str}

【涨跌幅领先股TOP10】
{stocks_str}

【今日要闻】
{news_str}

【输出要求 —— 高密度、简洁、直接可用于交易决策】
严格按以下格式输出，每段不超过3句话：

## 📊 今日市场强弱
（一句话定调：强/中性/弱 + 核心数字）

## 🔥 主线方向
（1-3个最确定的主线概念，为什么今天是它们）

## 💪 强势板块
（列出最强板块和领涨逻辑）

## ⭐ 核心标的
（基于板块逻辑，推荐3-5只最值得关注的方向和代表股，说明关注逻辑）

## ⚠️ 风险提示
（今天最大的1-2个风险点）

## 🎯 短线策略
（今天适合什么打法：追高/低吸/空仓/打板？给出明确策略）

直接输出，不要解释分析过程。"""

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

    # ============================================================
    # STEP 3: 结构化总结
    # ============================================================
    def get_summary(self) -> Dict[str, Any]:
        """返回结构化总结给 UI 层"""
        if not self.data or not self.data.get("success"):
            return {
                "market_strength": "未知",
                "hot_sectors": [],
                "indices": [],
                "hot_news": [],
                "market_sentiment": {},
                "data_source": "unknown",
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
        elif limit_up > 20:
            market_strength = "中性"
        elif limit_up > 5:
            market_strength = "偏弱"
        else:
            market_strength = "弱势"

        return {
            "market_strength": market_strength,
            "limit_up_count": limit_up,
            "limit_down_count": sentiment.get("limit_down_count", 0),
            "avg_change": avg_change,
            "market_mood": sentiment.get("market_mood", "未知"),
            "rise_ratio": sentiment.get("rise_ratio", 0),
            "strong_count": sentiment.get("strong_count", 0),
            "weak_count": sentiment.get("weak_count", 0),
            "data_source": self.data.get("data_source", "unknown"),
            "hot_sectors": hot_sectors[:10],
            "strong_stocks": hot_stocks[:10] if hot_stocks else [],
            "indices": self.data.get("indices", []) or [],
            "hot_news": self.data.get("hot_news", []) or [],
            "market_sentiment": sentiment,
        }


def run_morning_analysis() -> Dict[str, Any]:
    """快捷函数：执行完整早盘分析"""
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