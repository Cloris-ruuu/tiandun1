"""
天盾 - 多模态智能投资风控系统
交互升级版：支持搜索、收藏、登录、持仓、预警反馈
"""

import streamlit as st
import pandas as pd
from modules.data_fetcher import StockDataFetcher
from modules.risk_engine import RiskAnalysisEngine
from modules.hidden_risk import HiddenRiskDetector
from modules.supply_chain import SupplyChainModel
from modules.multimedia import MultimediaContent
from modules.visualizer import RiskVisualizer

# -------------------- 页面配置 --------------------
st.set_page_config(
    page_title="🛡️ 天盾智能投资风控（交互版）",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- 初始化 --------------------
@st.cache_resource
def init_modules():
    return {
        'fetcher': StockDataFetcher(),
        'engine': RiskAnalysisEngine(),
        'hidden': HiddenRiskDetector(),
        'supply': SupplyChainModel(),
        'viz': RiskVisualizer(),
    }

modules = init_modules()
fetcher = modules['fetcher']

# -------------------- 会话状态初始化 --------------------
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = '600519'
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "user" not in st.session_state:
    st.session_state.user = None
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}
if "alerts" not in st.session_state:
    st.session_state.alerts = []

# -------------------- 侧边栏：用户系统 --------------------
with st.sidebar:
    st.markdown("### 👤 用户中心")
    if st.session_state.user is None:
        name = st.text_input("输入昵称（模拟登录）", placeholder="如：小明")
        if st.button("登录"):
            st.session_state.user = name
            st.rerun()
    else:
        st.success(f"已登录：{st.session_state.user}")
        if st.button("退出"):
            st.session_state.user = None
            st.rerun()

    # 收藏夹
    if st.session_state.favorites:
        st.markdown("### ⭐ 我的收藏")
        for code in st.session_state.favorites:
            name = fetcher.STOCK_POOL.get(code, code)
            if st.button(f"{name}", key=f"fav_{code}", use_container_width=True):
                st.session_state.selected_stock = code

    # 持仓管理
    if st.session_state.user:
        st.markdown("### 💼 我的持仓")
        code = st.selectbox("选择股票", list(fetcher.STOCK_POOL.keys()), format_func=lambda x: f"{x} {fetcher.STOCK_POOL[x]}")
        shares = st.number_input("持股数量", min_value=0, step=100)
        cost = st.number_input("成本价（元）", min_value=0.0, step=0.1)
        if st.button("添加持仓"):
            st.session_state.portfolio[code] = {"shares": shares, "cost": cost}
            st.success(f"已添加 {fetcher.STOCK_POOL[code]} {shares}股")

        if st.session_state.portfolio:
            st.markdown("#### 📦 当前持仓")
            for code, info in st.session_state.portfolio.items():
                st.write(f"{fetcher.STOCK_POOL[code]}: {info['shares']}股 @ {info['cost']}元")

    st.markdown("---")

    # 股票搜索
    st.markdown("### 🔍 股票搜索")
    query = st.text_input("输入代码或名称", placeholder="如：002594 或 比亚迪")
    if query:
        results = fetcher.search_stock(query)
        if results:
            for r in results:
                if st.button(f"{r['code']} - {r['name']}", key=f"search_{r['code']}", use_container
Width=True):
                    st.session_state.selected_stock = r['code']
                    if r['code'] not in st.session_state.favorites:
                        st.session_state.favorites.append(r['code'])
                        st.success(f"已收藏 {r['name']}")
        else:
            st.warning("未找到相关股票，试试热门股吧～")

    # 热门股票
    st.markdown("### 🔥 热门股票")
    for stock in fetcher.get_stock_list()[:5]:
        if st.button(f"{stock['code']} {stock['name']}", key=f"hot_{stock['code']}", use_container_width=True):
            st.session_state.selected_stock = stock['code']

# -------------------- 主内容区 --------------------
st.markdown("## 🛡️ 天盾智能投资风控系统（交互版）")
st.write("让普通人也能看懂的投资风险预警工具 · 支持持仓管理 · 个性化预警 · 可交互")

# 当前选中股票
stock_code = st.session_state.selected_stock
stock_name = fetcher.STOCK_POOL.get(stock_code, stock_code)

st.markdown(f"### 📊 {stock_code} - {stock_name} 风险分析")

# 模拟数据
price_data = fetcher.get_daily_data(stock_code, 30)
financials = fetcher.get_financial_metrics(stock_code)
sentiment_data = fetcher.get_news_sentiment(stock_code, stock_name, 30)

# 风险分析（复用原逻辑）
engine = RiskAnalysisEngine()
hidden_detector = HiddenRiskDetector()
supply_chain = SupplyChainModel()

comp_risk = engine.calculate_comprehensive_risk(
    stock_code, stock_name, price_data, financials, sentiment_data,
    supply_chain.calculate_contagion_risk(stock_code)['contagion_risk'],
    np.random.uniform(20, 60)
)
hidden_risk = hidden_detector.detect_hidden_risks(stock_code, stock_name, financials, price_data)

# 显示核心指标卡片
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("综合风险评分", f"{comp_risk['comprehensive_risk']:.0f}", delta=None)
with col2:
    st.metric("隐性风险评分", f"{hidden_risk['hidden_risk_score']:.0f}", delta=None)
with col3:
    st.metric("供应链风险", f"{supply_chain.calculate_contagion_risk(stock_code)['contagion_risk']:.0f}", delta=None)

# 预警卡片（可交互）
st.markdown("### 🚨 今日预警")
alert = {
    "code": stock_code,
    "name": stock_name,
    "level": "yellow",
    "msg": "PEG>1.5 且估值分位数>80%",
    "time": "2026-03-23 14:30",
    "status": "new"
}

if alert not in st.session_state.alerts:
    st.session_state.alerts.append(alert)

for a in st.session_state.alerts:
    if a['code'] == stock_code and a['status'] == "new":
        with st.expander(f"⚠️ {a['name']} 预警：{a['msg']}"):
            col1, col2, col3 = st.columns(3)
            if col1.button("已读", key=f"read_{a['code']}_{a['time']}"):
                a["status"] = "read"
            if col2.button("忽略", key=f"ignore_{a['code']}_{a['time']}"):
                a["status"] = "ignore"
            if col3.button("我卖了", key=f"sold_{a['code']}_{a['time']}"):
                a["status"] = "sold"
                st.success("已标记为卖出，后续不再提醒")

# 标签页（简化版）
tab1, tab2 = st.tabs(["📊 风险总览", "🔍 隐性风险"])

with tab1:
    st.write("这里可以放 30 天风险动画、雷达图、仪表盘等（复用你原来的图）")

with tab2:
    st.write("这里可以放隐性风险对比图、红旗列表、通俗解释等（复用你原来的图）")

st.markdown("---")
st.markdown("> 🛡️ 天盾智能投资风控系统 | 数据仅供参考，投资需谨慎")
