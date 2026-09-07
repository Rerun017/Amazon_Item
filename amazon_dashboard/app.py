import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="Amazon 电商数据分析看板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .kpi-card {
        background: linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .kpi-card .label { font-size: 13px; opacity: 0.85; margin-bottom: 6px; }
    .kpi-card .value { font-size: 28px; font-weight: 700; }
    .kpi-card .delta { font-size: 12px; margin-top: 4px; }
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #1a365d;
        margin: 24px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #e2e8f0;
    }
    .stMetric { background: #f7fafc; padding: 12px; border-radius: 8px; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 数据加载与缓存
# ============================================================
@st.cache_data
def load_data(data_file):
    df = pd.read_csv(data_file)
    df['OrderDate'] = pd.to_datetime(df['OrderDate'])
    df['Year'] = df['OrderDate'].dt.year
    df['Month'] = df['OrderDate'].dt.month
    df['YearMonth'] = df['OrderDate'].dt.to_period('M').astype(str)
    df['Quarter'] = df['OrderDate'].dt.to_period('Q').astype(str)
    df['DayOfWeek'] = df['OrderDate'].dt.day_name()
    df['IsDelivered'] = df['OrderStatus'] == 'Delivered'
    return df


# 数据文件路径：基于 app.py 所在目录自动定位，兼容本地和 Streamlit Cloud 部署
import os
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_data_paths = [
    os.path.join(_APP_DIR, "data", "Amazon_dataset.csv"),    # 相对于 app.py 文件位置
    r"C:\Users\wan01\AppData\Roaming\TRAE SOLO CN\ItemData\Amazon_dataset.csv",  # 本地备用
]
_data_file = None
for _p in _data_paths:
    if os.path.exists(_p):
        _data_file = _p
        break

if _data_file is None:
    st.error("❌ 找不到数据文件！请确认 data/Amazon_dataset.csv 存在。")
    st.info("部署到 Streamlit Cloud 时，请确保 GitHub 仓库中包含 data/Amazon_dataset.csv")
    st.stop()

df = load_data(_data_file)

# ============================================================
# 侧边栏筛选
# ============================================================
st.sidebar.title("🔧 筛选条件")

# 日期范围
min_date = df['OrderDate'].min()
max_date = df['OrderDate'].max()
date_range = st.sidebar.date_input(
    "📅 日期范围",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# 国家
countries = sorted(df['Country'].unique())
selected_countries = st.sidebar.multiselect(
    "🌍 国家",
    options=countries,
    default=countries
)

# 品类
categories = sorted(df['Category'].unique())
selected_categories = st.sidebar.multiselect(
    "📦 商品品类",
    options=categories,
    default=categories
)

# 订单状态
statuses = sorted(df['OrderStatus'].unique())
selected_statuses = st.sidebar.multiselect(
    "📋 订单状态",
    options=statuses,
    default=statuses
)

# 支付方式
payments = sorted(df['PaymentMethod'].unique())
selected_payments = st.sidebar.multiselect(
    "💳 支付方式",
    options=payments,
    default=payments
)

# 应用筛选
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (
        (df['OrderDate'] >= pd.Timestamp(start_date)) &
        (df['OrderDate'] <= pd.Timestamp(end_date)) &
        (df['Country'].isin(selected_countries)) &
        (df['Category'].isin(selected_categories)) &
        (df['OrderStatus'].isin(selected_statuses)) &
        (df['PaymentMethod'].isin(selected_payments))
    )
    filtered_df = df[mask].copy()
else:
    filtered_df = df.copy()

# 侧边栏信息
st.sidebar.markdown("---")
st.sidebar.info(f"""
**当前筛选数据量：**
- 订单数：{len(filtered_df):,}
- 客户数：{filtered_df['CustomerID'].nunique():,}
- 商品数：{filtered_df['ProductName'].nunique()}
""")

st.sidebar.markdown("---")
st.sidebar.markdown("👨‍💻 **分析者**：姚日亨")
st.sidebar.markdown("📧 1693600020@qq.com")


# ============================================================
# 标题
# ============================================================
st.title("📊 Amazon 电商数据分析看板")
st.markdown(f"<p style='color:#718096; margin-top:-10px;'>数据周期：{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} | 全量 10 万+ 订单记录</p>", unsafe_allow_html=True)


# ============================================================
# 模块一：核心KPI
# ============================================================
st.markdown("<div class='section-title'>🎯 核心经营指标</div>", unsafe_allow_html=True)

# 计算KPI
total_gmv = filtered_df['TotalAmount'].sum()
total_orders = len(filtered_df)
total_customers = filtered_df['CustomerID'].nunique()
aov = total_gmv / total_orders if total_orders > 0 else 0
delivered_rate = filtered_df['IsDelivered'].mean() * 100
avg_discount = filtered_df['Discount'].mean() * 100

# 同比计算（选前后各一半）
mid_date = filtered_df['OrderDate'].min() + (filtered_df['OrderDate'].max() - filtered_df['OrderDate'].min()) / 2
first_half = filtered_df[filtered_df['OrderDate'] < mid_date]
second_half = filtered_df[filtered_df['OrderDate'] >= mid_date]

if len(first_half) > 0 and len(second_half) > 0:
    gmv_growth = (second_half['TotalAmount'].sum() / first_half['TotalAmount'].sum() - 1) * 100
    order_growth = (len(second_half) / len(first_half) - 1) * 100
    aov_growth = ((second_half['TotalAmount'].sum() / len(second_half)) / (first_half['TotalAmount'].sum() / len(first_half)) - 1) * 100
    customer_growth = (second_half['CustomerID'].nunique() / first_half['CustomerID'].nunique() - 1) * 100
else:
    gmv_growth = order_growth = aov_growth = customer_growth = 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💰 总 GMV", f"${total_gmv:,.0f}", f"{gmv_growth:+.1f}%", delta_color="normal")
with col2:
    st.metric("📦 总订单数", f"{total_orders:,}", f"{order_growth:+.1f}%", delta_color="normal")
with col3:
    st.metric("👥 活跃客户数", f"{total_customers:,}", f"{customer_growth:+.1f}%", delta_color="normal")
with col4:
    st.metric("💵 客单价 (AOV)", f"${aov:,.2f}", f"{aov_growth:+.1f}%", delta_color="normal")

col5, col6, col7, col8 = st.columns(4)
with col5:
    st.metric("✅ 订单完成率", f"{delivered_rate:.1f}%")
with col6:
    st.metric("🏷️ 平均折扣率", f"{avg_discount:.1f}%")
with col7:
    st.metric("🛍️ 商品SKU数", f"{filtered_df['ProductName'].nunique()}")
with col8:
    st.metric("🏪 活跃卖家数", f"{filtered_df['SellerID'].nunique()}")


# ============================================================
# 模块二：销售趋势
# ============================================================
st.markdown("<div class='section-title'>📈 销售趋势分析</div>", unsafe_allow_html=True)

trend_col1, trend_col2 = st.columns([3, 2])

with trend_col1:
    # 月度销售趋势
    monthly = filtered_df.groupby('YearMonth').agg(
        GMV=('TotalAmount', 'sum'),
        Orders=('OrderID', 'count'),
        Customers=('CustomerID', 'nunique')
    ).reset_index()
    monthly = monthly.sort_values('YearMonth')

    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    fig_trend.add_trace(
        go.Bar(x=monthly['YearMonth'], y=monthly['GMV'],
               name='GMV ($)', marker_color='#2b6cb0', opacity=0.8),
        secondary_y=False
    )
    fig_trend.add_trace(
        go.Scatter(x=monthly['YearMonth'], y=monthly['Orders'],
                   name='订单数', mode='lines+markers',
                   line=dict(color='#e53e3e', width=2),
                   marker=dict(size=5)),
        secondary_y=True
    )
    fig_trend.update_layout(
        title="月度 GMV 与订单量趋势",
        height=420,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=60, b=10)
    )
    fig_trend.update_yaxes(title_text="GMV ($)", secondary_y=False, gridcolor='#f0f0f0')
    fig_trend.update_yaxes(title_text="订单数", secondary_y=True, gridcolor='#f0f0f0')
    fig_trend.update_xaxes(tickangle=45, tickfont=dict(size=9))
    st.plotly_chart(fig_trend, use_container_width=True)

with trend_col2:
    # 星期分布
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_data = filtered_df.groupby('DayOfWeek').agg(
        GMV=('TotalAmount', 'sum'),
        Orders=('OrderID', 'count')
    ).reindex(dow_order).reset_index()

    fig_dow = px.bar(dow_data, x='DayOfWeek', y='Orders',
                     color='GMV',
                     color_continuous_scale='Blues',
                     title="按星期分布订单量",
                     labels={'DayOfWeek': '星期', 'Orders': '订单数'})
    fig_dow.update_layout(height=420, margin=dict(l=10, r=10, t=60, b=10))
    fig_dow.update_xaxes(tickangle=30)
    st.plotly_chart(fig_dow, use_container_width=True)

# 季度热力图
st.subheader("📅 季度销售热力图")
# 提取季度数字（1-4）用于透视
heatmap_df = filtered_df.copy()
heatmap_df['Qtr'] = heatmap_df['OrderDate'].dt.quarter
pivot_heatmap = heatmap_df.pivot_table(
    index='Year', columns='Qtr',
    values='TotalAmount', aggfunc='sum'
).fillna(0)
# 确保列顺序为 Q1-Q4
for q in range(1, 5):
    if q not in pivot_heatmap.columns:
        pivot_heatmap[q] = 0
pivot_heatmap = pivot_heatmap[sorted(pivot_heatmap.columns)]

fig_heatmap = px.imshow(
    pivot_heatmap.values,
    labels=dict(x="季度", y="年份", color="GMV ($)"),
    x=[f"Q{i}" for i in pivot_heatmap.columns],
    y=pivot_heatmap.index.tolist(),
    text_auto='.2s',
    color_continuous_scale='Blues',
    aspect="auto"
)
fig_heatmap.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10))
st.plotly_chart(fig_heatmap, use_container_width=True)


