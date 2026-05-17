import os, sys, time, json, warnings, requests, pandas as pd
from pathlib import Path
from datetime import datetime

warnings.filterwarnings('ignore')

DATA_DIR = Path('data/cn/daily')
DATALAKE_DIR = Path('datalake/cn/daily')
START_DATE = '2023-01-13'
END_DATE = datetime.now().strftime('%Y-%m-%d')

PREFIX_TO_DIR = {
    '000': ('sz_main', 'SZ'), '001': ('sz_main', 'SZ'), '002': ('sz_sme', 'SZ'),
    '003': ('sz_main', 'SZ'), '300': ('sz_gem', 'SZ'), '301': ('sz_gem', 'SZ'),
    '600': ('sh_main', 'SH'), '601': ('sh_main', 'SH'), '603': ('sh_main', 'SH'),
    '605': ('sh_main', 'SH'), '688': ('sh_star', 'SH'), '689': ('sh_star', 'SH'),
}

def get_code_info(code):
    prefix = code[:3]
    return PREFIX_TO_DIR.get(prefix, ('unknown', 'UNKNOWN'))

def get_stock_data_from_tencent(code, start_date, end_date):
    session = requests.Session()
    session.trust_env = False
    session.proxies = {}

    if code.startswith('6'):
        market = 'sh'
    else:
        market = 'sz'

    url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param={market}{code},day,{start_date},{end_date},1000,qfq'

    try:
        r = session.get(url, timeout=10)
        text = r.text
        if text.startswith('kline_dayqfq='):
            text = text[len('kline_dayqfq='):]

        data = json.loads(text)
        if data.get('code') == 0 and data.get('data'):
            stock_data = data['data'].get(f'{market}{code}', {})
            qfqday = stock_data.get('qfqday', [])

            if not qfqday:
                return None

            # 统一处理为6列：日期, 开, 收, 高, 低, 量
            cleaned_data = []
            for row in qfqday:
                if len(row) >= 6:
                    cleaned_data.append([row[0], row[1], row[2], row[3], row[4], row[5]])

            df = pd.DataFrame(cleaned_data, columns=['date', 'open', 'close', 'high', 'low', 'volume'])

            df['date'] = pd.to_datetime(df['date'])
            df['open'] = df['open'].astype(float)
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['volume'] = df['volume'].astype(float)

            df['amount'] = df['volume'] * df['close']
            df['turnover_rate'] = 0.0
            df['change_pct'] = df['close'].pct_change() * 100
            df['amplitude'] = ((df['high'] - df['low']) / df['low']) * 100

            df = df.sort_values('date')
            return df
    except Exception as e:
        print(f'  错误: {e}')

    return None

code = '002624'
df = get_stock_data_from_tencent(code, START_DATE, END_DATE)
if df is not None and not df.empty:
    print(f'{code}: ✅ {len(df)} 条数据')
    csv_dir, exchange = get_code_info(code)
    print(f'目录: {csv_dir}, 交易所: {exchange}')
    print(df.tail(2))
else:
    print(f'{code}: ❌ 获取数据失败')