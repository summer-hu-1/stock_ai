import yfinance as yf

from core.base_provider import BaseProvider


class USProvider(BaseProvider):
    """
    美股数据源 Provider
    使用 yfinance 获取美股行情数据
    """

    def get_stock_data(self, code: str) -> dict:
        """
        获取美股个股数据
        
        Args:
            code: 股票代码，如 AAPL, MSFT, GOOGL
        
        Returns:
            dict: 包含价格、涨跌幅等数据
        """
        code_upper = code.upper().strip()
        
        try:
            ticker = yf.Ticker(code_upper)
            info = ticker.info
            
            # 获取当前价格
            if info.get("currentPrice"):
                price = info["currentPrice"]
            elif info.get("regularMarketPrice"):
                price = info["regularMarketPrice"]
            else:
                # 获取历史数据的最新价格
                hist = ticker.history(period="1d")
                price = hist["Close"].iloc[-1] if not hist.empty else 0.0
            
            # 计算涨跌幅
            previous_close = info.get("previousClose", price)
            change_pct = ((price - previous_close) / previous_close) * 100 if previous_close != 0 else 0.0
            
            return {
                "code": code_upper,
                "name": info.get("shortName", info.get("longName", code_upper)),
                "price": float(price),
                "change_pct": float(change_pct),
                "volume": float(info.get("volume", 0)),
                "high": float(info.get("dayHigh", 0)),
                "low": float(info.get("dayLow", 0)),
                "open": float(info.get("regularMarketOpen", 0)),
                "market": "US",
                "market_cap": float(info.get("marketCap", 0)),
                "pe_ratio": float(info.get("trailingPE", 0)),
                "dividend_yield": float(info.get("dividendYield", 0)),
            }
        except Exception as e:
            # 如果获取失败，返回模拟数据
            return {
                "code": code_upper,
                "name": f"US Stock {code_upper}",
                "price": 0.0,
                "change_pct": 0.0,
                "volume": 0.0,
                "high": 0.0,
                "low": 0.0,
                "open": 0.0,
                "market": "US",
                "market_cap": 0.0,
                "pe_ratio": 0.0,
                "dividend_yield": 0.0,
            }

    def get_market_sentiment(self) -> dict:
        """获取美股市场情绪数据"""
        # 获取标普500指数作为市场参考
        try:
            spy = yf.Ticker("SPY")
            info = spy.info
            
            price = info.get("currentPrice", info.get("regularMarketPrice", 0))
            previous_close = info.get("previousClose", price)
            change_pct = ((price - previous_close) / previous_close) * 100 if previous_close != 0 else 0.0
            
            return {
                "market": "US",
                "index_name": "S&P 500",
                "index_price": float(price),
                "index_change_pct": float(change_pct),
                "bullish": change_pct > 0,
            }
        except Exception:
            return {
                "market": "US",
                "index_name": "S&P 500",
                "index_price": 0.0,
                "index_change_pct": 0.0,
                "bullish": None,
            }

    def get_sectors(self) -> list:
        """获取美股板块数据"""
        try:
            # 获取热门ETF作为板块代理
            popular_etfs = ["XLE", "XLF", "XLK", "XLP", "XLV", "XLY", "XLU", "XLB"]
            
            sectors = []
            for etf in popular_etfs[:5]:
                ticker = yf.Ticker(etf)
                info = ticker.info
                price = info.get("currentPrice", info.get("regularMarketPrice", 0))
                previous_close = info.get("previousClose", price)
                change_pct = ((price - previous_close) / previous_close) * 100 if previous_close != 0 else 0.0
                
                sectors.append({
                    "name": info.get("shortName", etf),
                    "change_pct": float(change_pct),
                    "market": "US",
                })
            
            return sectors
        except Exception:
            return []

    def get_market_volume(self) -> float:
        """获取美股全市场成交额（亿美元）"""
        try:
            # 使用几只大盘股估算
            tickers = yf.Tickers("AAPL MSFT GOOGL AMZN META TSLA NVDA JPM")
            total_volume = 0
            
            for ticker in tickers.tickers.values():
                info = ticker.info
                total_volume += info.get("volume", 0) * info.get("currentPrice", 0)
            
            return float(total_volume / 100000000)  # 转换为亿美元
        except Exception:
            return 0.0