# ============================================================
# 模块三：品类与商品分析
# ============================================================
st.markdown("<div class='section-title'>📦 品类与商品分析</div>", unsafe_allow_html=True)

cat_col1, cat_col2 = st.columns(2)

with cat_col1:
    # 品类销售占比
    cat_sales = filtered_df.groupby('Category').agg(
        GMV=('TotalAmount', 'sum'),
        Orders=('OrderID', 'count'),
        AvgPrice=('UnitPrice', 'mean')
    ).reset_index().sort_values('GMV', ascending=False)

    fig_cat = px.pie(cat_sales, values='GMV', names='Category',
                     title='各品类 GMV 占比',
                     hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Blues_r)
    fig_cat.update_traces(textposition='inside', textinfo='percent+label')
    fig_cat.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig_cat, use_container_width=True)

with cat_col2:
    # 品牌销售排行
    brand_sales = filtered_df.groupby('Brand').agg(
        GMV=('TotalAmount', 'sum'),
        Orders=('OrderID', 'count')
    ).reset_index().sort_values('GMV', ascending=True)

    fig_brand = px.bar(brand_sales, x='GMV', y='Brand', orientation='h',
                       title='品牌 GMV 排行',
                       color='GMV', color_continuous_scale='Blues',
                       labels={'GMV': '总销售额 ($)', 'Brand': '品牌'})
    fig_brand.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
    fig_brand.update_traces(texttemplate='%{x:,.0f}', textposition='outside')
    st.plotly_chart(fig_brand, use_container_width=True)

