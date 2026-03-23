"""
天盾 · 多模态智能投资风控系统
交互版 - 直接复用本地 modules
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
# ↓↓↓ 你本地已有的 modules，无需改动
from modules.data_fetcher        import StockDataFetcher
from modules.risk_engine         import RiskAnalysisEngine
from modules.hidden_risk         import HiddenRiskDetector
from modules.supply_chain        import SupplyChainModel
from modules.multimedia          import MultimediaContent
from modules.visualizer          import RiskVisualizer

# -------------------- 页面配置 --------------------
st.set_page_config(page_title="🛡️天盾·交互版", layout="wide")

# -------------------- 缓存初始化 --------------------
@st.cache_resource
def load_modules():
    return {
        "fetcher": StockDataFetcher(),
        "engine" : RiskAnalysisEngine(),
        "hidden" : HiddenRiskDetector(),
        "supply" : SupplyChainModel(),
        "viz"    : RiskVisualizer(),
    }
mods = load_modules()

# -------------------- session 状态 --------------------
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = "600519"
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "user" not in st.session_state:
    st.session_state.user = None
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}
if "alerts" not in st.session_state:
    st.session_state.alerts = []

# -------------------- 侧边栏 · 用户+搜索+持仓 --------------------
with st.sidebar:
    # 1. 登录
    if not st.session_state.user:
        name = st.text_input("👤 输入昵称（模拟登录）")
        if st.button("登录"):
            st.session_state.user = name
            st.rerun()
    else:
        st.success(f"欢迎，{st.session_state.user}")
        if st.button("退出"):
            st.session_state.user = None
            st.rerun()

    st.markdown("---")

    # 2. 搜索 & 收藏
    st.markdown("### 🔍 股票搜索")
    query = st.text_input("代码/简称", placeholder="如 002594 或 比亚迪")
    if query:
        res = mods["fetcher"].search_stock(query)
        if res:
            for r in res:
                if st.button(f"{r['code']} {r['name']}", key=f"sr_{r['code']}",
                              use_container_width=True):
                    st.session_state.selected_stock = r["code"]
                    if r["code"] not in st.session_state.favorites:
                        st.session_state.favorites.append(r["code"])
        else:
            st.warning("未找到股票")

    # 3. 收藏夹
    if st.session_state.favorites:
        st.markdown("### ⭐ 我的收藏")
        for code in st.session_state.favorites:
            name = mods["fetcher"].STOCK_POOL.get(code, code)
            if st.button(f"{name}", key=f"fav_{code}", use_container_width=True):
                st.session_state.selected_stock = code

    st.markdown("---")

    # 4. 持仓录入
    if st.session_state.user:
        st.markdown("### 💼 我的持仓")
        opts = list(mods["fetcher"].STOCK_POOL.keys())
        code = st.selectbox("股票",
                            opts,
                            format_func=lambda x: f"{x} {mods['fetcher'].STOCK_POOL[x]}")
        shares = st.number_input("持股数量", min_value=0, step=100)
        cost = st.number_input("成本价（元）", min_value=0.0, step=0.1)
        if st.button("添加"):
            st.session_state.portfolio[code] = {"shares": shares, "cost": cost}
            st.success(f"已添加 {mods['fetcher'].STOCK_POOL[code]}")
        if st.session_state.portfolio:
            st.caption("当前持仓")
            for c, p in st.session_state.portfolio.items():
                st.caption(f"{mods['fetcher'].STOCK_POOL[c]}  {p['shares']}股  @{p['cost']}")

# -------------------- 主界面 --------------------
st.markdown("## 🛡️ 天盾 · 多模态智能投资风控（交互版）")
st.caption("融合财务/舆情/语音/图像/供应链 · 实时个性化预警")

code = st.session_state.selected_stock
name = mods["fetcher"].STOCK_POOL.get(code, code)

# 数据获取（缓存 5min）
@st.cache_data(ttl=300)
def get_full_analysis(_fetcher, _code, _name):
    price = _fetcher.get_daily_data(_code, 30)
    fin   = _fetcher.get_financial_metrics(_code)
    sent  = _fetcher.get_news_sentiment(_code, _name, 30)
    supply= mods["supply"].calculate_contagion_risk(_code)
    hidden= mods["hidden"].detect_hidden_risks(_code, _name, fin, price)
    comp  = mods["engine"].calculate_comprehensive_risk(_code, _name, price, fin, sent,
                                                       supply["contagion_risk"],
                                                       np.random.uniform(20,60))
    return {"price":price, "fin":fin, "sent":sent, "supply":supply, "hidden":hidden, "comp":comp}

with st.spinner("正在拉取多模态数据..."):
    ana = get_full_analysis(mods["fetcher"], code, name)

# 顶栏指标
c1,c2,c3 = st.columns(3)
comp = ana["comp"]
hidden = ana["hidden"]
supply = ana["supply"]
c1.metric("综合风险", f"{comp['comprehensive_risk']:.0f}")
c2.metric("隐性风险", f"{hidden['hidden_risk_score']:.0f}")
c3.metric("供应链传染", f"{supply['contagion_risk']:.0f}")

# 预警交互
st.markdown("#### 🚨 今日预警")
alert = {"code":code,"name":name,"level":"yellow","msg":"PEG>1.5 且估值分位>80%",
         "time":datetime.now().strftime("%m-%d %H:%M"),"status":"new"}
# 简单去重
if not any(a["code"]==code and a["msg"]==alert["msg"] for a in st.session_state.alerts):
    st.session_state.alerts.append(alert)

for a in st.session_state.alerts:
    if a["code"]!=code or a["status"]!="new": continue
    with st.expander(f"⚠️ {a['name']} · {a['msg']}"):
        c1,c2,c3=st.columns(3)
        if c1.button("已读",key=f"read_{code}"):
            a["status"]="read"; st.rerun()
        if c2.button("忽略",key=f"ign_{code}"):
            a["status"]="ignore"; st.rerun()
        if c3.button("我卖了",key=f"sold_{code}"):
            a["status"]="sold"; st.rerun()

# 标签页
tab1, tab2, tab3, tab4 = st.tabs(["📊风险总览","🔗产业链","🔍隐性风险","📹相关视频"])

with tab1:
    st.write("30日风险动画/雷达图/仪表盘（此处直接复用你原 `visualizer.py` 的函数）")
    # 例：mods['viz'].create_risk_gauge(...)
with tab2:
    fig = mods["supply"].create_industry_chain_visualization(code, name)
    st.plotly_chart(fig, use_container_width=True)
with tab3:
    fig = hidden["viz_chart"] = mods["hidden"].create_risk_comparison_chart(hidden)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### 🚩 风险信号")
    if hidden["red_flags"]:
        for f in hidden["red_flags"]:
            with st.expander(f"{f['type'].replace('_',' ')} · 得分{f['score']}"):
                st.write(f["detail"])
                st.info(f["explanation"])
with tab4:
    mc = MultimediaContent(code, name)
    interviews = mc.get_interview_content("high" if hidden["hidden_risk_score"]>60 else "low")
    for iv in interviews:
        with st.expander(f"🎤 {iv['title']} · {iv['speaker']}"):
            st.write(iv["summary"])
            if iv["risk_signals"]:
                st.warning("AI识别风险信号："+"；".join(iv["risk_signals"]))

st.markdown("---")
st.caption("🛡️ 天盾系统 · 数据仅供参考，投资需谨慎")
