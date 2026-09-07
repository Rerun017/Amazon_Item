# Amazon 数据分析看板

基于 Streamlit + Plotly 构建的交互式电商数据分析看板，展示 10 万+ Amazon 订单数据的多维度分析成果。

## 📊 看板功能

- **核心经营指标**：GMV、订单数、客户数、客单价等 8 项 KPI
- **销售趋势分析**：月度趋势、星期分布、季度热力图
- **品类与商品分析**：品类占比、品牌排行、Top10 商品、折扣与销量关系
- **RFM 客户分层**：基于 RFM 模型的 8 类客户分层及策略建议
- **地理销售分析**：国家分布、城市排行、州/省详情
- **支付与订单状态**：支付方式占比、订单状态分布、取消率分析
- **卖家分析**：Top 卖家排行、帕累托分布
- **数据明细查询**：支持订单号/客户名/商品名搜索

## 🚀 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run app.py
```

## ☁️ 部署到 Streamlit Cloud

### 步骤 1：准备 GitHub 仓库

1. 新建一个 GitHub 仓库
2. 将本目录所有文件上传到仓库：
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `data/Amazon_dataset.csv`

### 步骤 2：部署到 Streamlit Cloud

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 使用 GitHub 账号登录
3. 点击 **"New app"**
4. 选择你的仓库、分支（main）、主文件路径（`app.py`）
5. 点击 **"Deploy!"**
6. 等待 1-3 分钟部署完成

### 步骤 3：获取链接并分享

部署成功后，你会得到一个类似 `https://xxx-amazon-dashboard.streamlit.app` 的链接

## 📁 项目结构

```
amazon_dashboard/
├── app.py                  # 主应用文件
├── requirements.txt        # 依赖包
├── config.toml         # Streamlit 配置
├── data/
│   └── Amazon_dataset.csv  # 数据集
└── README.md               # 说明文档
```