# Top 10 商品
st.subheader("🏆 Top 10 畅销商品")
top_products = filtered_df.groupby('ProductName').agg(
    GMV=('TotalAmount', 'sum'),
    Orders=('OrderID', 'count'),
    Quantity=('Quantity', 'sum'),
    Category=('Category', 'first'),
    Brand=('Brand', 'first')
).reset_index().sort_values('GMV', ascending=False).head(10)

st.dataframe(
    top_products.style.format({
        'GMV': '${:,.0f}',
        'Orders': '{:,}',
        'Quantity': '{:,}'
    }),
    use_container_width=True,
    hide_index=True
)

# 折扣与销量关系
st.subheader("📊 折扣力度与销量关系分析")
discount_col1, discount_col2 = st.columns([2, 1])

with discount_col1:
    filtered_df['DiscountTier'] = pd.cut(filtered_df['Discount'],
                                         bins=[-0.01, 0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.31],
                                         labels=['无折扣', '0-5%', '5-10%', '10-15%', '15-20%', '20-25%', '25-30%'])
    discount_analysis = filtered_df.groupby('DiscountTier').agg(
        AvgQuantity=('Quantity', 'mean'),
        Orders=('OrderID', 'count'),
        AvgTotalAmount=('TotalAmount', 'mean')
    ).reset_index()

    fig_discount = make_subplots(specs=[[{"secondary_y": True}]])
    fig_discount.add_trace(
        go.Bar(x=discount_analysis['DiscountTier'], y=discount_analysis['AvgQuantity'],
               name='平均购买数量', marker_color='#2b6cb0'),
        secondary_y=False
    )
    fig_discount.add_trace(
        go.Scatter(x=discount_analysis['DiscountTier'], y=discount_analysis['AvgTotalAmount'],
                   name='平均订单金额 ($)', mode='lines+markers',
                   line=dict(color='#e53e3e', width=2)),
        secondary_y=True
    )
    fig_discount.update_layout(
        title="折扣力度 vs 购买数量 & 订单金额",
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=60, b=10)
    )
    fig_discount.update_yaxes(title_text="平均购买数量", secondary_y=False)
    fig_discount.update_yaxes(title_text="平均订单金额 ($)", secondary_y=True)
    st.plotly_chart(fig_discount, use_container_width=True)

