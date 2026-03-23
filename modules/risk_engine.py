"""
天盾 - 风险分析引擎（Cloud 零依赖版）
"""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List

class RiskAnalysisEngine:
    WEIGHTS = {
        'price_volatility': 0.20,
        'financial_health': 0.25,
        'sentiment_risk':  0.20,
        'supply_chain':    0.20,
        'esg_risk':        0.15,
    }
    ALERT_THRESHOLDS = {'green': 30, 'yellow': 60, 'red': 100}

    def calculate_comprehensive_risk(self, stock_code: str, stock_name: str,
                                     price_data: pd.DataFrame,
                                     financials: Dict,
                                     sentiment_data: List[Dict],
                                     supply_chain_risk: float,
                                     esg_risk: float) -> Dict:
        price_risk   = self._price_risk(price_data)
        finance_risk = self._finance_risk(financials)
        sent_risk    = self._sent_risk(sentiment_data)
        supply_risk  = min(supply_chain_risk, 100)
        esg          = min(esg_risk, 100)

        risks = {'price_volatility': price_risk, 'financial_health': finance_risk,
                 'sentiment_risk': sent_risk, 'supply_chain': supply_risk, 'esg_risk': esg}
        max_risk = max(risks.values())
        weighted = sum(risks[k] * self.WEIGHTS[k] for k in risks)
        comprehensive = 0.6 * max_risk + 0.4 * weighted * 100 / sum(self.WEIGHTS.values())
        comprehensive = min(max(comprehensive, 0), 100)

        level, level_name = ('green','低风险') if comprehensive < 60 else (('yellow','中风险') if comprehensive < 80 else ('red','高风险'))
        return {
            'stock_code': stock_code, 'stock_name': stock_name,
            'comprehensive_risk': round(comprehensive, 1),
            'risk_level': level, 'risk_level_name': level_name,
            'dimension_risks': risks,
            'calculation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    # -------------------- 私有估算 --------------------
    def _price_risk(self, price: pd.DataFrame) -> float:
        if len(price) < 5: return 50
        close = price['close'].values
        ret   = np.diff(close) / close[:-1]
        vol   = np.std(ret) * np.sqrt(252) * 100
        peak  = np.maximum.accumulate(close)
        draw  = (peak - close) / peak * 100
        score = min(vol * 2, 40) + min(np.max(draw) if len(draw) else 0, 40)
        return min(max(score, 0), 100)

    def _finance_risk(self, f: Dict) -> float:
        score = 0
        pe = f.get('pe_ratio', 25)
        if pe > 50: score += 30
        elif pe > 30: score += 15
        debt = f.get('debt_ratio', 50)
        if debt > 70: score += 30
        elif debt > 50: score += 15
        roe = f.get('roe', 15)
        if roe < 5: score += 25
        elif roe < 10: score += 10
        growth = f.get('profit_growth', 10)
        if growth < 0: score += 25
        elif growth < 5: score += 10
        return min(max(score, 0), 100)

    def _sent_risk(self, sent: List[Dict]) -> float:
        if not sent: return 50
        recent = [d['sentiment_score'] for d in sent[-7:]]
        avg   = np.mean(recent)
        neg   = sum(1 for d in sent[-7:] if d['sentiment_score'] < -0.2)
        score = (1 - avg) * 30 + neg * 5
        return min(max(score, 0), 100)

    # -------------------- 可视化用历史 --------------------
    def calculate_30day_risk_history(self, code, name, price, sent):
        hist = []
        for i in range(1, min(31, len(price)+1)):
            sub_p = price.iloc[:i]
            sub_s = sent[:i]
            if len(sub_p) >= 5:
                r = self.calculate_comprehensive_risk(
                    code, name, sub_p,
                    {'pe_ratio':25,'debt_ratio':50,'roe':15,'profit_growth':10},
                    sub_s, 40, 40
                )
                hist.append({
                    'date': sub_p['date'].iloc[-1].strftime('%Y-%m-%d'),
                    'risk_score': r['comprehensive_risk'],
                    'price': float(sub_p['close'].iloc[-1])
                })
        return hist
