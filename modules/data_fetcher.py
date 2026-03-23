"""
天盾 - 数据获取（Cloud 零依赖版）
三级降级：akshare → 新浪 → mock
"""
import os, pickle, warnings, requests, pandas as pd, numpy as np
from datetime import datetime, timedelta
from pathlib import Path

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
warnings.filterwarnings("ignore")

class StockDataFetcher:
    STOCK_POOL = {
        '600519': '贵州茅台', '300750': '宁德时代', '002594': '比亚迪',
        '000858': '五粮液', '601318': '中国平安', '600036': '招商银行',
        '000333': '美的集团', '600276': '恒瑞医药', '002415': '海康威视',
        '300059': '东方财富'
    }

    # ------------ 对外 API ------------
    def get_stock_list(self):
        return [{"code": c, "name": n} for c, n in self.STOCK_POOL.items()]

    def search_stock(self, keyword):
        kw = str(keyword)
        return [{"code": c, "name": n} for c, n in self.STOCK_POOL.items()
                if kw in c or kw in n]

    def get_daily_data(self, stock_code: str, days: int = 60):
        cache_file = CACHE_DIR / f"{stock_code}_price.pkl"
        try:
            import akshare as ak
            end = datetime.now().strftime('%Y%m%d')
            start = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start, end_date=end, adjust="qfq")
            df = df.rename(columns={'日期': 'date', '收盘': 'close', '开盘': 'open', '最高': 'high', '最低': 'low'})
            df['date'] = pd.to_datetime(df['date'])
            df = df[['date', 'open', 'high', 'low', 'close']].sort_values('date').tail(days)
            cache_file.write_bytes(pickle.dumps(df))
            return df
        except Exception as e:
            print(f"akshare failed: {e}, try sina")
        # 新浪备用
        try:
            if stock_code.startswith('6'):
                sym = f"sh{stock_code}"
            else:
                sym = f"sz{stock_code}"
            url = f"http://hq.sinajs.cn/list={sym}"
            r = requests.get(url, timeout=5)
            r.encoding = 'gbk'
            parts = r.text.split('"')[1].split(',')
            current = float(parts[3])
            rng = np.random.default_rng(abs(hash(stock_code)))
            dates = pd.date_range(end=datetime.now(), periods=days)
            prices = current * np.cumprod(1 + rng.normal(0.001, 0.025, days))
            df = pd.DataFrame({"date": dates, "close": prices, "open": prices*0.99, "high": prices*1.02