with discount_col2:
    # 计算相关性
    corr_qty_disc = filtered_df['Quantity'].corr(filtered_df['Discount'])
    corr_amt_disc = filtered_df['TotalAmount'].corr(filtered_df['Discount'])

    st.markdown("### 🔍 分析结论")
    st.info(f"""
    **折扣 vs 数量 相关系数：** {corr_qty_disc:.3f}
    - {'正相关' if corr_qty_disc > 0 else '负相关'}：折扣{'越高' if corr_qty_disc > 0 else '越低'}，购买数量{'越多' if corr_qty_disc > 0 else '越少'}

    **折扣 vs 金额 相关系数：** {corr_amt_disc:.3f}
    - {'正相关' if corr_amt_disc > 0 else '负相关'}：折扣{'越高' if corr_amt_disc > 0 else '越低'}，订单金额{'越高' if corr_amt_disc > 0 else '越低'}
    """)

    st.markdown("### 💡 策略建议")
    if corr_qty_disc > 0.1:
        st.success("折扣对销量有明显拉动作用，建议在促销季适度提高折扣力度以拉动销量。")
    else:
        st.warning("折扣对销量拉动有限，建议谨慎使用高折扣策略，避免利润流失。")


# ============================================================
# 模块四：RFM 客户分层
# ============================================================
st.markdown("<div class='section-title'>👥 客户 RFM 分层模型</div>", unsafe_allow_html=True)

# 计算RFM
snapshot_date = filtered_df['OrderDate'].max() + pd.Timedelta(days=1)

rfm = filtered_df.groupby('CustomerID').agg(
    Recency=('OrderDate', lambda x: (snapshot_date - x.max()).days),
    Frequency=('OrderID', 'count'),
    Monetary=('TotalAmount', 'sum')
).reset_index()

# RFM打分 (1-5分)
rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']

# 客户分层
def segment_customer(row):
    r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
    if r >= 4 and f >= 4 and m >= 4:
        return '重要价值客户'
    elif r >= 4 and f <= 2 and m >= 4:
        return '重要发展客户'
    elif r <= 2 and f >= 4 and m >= 4:
        return '重要挽留客户'
    elif r <= 2 and f <= 2 and m >= 4:
        return '重要价值流失'
    elif r >= 4 and f >= 4 and m <= 2:
        return '一般价值客户'
    elif r >= 4 and f <= 2 and m <= 2:
        return '新客户'
    elif r <= 2 and f >= 4 and m <= 2:
        return '流失忠诚客户'
    else:
        return '一般客户'


