"""
天盾 - 多模态智能投资风控系统
Cloud-零依赖版：自带 3 级降级 + 一键 DEMO
运行：streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle, pathlib, warnings
warnings.filterwarnings("ignore")

# -------------------- 页面配置 --------------------
st.set_page_config(page_title="🛡️ 天盾智能投资风控", page_icon="🛡️", layout="wide")
st.markdown("""
<style>
.main-title { font-size: 32px; font-weight: bold; color: #1a237e; }
.subtitle { font-size: 16px; color: #666; margin-bottom: 20px; }
.metric-card {
    background: white; border-radius: 12px; padding: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 10px 0;
}
.alert-red { background: #FFEBEE; border-left: 5px solid #EF5350; padding: 15px; border-radius: 8px; }
.alert-yellow { background: #FFF8E1; border-left: 5px solid #FFCA28; padding: 15px; border-radius: 8px; }
.alert-green { background: #E8F5E9; border-left: 5px solid #66BB6A; padding: 15px; border-radius: 8px; }
</style>""", unsafe_allow_html=True)

# -------------------- 一键 DEMO --------------------
with st.sidebar:
    st.markdown("### 🚀 快速体验")
    if st.button("▶️ 一键 DEMO（零等待）"):
        st.session_state["demo"] = True
        st.session_state["selected_stock"] = "600519"

if st.session_state.get("demo"):
    st.info("✅ 当前为演示模式，所有数据已缓存，0 秒出图！")

# -------------------- 模块懒加载 --------------------
@st.cache_data(ttl=600)
def load_modules():
    from modules import StockDataFetcher, RiskAnalysisEngine, SupplyChainModel, HiddenRiskDetector, MultimediaContent, RiskVisualizer
    return StockDataFetcher(), RiskAnalysisEngine(), SupplyChainModel(), HiddenRiskDetector(), MultimediaContent("600519", "贵州茅台"), RiskVisualizer()

fetcher, engine, supply_chain, hidden_detector, multimedia, visualizer = load_modules()

# -------------------- 标题 & 股票选择 --------------------
if "selected_stock" not in st.session_state:
    st.session_state["selected_stock"] = "600519"
stock_code = st.session_state["selected_stock"]
stock_name = fetcher.STOCK_POOL.get(stock_code, stock_code)

st.markdown(f'<div class="main-title">🛡️ 天盾智能投资风控系统</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">让普通人也能看懂的投资风险预警工具 · 多模态分析 · 供应链传染监测 · 隐性风险识别</div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown(f"### 📊 {stock_code} - {stock_name} 风险分析")

# -------------------- 数据获取（带降级） --------------------
def mock_price_df(code, days=60):
    rng = np.random.default_rng(abs(hash(code)))
    dates = pd.date_range(end=datetime.now(), periods=days)
    base = rng.integers(20, 500)
    prices = base * np.cumprod(1 + rng.normal(0.001, 0.025, days))
    return pd.DataFrame({"date": dates, "close": prices, "open": prices*0.99, "high": prices*1.02, "low": prices*0.98})

def mock_financials(code):
    rng = np.random.default_rng(abs(hash(code)))
    return {"pe_ratio": round(rng.uniform(10, 45), 2), "debt_ratio": round(rng.uniform(30, 70), 2),
            "roe": round(rng.uniform(5, 25), 2), "profit_growth": round(rng.uniform(-10, 40), 2),
            "cash_profit_ratio": round(rng.uniform(0.4, 1.1), 2),
            "receivables_growth": round(rng.uniform(10, 60), 2),
            "revenue_growth": round(rng.uniform(5, 30), 2),
            "inventory_days": round(rng.uniform(60, 120), 1),
            "prev_inventory_days": 60, "executive_reduce_count": rng.integers(0, 5)}

def mock_sentiment(code, name, days=30):
    rng = np.random.default_rng(abs(hash(code)))
    dates = pd.date_range(end=datetime.now(), periods=days)
    keywords = ["业绩稳定增长", "股东减持", "订单饱满", "监管问询", "新产品发布"]
    return [{"date": d, "sentiment_score": round(rng.uniform(-0.4, 0.4), 3),
             "news_count": rng.integers(1, 6), "keyword": rng.choice(keywords)} for d in dates]

@st.cache_data(ttl=300)
def get_analysis(code):
    if st.session_state.get("demo"):
        price_data = mock_price_df(code)
        financials = mock_financials(code)
        sentiment_data = mock_sentiment(code, fetcher.STOCK_POOL.get(code, code))
    else:
        try:
            price_data = fetcher.get_daily_data(code)
            financials = fetcher.get_financial_metrics(code)
            sentiment_data = fetcher.get_news_sentiment(code, fetcher.STOCK_POOL.get(code, code))
        except Exception as e:
            st.warning(f"真实数据获取失败，自动切换到演示数据：{e}")
            price_data = mock_price_df(code)
            financials = mock_financials(code)
            sentiment_data = mock_sentiment(code, fetcher.STOCK_POOL.get(code, code))
                comp_risk = engine.calculate_comprehensive_risk(
        code, stock_name, price_data, financials, sentiment_data,
        supply_risk['contagion_risk'], np.random.uniform(20,60)
    )
    return {
        'price_data': price_data,
        'financials': financials,
        'sentiment_data': sentiment_data,
        'supply_chain': supply_risk,
        'hidden_risk': hidden_risk,
        'comprehensive': comp_risk,
    }

with st.spinner('🔍 正在分析风险...'):
    analysis = get_analysis(stock_code)

# -------------------- 核心指标卡片 --------------------
col1,col2,col3 = st.columns(3)
comp = analysis['comprehensive']
level_color = {'red':'#EF5350','yellow':'#FFCA28','green':'#66BB6A'}
level_emoji = {'red':'🔴','yellow':'🟡','green':'🟢'}

with col1:
    st.markdown(f"""
    <div class="metric-card" style="border-top:4px solid {level_color[comp['risk_level']]}">
        <div style="color:gray;font-size:14px">综合风险评分</div>
        <div style="font-size:36px;font-weight:bold;color:{level_color[comp['risk_level']]}">
            {level_emoji[comp['risk_level']]} {comp['comprehensive_risk']:.0f}
        </div>
        <div style="font-size:16px">{comp['risk_level_name']}</div>
    </div>""", unsafe_allow_html=True)

hid = analysis['hidden_risk']
with col2:
    st.markdown(f"""
    <div class="metric-card" style="border-top:4px solid {hid['risk_color']}">
        <div style="color:gray;font-size:14px">隐性风险评分</div>
        <div style="font-size:36px;font-weight:bold;color:{hid['risk_color']}">
            {hid['hidden_risk_score']:.0f}
        </div>
        <div style="font-size:16px">{hid['risk_label']}</div>
    </div>""", unsafe_allow_html=True)

sup = analysis['supply_chain']
with col3:
    st.markdown(f"""
    <div class="metric-card" style="border-top:4px solid #AB47BC">
        <div style="color:gray;font-size:14px">供应链风险</div>
        <div style="font-size:36px;font-weight:bold;color:#AB47BC">
            {sup['contagion_risk']:.0f}
        </div>
        <div style="font-size:16px">影响{sup['affected_nodes']}个节点</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# -------------------- TAB 标签 --------------------
tab1, tab2, tab3, tab4 = st.tabs(["📊 风险总览", "🔗 产业链", "🔍 隐性风险", "📹 相关视频"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        # 30 天风险动画（直接 mock）
        dates = pd.date_range(end=datetime.now(), periods=30)
        risk_hist = [{"date": d.strftime("%Y-%m-%d"),
                      "risk_score": comp['comprehensive_risk'] + np.random.uniform(-5,5),
                      "price": analysis['price_data']['close'].iloc[-30:].values[i] if len(analysis['price_data'])>=30 else 100+i*2}
                     for i, d in enumerate(dates)]
        fig = visualizer.create_30day_animation(risk_hist)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig_radar = visualizer.create_dimension_radar(comp['dimension_risks'])
        st.plotly_chart(fig_radar, use_container_width=True)

with tab2:
    impact_map = supply_chain.get_industry_impact_map(stock_code, stock_name)
    fig_ind = supply_chain.create_industry_chain_visualization(stock_code, stock_name)
    st.plotly_chart(fig_ind, use_container_width=True)
    st.markdown("#### ⚠️ 风险传导路径（通俗解释）")
    st.info(supply_chain.explain_industry_risk_for_common_user(stock_name))

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        fig_cmp = hidden_detector.create_risk_comparison_chart(hid)
        st.plotly_chart(fig_cmp, use_container_width=True)
    with col2:
        st.metric("表面健康度", f"{hid['surface_score']:.0f} 分")
        st.metric("真实健康度", f"{hid['real_score']:.0f} 分")
        st.metric("差距", f"{hid['gap']:.0f} 分", delta="-" if hid['gap']>20 else "正常")
    st.markdown("#### 🚩 风险信号列表")
    if hid['red_flags']:
        for f in hid['red_flags']:
            severity_css = "alert-red" if f['severity']=='high' else "alert-yellow"
            st.markdown(f"""<div class="{severity_css}">
                <strong>{f['type'].replace('_',' ').title()}</strong><br>{f['detail']}
            </div>""", unsafe_allow_html=True)
            with st.expander("💡 通俗解释"):
                st.markdown(f['explanation'])
    else:
        st.success("✅ 未发现明显隐性风险信号")
    st.info(hid['summary'])

with tab4:
    mm = MultimediaContent(stock_code, stock_name)
    interviews = mm.get_interview_content('high' if comp['comprehensive_risk']>60 else 'low' if comp['comprehensive_risk']<30 else 'neutral')
    for idx, iv in enumerate(interviews):
        mm.render_video_card(iv, f"{stock_code}_{idx}")

st.markdown("---")
st.caption("© 2025 天盾团队 | 数据仅供参考，投资需谨慎")

    supply_risk = supply_chain.calculate_contagion_risk(code)
    hidden_risk = hidden_detector.detect_hidden_risks(code, fetcher.STOCK_POOL.get(code, code), financials, price_data)
    comp_risk = engine.calculate_comprehensive_risk(code, fetcher.STOCK_PO
