"""
供应链风险传染（Cloud 零依赖版）
"""
import numpy as np
import plotly.graph_objects as go

class SupplyChainModel:
    INDUSTRY_MAP = {
        '贵州茅台': {'industry': '白酒', 'upstream': [{'name': '高粱种植', 'impact': 0.3}, {'name': '包装材料', 'impact': 0.2}],
                   'downstream': [{'name': '经销商', 'impact': 0.4}, {'name': '电商平台', 'impact': 0.3}]},
        '宁德时代': {'industry': '动力电池', 'upstream': [{'name': '锂矿开采', 'impact': 0.4}, {'name': '正负极材料', 'impact': 0.3}],
                   'downstream': [{'name': '新能源汽车', 'impact': 0.6}, {'name': '储能系统', 'impact': 0.3}]},
        '比亚迪': {'industry': '新能源汽车', 'upstream': [{'name': '电池供应商', 'impact': 0.4}, {'name': '芯片/电子', 'impact': 0.3}],
                 'downstream': [{'name': '个人消费者', 'impact': 0.6}, {'name': '网约车平台', 'impact': 0.2}]},
    }

    def calculate_contagion_risk(self, stock_code: str):
        rng = np.random.default_rng(abs(hash(stock_code)))
        return {
            'stock_code': stock_code,
            'contagion_risk': round(rng.uniform(20, 60), 1),
            'affected_nodes': rng.integers(3, 9)
        }

    def get_industry_impact_map(self, stock_code: str, stock_name: str):
        if stock_name in self.INDUSTRY_MAP:
            return {**self.INDUSTRY_MAP[stock_name], 'center': {'name': stock_name, 'industry': self.INDUSTRY_MAP[stock_name]['industry']}}
        return {
            'center': {'name': stock_name, 'industry': '通用制造业'},
            'upstream': [{'name': '原材料', 'impact': 0.4}],
            'downstream': [{'name': '经销商', 'impact': 0.4}]
        }

    def create_industry_chain_visualization(self, stock_code: str, stock_name: str):
        data = self.get_industry_impact_map(stock_code, stock_name)
        labels = [data['center']['name']]
        parents = ['']
        values = [100]
        colors = ['#42A5F5']
        for u in data['upstream']:
            labels.append(u['name']); parents.append(data['center']['name']); values.append(u['impact']*100); colors.append('#AB47BC')
        for d in data['downstream']:
            labels.append(d['name']); parents.append(data['center']['name']); values.append(d['impact']*100); colors.append('#66BB6A')
        fig = go.Figure(go.Sunburst(labels=labels, parents=parents, values=values, marker_colors=colors))
        fig.update_layout(title=f'{stock_name} - 产业链影响地图', height=500)
        return fig

    def explain_industry_risk_for_common_user(self, stock_name: str):
        if stock_name in self.INDUSTRY_MAP:
            d = self.INDUSTRY_MAP[stock_name]
            expl = f"**行业**：{d['industry']}\n\n**上游供应商**：\n" + "\n".join([f"- {u['name']}" for u in d['upstream']]) + "\n\n**下游客户**：\n" + "\n".join([f"- {dd['name']}" for dd in d['downstream']])
            return expl
        return f"**{stock_name}** 产业数据暂缺"