rfm['Segment'] = rfm.apply(segment_customer, axis=1)

rfm_col1, rfm_col2, rfm_col3 = st.columns(3)

with rfm_col1:
    # RFM分布图
    segment_counts = rfm['Segment'].value_counts().reset_index()
    segment_counts.columns = ['Segment', 'Count']
    segment_counts = segment_counts.sort_values('Count', ascending=True)

    fig_rfm = px.bar(segment_counts, y='Segment', x='Count', orientation='h',
                     title='客户分层分布',
                     color='Count', color_continuous_scale='Blues',
                     labels={'Count': '客户数', 'Segment': '客户分层'})
    fig_rfm.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
    fig_rfm.update_traces(texttemplate='%{x:,}', textposition='outside')
    st.plotly_chart(fig_rfm, use_container_width=True)

with rfm_col2:
    # RFM得分分布
    score_dist = rfm['RFM_Score'].value_counts().sort_index().reset_index()
    score_dist.columns = ['Score', 'Count']

    fig_score = px.bar(score_dist, x='Score', y='Count',
                       title='RFM 综合得分分布',
                       color='Score', color_continuous_scale='RdYlGn',
                       labels={'Score': 'RFM 总分', 'Count': '客户数'})
    fig_score.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10), showlegend=False)
    st.plotly_chart(fig_score, use_container_width=True)

with rfm_col3:
    # 各分层GMV贡献
    rfm_gmv = rfm.groupby('Segment')['Monetary'].sum().reset_index().sort_values('Monetary', ascending=False)
    total_monetary = rfm_gmv['Monetary'].sum()

    fig_rfm_gmv = px.pie(rfm_gmv, values='Monetary', names='Segment',
                         title='各客户分层 GMV 贡献',
                         hole=0.5,
                         color_discrete_sequence=px.colors.sequential.Viridis)
    fig_rfm_gmv.update_traces(textposition='inside', textinfo='percent')
    fig_rfm_gmv.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig_rfm_gmv, use_container_width=True)

