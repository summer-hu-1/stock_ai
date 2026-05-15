from typing import List, Optional, Union
from datetime import datetime
import os
import pandas as pd

from ..models import OHLCV


class CSVAdapter:
    MARKET_DIR_MAP = {
        "cn": "cn/daily",
        "hk": "hk/daily",
        "us": "us/daily"
    }

    SUB_DIRS = {
        '000': 'cn/daily/sz_main', '001': 'cn/daily/sz_main', '002': 'cn/daily/sz_sme',
        '003': 'cn/daily/sz_main', '004': 'cn/daily/sz_main', '005': 'cn/daily/sz_main',
        '006': 'cn/daily/sz_main', '007': 'cn/daily/sz_main', '008': 'cn/daily/sz_main',
        '300': 'cn/daily/sz_gem', '301': 'cn/daily/sz_gem',
        '600': 'cn/daily/sh_main', '601': 'cn/daily/sh_main', '603': 'cn/daily/sh_main', '605': 'cn/daily/sh_main',
        '688': 'cn/daily/sh_star', '689': 'cn/daily/sh_star',
    }

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_dir = os.path.dirname(os.path.dirname(script_dir))
            self.base_data_dir = os.path.join(project_dir, "data")
        else:
            self.base_data_dir = data_dir

    def _get_sub_dir(self, code: str) -> str:
        prefix = code[:3]
        return self.SUB_DIRS.get(prefix, 'cn/daily')

    def get_stock_daily(
        self,
        code: str,
        market: str = "cn",
        start_date: Union[str, datetime] = None,
        end_date: Union[str, datetime] = None
    ) -> List[OHLCV]:
        code = str(code).zfill(6)

        if market == "cn":
            market_subdir = self._get_sub_dir(code)
        else:
            market_subdir = self.MARKET_DIR_MAP.get(market, "cn/daily")

        data_dir = os.path.join(self.base_data_dir, market_subdir)
        path = os.path.join(data_dir, f"{code}.csv")

        if not os.path.exists(path):
            return []

        try:
            df = pd.read_csv(path)

            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])

                if start_date:
                    start_date = self._parse_date(start_date)
                    df = df[df['date'] >= start_date]

                if end_date:
                    end_date = self._parse_date(end_date)
                    df = df[df['date'] <= end_date]

            return self._df_to_ohlcv(df, code)

        except Exception as e:
            print(f"读取股票 {code} 数据失败：{e}")
            return []

    def _df_to_ohlcv(self, df: pd.DataFrame, code: str) -> List[OHLCV]:
        result = []
        for _, row in df.iterrows():
            try:
                ohlcv = OHLCV(
                    code=code,
                    date=row.get('date', datetime.now()),
                    open=float(row.get('open', 0)),
                    high=float(row.get('high', 0)),
                    low=float(row.get('low', 0)),
                    close=float(row.get('close', 0)),
                    volume=float(row.get('volume', 0)),
                    amount=float(row.get('amount', 0)),
                    turnover_rate=float(row.get('turnover_rate', 0)),
                    price_change_pct=float(row.get('price_change_pct', 0)),
                    amplitude=float(row.get('amplitude', 0))
                )
                result.append(ohlcv)
            except Exception:
                continue
        return result

    def _parse_date(self, date: Union[str, datetime]) -> datetime:
        if isinstance(date, datetime):
            return date
        if isinstance(date, str):
            date = date.replace("/", "-")
            for fmt in ["%Y-%m-%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S"]:
                try:
                    return datetime.strptime(date, fmt)
                except ValueError:
                    continue
        return datetime.now()

    def get_stock_info(self, code: str, market: str = "cn") -> Optional[dict]:
        df = self.get_stock_daily(code, market)
        if not df:
            return None

        latest = df[-1]
        return {
            "code": code,
            "name": code,
            "market": market,
            "price": latest.close,
            "change_pct": latest.price_change_pct,
            "volume": latest.volume,
            "turnover_rate": latest.turnover_rate,
        }

    def list_available_stocks(self, market: str = "cn") -> List[str]:
        market_subdir = self.MARKET_DIR_MAP.get(market, "cn/daily")
        data_dir = os.path.join(self.base_data_dir, market_subdir)

        if not os.path.exists(data_dir):
            return []

        return [f.replace(".csv", "") for f in os.listdir(data_dir) if f.endswith(".csv")]