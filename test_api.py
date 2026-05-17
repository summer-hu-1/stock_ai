import json
import requests

test_codes = ['001257', '001312', '301513', '920001', '688781', '600519']
for code in test_codes:
    session = requests.Session()
    session.trust_env = False
    session.proxies = {}

    if code.startswith('6') or code.startswith('9'):
        market = 'sh' if code.startswith('6') else 'bj'
    else:
        market = 'sz'

    url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param={market}{code},day,2023-01-13,2026-05-16,1000,qfq'

    try:
        r = session.get(url, timeout=10)
        text = r.text
        if text.startswith('kline_dayqfq='):
            text = text[len('kline_dayqfq='):]
        data = json.loads(text)

        if data.get('code') == 0 and data.get('data'):
            stock_data = data['data'].get(f'{market}{code}', {})
            qfqday = stock_data.get('qfqday', [])
            print(f'{code}: ✅ {len(qfqday)} 条数据')
        else:
            print(f'{code}: ❌ code={data.get("code")}, keys={list(data.keys())}')
    except Exception as e:
        print(f'{code}: ❌ {e}')