# RFM策略建议
st.subheader("🎯 RFM 策略建议")
strategy_data = [
    {"分层": "重要价值客户", "数量": len(rfm[rfm['Segment'] == '重要价值客户']),
     "策略": "VIP专属服务、个性化推荐、新品优先体验",
     "重点": "保持满意度，提高品牌忠诚度"},
    {"分层": "重要发展客户", "数量": len(rfm[rfm['Segment'] == '重要发展客户']),
     "策略": "会员体系引导、满减优惠提升复购",
     "重点": "提高购买频次，向价值客户转化"},
    {"分层": "重要挽留客户", "数量": len(rfm[rfm['Segment'] == '重要挽留客户']),
     "策略": "专属召回优惠、客服主动联系、满意度调研",
     "重点": "防止流失，唤醒沉睡高价值客户"},
    {"分层": "新客户", "数量": len(rfm[rfm['Segment'] == '新客户']),
     "策略": "首单优惠引导、新人礼包、使用教程",
     "重点": "提高首次购买体验，培养消费习惯"},
]
st.dataframe(
    pd.DataFrame(strategy_data).style.set_properties(**{'text-align': 'left'}),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 模块五：地理分析
# ============================================================
st.markdown("<div class='section-title'>🌍 地理销售分析</div>", unsafe_allow_html=True)

geo_col1, geo_col2 = st.columns(2)

with geo_col1:
    # 国家销售分布
    country_sales = filtered_df.groupby('Country').agg(
        GMV=('TotalAmount', 'sum'),
        Orders=('OrderID', 'count'),
        Customers=('CustomerID', 'nunique'),
        AOV=('TotalAmount', 'mean')
    ).reset_index().sort_values('GMV', ascending=False)

    fig_country = px.bar(country_sales, x='Country', y='GMV',
                         color='AOV',
                         color_continuous_scale='Blues',
                         title='各国 GMV 分布（颜色=客单价）',
                         labels={'Country': '国家', 'GMV': '总销售额 ($)', 'AOV': '客单价 ($)'})
    fig_country.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
    fig_country.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
    st.plotly_chart(fig_country, use_container_width=True)

with geo_col2:
    # 城市销售Top10
    city_sales = filtered_df.groupby('City').agg(
        GMV=('TotalAmount', 'sum'),
        Orders=('OrderID', 'count')
    ).reset_index().sort_values('GMV', ascending=True).tail(10)

    fig_city = px.bar(city_sales, x='GMV', y='City', orientation='h',
                      title='Top 10 城市 GMV',
                      color='GMV', color_continuous_scale='Blues',
                      labels={'GMV': '总销售额 ($)', 'City': '城市'})
    fig_city.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
    fig_city.update_traces(texttemplate='%{x:,.0f}', textposition='outside')
    st.plotly_chart(fig_city, use_container_width=True)

# 州/省份分布
st.subheader("🏙️ 州/省份销售详情")
state_sales = filtered_df.groupby('State').agg(
    GMV=('TotalAmount', 'sum'),
    Orders=('OrderID', 'count'),
    Customers=('CustomerID', 'nunique'),
    AOV=('TotalAmount', 'mean')
).reset_index().sort_values('GMV', ascending=False)

st.dataframe(
    state_sales.style.format({
        'GMV': '${:,.0f}',
        'Orders': '{:,}',
        'Customers': '{:,}',
        'AOV': '${:,.2f}'
    }),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 模块六：支付与订单状态
# ============================================================
st.markdown("<div class='section-title'>💳 支付方式 & 订单状态</div>", unsafe_allow_html=True)

pay_col1, pay_col2 = st.columns(2)

with pay_col1:
    # 支付方式分布
    pay_data = filtered_df.groupby('PaymentMethod').agg(
        GMV=('TotalAmount', 'sum'),
        Orders=('OrderID', 'count')
    ).reset_index().sort_values('GMV', ascending=False)

    fig_pay = px.pie(pay_data, values='Orders', names='PaymentMethod',
                     title='支付方式订单占比',
                     hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Set2)
    fig_pay.update_traces(textposition='inside', textinfo='percent+label')
    fig_pay.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig_pay, use_container_width=True)

with pay_col2:
    # 订单状态分布
    status_data = filtered_df.groupby('OrderStatus').agg(
        GMV=('TotalAmount', 'sum'),
        Orders=('OrderID', 'count')
    ).reset_index().sort_values('Orders', ascending=False)

    fig_status = px.bar(status_data, x='OrderStatus', y='Orders',
                        color='GMV',
                        color_continuous_scale='Reds',
                        title='订单状态分布',
                        labels={'OrderStatus': '订单状态', 'Orders': '订单数', 'GMV': 'GMV ($)'})
    fig_status.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
    fig_status.update_traces(texttemplate='%{y:,}', textposition='outside')
    st.plotly_chart(fig_status, use_container_width=True)

# 取消率分析
st.subheader("⚠️ 订单取消率分析")
cancel_by_cat = filtered_df.groupby(['Category', 'OrderStatus']).size().unstack(fill_value=0)
cancel_by_cat['CancelRate'] = cancel_by_cat.get('Cancelled', 0) / cancel_by_cat.sum(axis=1) * 100
cancel_by_cat = cancel_by_cat.sort_values('CancelRate', ascending=False).reset_index()

fig_cancel = px.bar(cancel_by_cat, x='Category', y='CancelRate',
                    title='各品类订单取消率',
                    color='CancelRate', color_continuous_scale='Reds',
                    labels={'Category': '品类', 'CancelRate': '取消率 (%)'})
fig_cancel.update_layout(height=350, margin=dict(l=10, r=10, t=50, b=10))
fig_cancel.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
st.plotly_chart(fig_cancel, use_container_width=True)


# ============================================================
# 模块七：卖家分析
# ============================================================
st.markdown("<div class='section-title'>🏪 卖家分析</div>", unsafe_allow_html=True)

seller_col1, seller_col2 = st.columns(2)

with seller_col1:
    # Top卖家
    top_sellers = filtered_df.groupby('SellerID').agg(
        GMV=('TotalAmount', 'sum'),
        Orders=('OrderID', 'count'),
        Products=('ProductName', 'nunique'),
        Categories=('Category', 'nunique')
    ).reset_index().sort_values('GMV', ascending=False).head(10)

    fig_seller = px.bar(top_sellers, x='SellerID', y='GMV',
                        title='Top 10 卖家 GMV',
                        color='Orders', color_continuous_scale='Greens',
                        labels={'SellerID': '卖家ID', 'GMV': 'GMV ($)', 'Orders': '订单数'})
    fig_seller.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
    fig_seller.update_xaxes(tickangle=45)
    st.plotly_chart(fig_seller, use_container_width=True)

with seller_col2:
    # 卖家GMV分布（长尾效应）
    seller_gmv = filtered_df.groupby('SellerID')['TotalAmount'].sum().sort_values(ascending=False).reset_index()
    seller_gmv['CumulativePct'] = seller_gmv['TotalAmount'].cumsum() / seller_gmv['TotalAmount'].sum() * 100
    seller_gmv['Rank'] = range(1, len(seller_gmv) + 1)

    fig_pareto = px.line(seller_gmv, x='Rank', y='CumulativePct',
                         title='卖家 GMV 帕累托分布 (累计占比)',
                         labels={'Rank': '卖家排名', 'CumulativePct': '累计 GMV 占比 (%)'})
    fig_pareto.add_hline(y=80, line_dash="dash", line_color="red",
                         annotation_text="80% 线")
    fig_pareto.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
    fig_pareto.update_traces(line_color='#2b6cb0', fill='tozeroy', opacity=0.3)
    st.plotly_chart(fig_pareto, use_container_width=True)


# ============================================================
# 模块八：数据明细
# ============================================================
st.markdown("<div class='section-title'>📋 数据明细查询</div>", unsafe_allow_html=True)

search_term = st.text_input("🔍 搜索订单（订单号/客户名/商品名）", "")
if search_term:
    search_result = filtered_df[
        filtered_df['OrderID'].str.contains(search_term, case=False) |
        filtered_df['CustomerName'].str.contains(search_term, case=False) |
        filtered_df['ProductName'].str.contains(search_term, case=False)
    ].head(100)
    st.dataframe(search_result[[
        'OrderID', 'OrderDate', 'CustomerName', 'ProductName', 'Category',
        'Quantity', 'UnitPrice', 'TotalAmount', 'PaymentMethod', 'OrderStatus', 'Country'
    ]], use_container_width=True, hide_index=True)
    st.caption(f"显示前 100 条结果，共 {len(search_result)} 条匹配")
else:
    st.info("👆 输入关键词搜索订单数据")

# 数据概览
with st.expander("📊 查看数据集整体统计"):
    st.write(f"""
    - **数据总量**：{len(df):,} 条订单记录
    - **时间跨度**：{df['OrderDate'].min().strftime('%Y-%m-%d')} 至 {df['OrderDate'].max().strftime('%Y-%m-%d')}
    - **客户数**：{df['CustomerID'].nunique():,} 人
    - **商品数**：{df['ProductName'].nunique()} 个 SKU
    - **品类数**：{df['Category'].nunique()} 个
    - **品牌数**：{df['Brand'].nunique()} 个
    - **国家数**：{df['Country'].nunique()} 个
    - **城市数**：{df['City'].nunique()} 个
    - **卖家数**：{df['SellerID'].nunique()} 个
    """)

    st.subheader("数值字段统计")
    st.dataframe(df[['Quantity', 'UnitPrice', 'Discount', 'Tax', 'ShippingCost', 'TotalAmount']].describe().T.style.format("{:,.2f}"))


# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #a0aec0; font-size: 13px;'>"
    "📊 Amazon 电商数据分析看板 | 基于 Streamlit + Plotly 构建 | 分析者：Bubble"
    "</p>",
    unsafe_allow_html=True
)
