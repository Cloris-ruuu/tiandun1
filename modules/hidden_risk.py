"""
隐性风险识别（Cloud 零依赖版）
"""
import numpy as np
import pandas as pd
from typing import Dict, List

class HiddenRiskDetector:
    RED_FLAGS = {
        'profit_cash_mismatch': {'name': '利润与现金流不匹配', 'weight': 0.25, 'threshold': 0.5},
        'receivables_surge': {'name': '应收账款异常增长', 'weight': 0.20, 'threshold': 1.5},
        'inventory_abnormal': {'name': '存货异常积压', 'weight': 0.15, 'threshold': 1.5},
        'high_debt_low_cash': {'name': '高负债低现金', 'weight': 0.20, 'threshold': 0.3},
        'executive_reduce': {'name': '高管密集减持', 'weight': 0.20, 'threshold': 3},
    }

    def detect_hidden_risks(self, stock_code: str, stock_name: str,
                           financials: Dict, price_data: pd.DataFrame = None) -> Dict:
        flags = []
        score = 0
        # 1. 利润现金流不匹配
        if financials.get('cash_profit_ratio', 0.8) < 0.5:
            flags.append({'type': 'profit_cash_mismatch', 'severity': 'high', 'score': 85,
                          'detail': f"经营现金流/净利润 = {financials.get('cash_profit_ratio', 0.3):.2f}",
                          'explanation': self._explain('profit_cash_mismatch')})
            score += 25
        # 2. 应收账款激增
        recv_g = financials.get('receivables_growth', 20)
        rev_g  = financials.get('revenue_growth', 20)
        if rev_g <= 0: ratio = 999
        else: ratio = recv_g / rev_g
        if ratio > 1.5:
            flags.append({'type': 'receivables_surge', 'severity': 'medium', 'score': 70,
                          'detail': f"应收账款增速 {recv_g:.1f}% 远超收入增速 {rev_g:.1f}%",
                          'explanation': self._explain('receivables_surge')})
            score += 20
        # 3. 存货异常
        prev = financials.get('prev_inventory_days', 60)
        curr = financials.get('inventory_days', 60)
        if prev > 0 and curr/prev > 1.5:
            flags.append({'type': 'inventory_abnormal', 'severity': 'medium', 'score': 65,
                          'detail': f"存货周转天数从{prev}天增至{curr}天",
                          'explanation': self._explain('inventory_abnormal')})
            score += 15
        # 4. 高负债低现金
        if financials.get('cash_coverage', 0.5) < 0.3:
            flags.append({'type': 'high_debt_low_cash', 'severity': 'high', 'score': 80,
                          'detail': f"货币资金仅覆盖{financials.get('cash_coverage', 0.2):.1f}倍流动负债",
                          'explanation': self._explain('high_debt_low_cash
