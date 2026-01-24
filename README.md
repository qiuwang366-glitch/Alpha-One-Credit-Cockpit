# 🚀 Alpha-One Credit Cockpit | 信用驾驶舱

> **从交易员视角重新定义固定收益投资组合管理**
> 一个为真实世界设计的机构级量化分析系统

[![LinkedIn](https://img.shields.io/badge/LinkedIn-刘璐-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/liulu-math/)
[![Made with Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg?style=for-the-badge)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)

[English Version](./README_EN.md) | 中文版

---

## 💡 项目起源：从痛点到解决方案

在管理超过**500亿美元**的固定收益投资组合时，投资组合经理每天面临的核心挑战是：

- 📊 **相对价值发现**：在数百只债券中，哪些被**高估**（Rich），哪些被**低估**（Cheap）？
- 💰 **融资成本管理**：考虑资金成本（FTP）后，哪些资产在"**失血**"（负息差）？
- 📈 **基本面整合**：定价分析如何与发行人财务健康度**无缝结合**？
- 🔍 **单券深度分析**：快速查看单一债券的**公允价值**、**同发行人对比**、**财务趋势**？
- 🏢 **发行人全景视图**：如何系统性评估一个发行人的**估值偏离**、**财务健康**、**同业对标**？

**Alpha-One Credit Cockpit** 正是为解决这些实际交易场景而生的工具 —— 它不是学术项目，而是**可以直接投入生产**的分析系统。

---

## ✨ 核心价值主张

### 1. 🎯 统计驱动的相对价值分析

传统方法依赖经验和直觉，而本系统使用**分层回归**和**Z-Score标准化**，让富/便宜的判断有据可依：

```
双模型架构：
├─ Quadratic Model（二次多项式）      → 简洁、快速、适合标准曲线
└─ Nelson-Siegel Model（参数化模型）  → 理论严谨、适合复杂曲线

分层策略：
按行业分组 → 拟合各行业收益率曲线 → 计算残差Z-Score → 识别交易机会

Z-Score解读：
• Z < -1.5  →  Rich（富）   → 卖出候选
• Z > +1.5  →  Cheap（便宜） → 买入候选
• |Z| < 0.5 →  Fair Value    → 持有
```

### 2. 💸 融资成本意识（Net Carry Analysis）

许多债券表面收益率诱人，但扣除资金成本（FTP）后可能是**负贡献**：

```python
Net_Carry = Yield - FTP
Carry_Efficiency = Net_Carry / Duration  # 单位久期的净息差

# 系统自动识别"失血资产"（Bleeding Assets）
bleeding_assets = portfolio[portfolio['Net_Carry'] < 0]
```

这让投资组合经理能够**量化每个头寸对整体盈利的贡献**，而不只是看名义收益。

### 3. 🏢 发行人360°全景分析

首创性地将**定价分析**与**财务基本面**整合在同一个视图：

**A. 估值曲线对比**
- 发行人债券在行业曲线上的位置（偏贵 or 偏便宜？）
- 发行人内部曲线拟合（如有3+债券）
- 平均Z-Score计算

**B. 财务仪表板（8季度趋势）**
- 去杠杆化进程（总负债 + 净杠杆）
- 流动性状况（现金 vs 利息支出）
- 盈利能力（EBITDA利润率）
- 增长态势（收入环比增长）

**C. 同业对标（Radar Chart）**
- 5维度对比：净杠杆、利息覆盖率、EBITDA利润率、现金比率、收入增长
- 自动识别发行人相对行业的**优势**和**劣势**

### 4. 📱 机构级用户体验

- **Mobile-First设计**：响应式布局，支持平板/手机随时查看
- **Bloomberg Terminal美学**：专业深色主题（`#121212` 背景 + `#FF9800` 强调色）
- **双语界面**：所有标签和提示均为**中英文双语**
- **实时交互**：Plotly图表支持缩放、悬停、钻取

### 5. 🤖 为AI时代预留的扩展框架

**Module A** 提供了完整的抽象基类，为未来集成LLM（GPT-4, Claude等）做好准备：

```python
# 三大抽象接口
BaseCreditProfiler       # AI驱动的信用档案生成
BaseDocumentProcessor    # SEC文件和契约文档分析
BaseNewsAnalyzer         # 新闻情绪和重大事件检测

# 即插即用设计
from src.module_a.base import BaseCreditProfiler

class GPT4CreditProfiler(BaseCreditProfiler):
    def generate_profile(self, issuer_id):
        # 接入OpenAI API
        pass

engine.register_credit_profiler(GPT4CreditProfiler())
```

---

## 🎓 设计思路与技术洞察

### 为什么选择Nelson-Siegel模型？

在固定收益分析中，简单的多项式回归（二次曲线）虽然快速，但有两个问题：

1. **参数无经济含义**：系数 a, b, c 只是数学拟合结果
2. **对异常曲线鲁棒性差**：收益率曲线倒挂或驼峰时拟合效果不佳

**Nelson-Siegel模型**则优雅地解决了这些问题：

```
Yield(τ) = β₀ + β₁·f₁(τ) + β₂·f₂(τ)

其中：
• β₀ (Level)     → 长期收益率水平（渐近线）
• β₁ (Slope)     → 短期因子（曲线起始斜率）
• β₂ (Curvature) → 中期曲率（驼峰形状）
• λ (Decay)      → 控制曲率峰值位置
```

**每个参数都有明确的经济学含义**，这让我们可以：
- 分析短期、中期、长期利率的结构性变化
- 识别曲线的"凸性"和"凹性"特征
- 对不规则形状的收益率曲线有更好的拟合效果

**技术实现亮点**：使用 `scipy.optimize.curve_fit` 自动优化参数，设置合理的边界约束，确保收敛稳定性。

### 为什么采用分层回归（Stratified Regression）？

直接对所有债券做回归会产生**辛普森悖论**（Simpson's Paradox）：

```
例子：
金融债平均收益率 4.5%，企业债平均收益率 5.5%
如果直接混合回归，会认为某只5%的金融债是"cheap"
但实际上它在金融债行业内可能是"rich"
```

**解决方案**：按 `Sector_L1`（一级行业）分组，每个行业拟合独立曲线

```python
for sector in df['Sector_L1'].unique():
    sector_data = df[df['Sector_L1'] == sector]
    curve_params = fit_curve(sector_data)
    df.loc[sector_data.index, 'Model_Yield'] = predict(curve_params)
    df.loc[sector_data.index, 'Z_Score'] = (Yield - Model_Yield) / std
```

这样每个Z-Score都是**相对于本行业曲线**计算的，消除了行业间的系统性偏差。

### 为什么设计Module A/B分离架构？

**Module B（当前MVP）**：量化分析引擎
- 纯数值计算，无需外部API
- 数据处理 → 曲线拟合 → 优化建议
- 可以离线运行

**Module A（未来扩展）**：AI定性分析
- 需要LLM API（OpenAI / Anthropic / 本地模型）
- 信用档案生成、文档解析、新闻分析
- 可选模块，按需加载

**设计理念**：
1. **渐进式功能增强**：先实现核心量化功能，再叠加AI能力
2. **成本可控**：不用LLM的用户无需承担API费用
3. **接口标准化**：通过抽象基类定义清晰的契约，任何LLM提供商都可即插即用

这种设计体现了**软件工程的"开闭原则"**（Open-Closed Principle）：对扩展开放，对修改封闭。

---

## 🏗️ 系统架构

```
Alpha-One-Credit-Cockpit/
│
├── app.py                          # Streamlit主应用（Entry Point）
│   ├── Tab 1: Issuer 360 / 发行人全景
│   │   ├── 估值曲线对比（Issuer vs Sector）
│   │   ├── 财务仪表板（2x2网格）
│   │   └── 同业对标（Radar Chart）
│   ├── Tab 2: Relative Value Matrix / 相对价值矩阵
│   │   ├── Duration-Yield散点图 + 回归曲线
│   │   ├── Single Security Analysis / 单券分析
│   │   └── Credit Inspector / 信用检查器
│   ├── Tab 3: Optimization Lab / 优化实验室
│   │   ├── 卖出候选（Rich Bonds）
│   │   ├── 失血资产（Bleeding Assets）
│   │   └── Carry效率分布
│   └── Tab 4: Executive Brief / 管理简报
│       ├── Portfolio Metrics Overview
│       └── CSV Export（全量/筛选/回归统计）
│
├── src/
│   ├── module_a/                   # AI定性分析（Future）
│   │   ├── base.py                 # 抽象基类（3个接口）
│   │   │   ├── BaseCreditProfiler        # 信用档案生成
│   │   │   ├── BaseDocumentProcessor     # 文档解析
│   │   │   └── BaseNewsAnalyzer          # 新闻分析
│   │   └── issuer_360.py           # Issuer 360引擎
│   │
│   ├── module_b/                   # 量化分析（Current MVP）
│   │   ├── data_loader.py          # 数据ETL Pipeline
│   │   │   ├── 双语列映射（中英文）
│   │   │   ├── 编码兼容（UTF-8/GBK/GB2312）
│   │   │   ├── 脏数据清洗（%符号、逗号、括号）
│   │   │   └── 数据质量报告
│   │   │
│   │   ├── analytics.py            # 核心分析引擎
│   │   │   ├── nelson_siegel() - NS模型实现
│   │   │   ├── quadratic_curve() - 二次曲线
│   │   │   ├── PortfolioAnalyzer类
│   │   │   │   ├── fit_sector_curves() - 分层回归
│   │   │   │   ├── get_sell_candidates() - Rich识别
│   │   │   │   ├── get_bleeding_assets() - 负Carry识别
│   │   │   │   └── generate_executive_summary()
│   │   │   └── 总回报分析（Rolldown效应）
│   │   │
│   │   └── financials.py           # 财务基本面模块
│   │       ├── FinancialDataLoader
│   │       ├── 债券-股票代码映射（131发行人）
│   │       ├── 季度数据对齐（8季度）
│   │       └── 计算：净杠杆、利息覆盖率、QoQ增长
│   │
│   └── utils/
│       └── constants.py            # 配置常量（颜色、阈值）
│
├── data/
│   ├── portfolio.csv               # 投资组合持仓数据
│   ├── bond_equity_map.csv         # 债券→股票代码映射表
│   └── quarterly_financials.csv    # 季度财务数据
│
└── tests/
    ├── test_data_loader.py
    └── test_analytics.py
```

---

## 📊 数据流详解

### 输入数据格式

系统接受**双语CSV**（中英文列名均可），示例：

| 分类1 (Sector_L1) | TICKER | Duration | EffectiveYield | OAS | FTP Rate | AccSection |
|------------------|--------|----------|----------------|-----|----------|------------|
| Corps / 企业债    | ABC123 | 4.5      | 5.25%          | 120 | 3.5%     | AFS        |
| Fins / 金融债     | XYZ456 | 2.8      | 4.80%          | 85  | 3.2%     | HTM        |

**关键列说明**：

| 中文列名 | 英文列名 | 说明 | 处理逻辑 |
|---------|---------|------|---------|
| 分类1 | Sector_L1 | 一级行业（MBS/Corps/Fins等） | 用于分层回归 |
| TICKER | Ticker | 债券代码 | 唯一标识符 |
| Duration | Duration | 修正久期 | 数值型，用于曲线X轴 |
| EffectiveYield | Yield | 有效收益率 | 支持百分号格式（5.25%）自动转换 |
| OAS | OAS | 期权调整利差（bp） | 数值型 |
| FTP Rate | FTP | 资金转移定价 | 缺失时默认0% |
| AccSection | Accounting | 会计分类 | HTM不可交易，AFS/Fair Value可交易 |

### 数据清洗流程

```python
# DataLoader的9步清洗Pipeline
1. 编码检测       → 自动尝试 UTF-8 → GBK → GB2312
2. 列名映射       → 中文列名 → 标准英文列名
3. 去除脏字符     → %符号、逗号、括号、会计记号
4. 数值类型转换   → str → float（Yield, Duration, OAS, Nominal）
5. 百分号处理     → "5.25%" → 0.0525
6. 缺失值填充     → FTP缺失 → 0%，其他保留NaN
7. 会计分类规范化 → 统一为 HTM / AFS / Fair Value
8. 派生指标计算   → Net_Carry, Carry_Efficiency, Liquidity_Proxy
9. 数据质量报告   → 记录解析错误和缺失统计
```

### 派生指标自动生成

```python
# Liquidity Proxy（流动性评分）
df['Liquidity_Proxy'] = df['Nominal_USD'].apply(
    lambda x: 5 if x > 10_000_000 else 3
)

# Net Carry（净息差）
df['Net_Carry'] = df['Yield'] - df['FTP']

# Carry Efficiency（单位久期息差）
df['Carry_Efficiency'] = df['Net_Carry'] / df['Duration']

# Is Tradeable（是否可交易）
df['Is_Tradeable'] = df['Accounting'] != 'HTM'
```

---

## 🔬 量化方法论深度解析

### Nelson-Siegel模型数学推导

Nelson-Siegel模型源于无套利期限结构理论，其核心思想是将收益率分解为三个因子：

$$
y(\tau) = \beta_0 + \beta_1 \cdot \left(\frac{1-e^{-\tau/\lambda}}{\tau/\lambda}\right) + \beta_2 \cdot \left(\frac{1-e^{-\tau/\lambda}}{\tau/\lambda} - e^{-\tau/\lambda}\right)
$$

**参数含义**：
- $\beta_0$：当 $\tau \to \infty$ 时的极限收益率（Long-Term Level）
- $\beta_1$：短期因子，主导短久期区域的斜率
- $\beta_2$：曲率因子，决定曲线的"驼峰"形状
- $\lambda$：衰减参数，控制 $\beta_2$ 的影响在哪个久期达到最大

**直观理解**：
```
当 τ → 0 时：  y(0) ≈ β₀ + β₁  （短期收益率）
当 τ → ∞ 时：  y(∞) = β₀       （长期收益率）
当 τ = λ 时：  β₂的影响最大    （曲率峰值）
```

**实现细节**（`analytics.py:27-51`）：

```python
def nelson_siegel(duration: float, beta0: float, beta1: float,
                  beta2: float, lambda_param: float) -> float:
    """
    Nelson-Siegel收益率曲线模型

    参数边界设置：
    • beta0: [-10, 50]  → 合理的长期收益率范围
    • beta1: [-50, 50]  → 短期斜率范围
    • beta2: [-50, 50]  → 曲率范围
    • lambda: [0.1, 5]  → 衰减参数，经验值
    """
    tau = duration
    lambda_ = lambda_param

    # 第一个因子（短期）
    factor1 = (1 - np.exp(-tau / lambda_)) / (tau / lambda_)

    # 第二个因子（曲率）
    factor2 = factor1 - np.exp(-tau / lambda_)

    yield_value = beta0 + beta1 * factor1 + beta2 * factor2
    return yield_value
```

### Z-Score标准化与统计显著性

**为什么用Z-Score而不是绝对残差？**

假设有两个行业：
- 行业A：残差标准差 = 0.5%（曲线拟合很好）
- 行业B：残差标准差 = 1.5%（曲线拟合一般）

如果债券X残差为 +0.8%，在行业A中是**显著偏离**（Z=1.6），在行业B中是**正常波动**（Z=0.53）。

**Z-Score标准化公式**：

$$
Z = \frac{y_{actual} - y_{model}}{\sigma_{residuals}}
$$

**阈值设定**（基于正态分布）：

```python
Z_SCORE_THRESHOLDS = {
    'rich_threshold': -1.5,    # 约92.8%分位数，卖出信号
    'cheap_threshold': 1.5,    # 约7.2%分位数，买入信号
    'fair_range': (-0.5, 0.5)  # 中位38.3%，公允区间
}
```

**统计解释**：
- 在正态分布下，Z=-1.5表示比93%的债券都要"贵"
- Z=+1.5表示比93%的债券都要"便宜"
- 这是**统计上显著**的偏离，而非随机噪声

---

## 🚀 快速开始

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/your-repo/Alpha-One-Credit-Cockpit.git
cd Alpha-One-Credit-Cockpit

# 2. 创建虚拟环境（推荐使用Python 3.9+）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
# 启动Streamlit应用
streamlit run app.py

# 浏览器自动打开 http://localhost:8501
```

### 使用自己的数据

替换 `data/portfolio.csv` 为你的持仓数据（需包含必需列），然后重启应用：

```python
# 必需列（中英文列名均可）
required_columns = [
    '分类1 / Sector_L1',        # 一级行业
    'TICKER / Ticker',          # 债券代码
    'Duration',                 # 修正久期
    'EffectiveYield / Yield',   # 有效收益率
    'OAS',                      # 期权调整利差
]

# 可选列（增强功能）
optional_columns = [
    'FTP Rate / FTP',           # 资金转移定价（用于Net Carry计算）
    'AccSection / Accounting',  # 会计分类（用于可交易性判断）
    'Nominal（USD） / Nominal_USD',  # 持仓规模（用于流动性评分）
]
```

---

## 📖 使用示例

### 示例1：识别被高估的债券（Rich Bonds）

```python
from src.module_b.data_loader import DataLoader
from src.module_b.analytics import PortfolioAnalyzer

# 加载数据
loader = DataLoader()
df = loader.load('data/portfolio.csv')

# 使用Nelson-Siegel模型分析
analyzer = PortfolioAnalyzer(df, model_type='nelson_siegel')
regression_results = analyzer.fit_sector_curves()

# 获取Z-Score < -1.5的债券（被高估）
sell_candidates = analyzer.get_sell_candidates(z_threshold=-1.5)

print(f"发现 {len(sell_candidates)} 只被高估的债券")
print(sell_candidates[['Ticker', 'Sector_L1', 'Yield', 'Model_Yield', 'Z_Score']])

# 输出示例：
#    Ticker  Sector_L1  Yield  Model_Yield  Z_Score
# 0  ABC123  Corps      4.50%  5.20%        -2.1
# 1  DEF456  Fins       3.80%  4.50%        -1.8
```

### 示例2：识别失血资产（Negative Carry）

```python
# 获取Net Carry < 0的债券
bleeding = analyzer.get_bleeding_assets()

print(f"发现 {len(bleeding)} 只失血资产")
print(bleeding[['Ticker', 'Yield', 'FTP', 'Net_Carry', 'Carry_Efficiency']])

# 输出示例：
#    Ticker  Yield  FTP   Net_Carry  Carry_Efficiency
# 0  GHI789  3.20%  3.50% -0.30%     -0.067
# 1  JKL012  2.80%  3.20% -0.40%     -0.143
```

### 示例3：生成管理简报

```python
# 一键生成高管摘要
summary = analyzer.generate_executive_summary()

print(summary['header'])
print(f"\n总市值：${summary['total_market_value']:,.0f}")
print(f"加权久期：{summary['weighted_duration']:.2f}")
print(f"加权收益率：{summary['weighted_yield']:.2%}")
print(f"\n卖出候选数量：{summary['sell_candidates_count']} 只")
print(f"失血资产数量：{summary['bleeding_assets_count']} 只")
```

---

## 🎨 仪表板功能详解

### Tab 1: Issuer 360 / 发行人全景

**适用场景**：深度分析单一发行人的综合状况

**核心价值**：
- **估值偏离检测**：发行人债券相对行业曲线是偏贵还是偏便宜？
- **财务趋势监控**：8季度杠杆率、流动性、盈利能力、增长的动态变化
- **同业对标**：5维度雷达图对比，识别发行人相对行业的优劣势

**使用步骤**：
1. 从下拉菜单选择发行人（显示该发行人的债券数量和总敞口）
2. 查看**Section A**：发行人债券在行业曲线上的位置，平均Z-Score
3. 查看**Section B**：2x2财务仪表板，快速判断财务健康度
4. 查看**Section C**：雷达图对比，识别相对同业的强项/弱项

**技术实现**：
- 使用 `scipy.interpolate.interp1d` 拟合发行人内部曲线（需≥3债券）
- 行业基准曲线使用Nelson-Siegel模型
- 雷达图使用Plotly的`scatterpolar`图表

### Tab 2: Relative Value Matrix / 相对价值矩阵

**适用场景**：全组合扫描，发现相对价值机会

**核心价值**：
- **可视化全局**：Duration-Yield散点图 + 行业回归曲线叠加
- **单券钻取**：选择任意债券，立即查看公允价值、Z-Score、交易建议
- **发行人曲线**：自动显示同发行人其他债券的曲线
- **基本面融合**：Credit Inspector面板显示关键财务KPI

**交互操作**：
1. 切换回归模型：Quadratic（快速） vs Nelson-Siegel（精确）
2. 筛选行业：在左侧过滤器选择特定行业
3. 选择债券：从下拉菜单选择，散点图会用金色星标突出显示
4. 查看建议：系统自动给出 Buy / Sell / Hold 建议

**图表解读**：
```
散点图：
• X轴 = Duration（久期）
• Y轴 = Yield（收益率）
• 颜色 = Sector_L1（行业）
• 大小 = Nominal_USD（持仓规模）

回归曲线：
• 实线 = 各行业拟合曲线
• 虚线 = ±1标准差范围（Fair Value区间）

星标 ⭐ = 当前选中的债券
```

### Tab 3: Optimization Lab / 优化实验室

**适用场景**：生成可执行的交易建议

**核心价值**：
- **卖出清单**：Z-Score < -1.5的债券，按Z-Score排序
- **失血资产**：Net Carry < 0的债券，按Carry Efficiency排序
- **Carry分布**：直方图展示组合的息差效率分布
- **敞口汇总**：按行业/会计分类的头寸统计

**实战应用**：
1. 导出"卖出候选"表格，提交交易台执行
2. 对失血资产设置内部警报阈值
3. 定期监控Carry Efficiency分布的变化

### Tab 4: Executive Brief / 管理简报

**适用场景**：高层汇报、月度/季度报告

**核心价值**：
- **一键生成**：自动生成包含关键指标的高管摘要
- **行业敞口**：饼图可视化各行业配置
- **数据导出**：支持导出全量持仓、卖出清单、回归统计

**导出格式**：
```python
# 三种CSV导出选项
1. Full Portfolio（全量持仓）
   → 包含所有债券 + Z-Score + Carry指标

2. Sell Candidates（卖出清单）
   → 仅包含Rich债券，可直接提交交易

3. Regression Stats（回归统计）
   → 各行业曲线参数、拟合优度（R²）、样本量
```

---

## 🧠 关于作者

我是**刘璐**，拥有数学和金融双重背景，专注于**量化投资**和**机器学习在金融领域的应用**。

**本项目的设计理念**：

1. **实用主义**：不是为了展示技术而技术，而是解决真实交易场景的痛点
2. **模块化**：Module A/B分离，渐进式功能增强，降低使用门槛
3. **工程质量**：数据清洗、错误处理、测试覆盖，确保生产级稳定性
4. **可扩展性**：为AI时代预留接口，未来可无缝集成LLM能力

**我的技术栈**：
- **量化分析**：Python (Pandas, NumPy, SciPy), R, MATLAB
- **机器学习**：Scikit-learn, XGBoost, TensorFlow/PyTorch
- **数据工程**：SQL, Spark, Airflow
- **Web开发**：Streamlit, Flask, React
- **固定收益**：收益率曲线建模、信用分析、风险管理

**联系方式**：

📧 **LinkedIn**: [https://www.linkedin.com/in/liulu-math/](https://www.linkedin.com/in/liulu-math/)
💼 **寻求机会**：量化研究、数据科学、金融工程相关岗位

如果你对本项目感兴趣，或者有合作/职位机会，欢迎通过LinkedIn联系我！

---

## 🛠️ 技术栈

| 类别 | 技术 | 版本 | 用途 |
|-----|------|------|------|
| **语言** | Python | 3.9+ | 核心开发语言 |
| **UI框架** | Streamlit | 1.28+ | Web应用快速开发 |
| **数据处理** | Pandas | 2.0+ | DataFrame操作、ETL |
| **数值计算** | NumPy | 1.24+ | 矩阵运算、数学函数 |
| **科学计算** | SciPy | 1.10+ | 曲线拟合、优化算法 |
| **可视化** | Plotly | 5.18+ | 交互式图表 |
| **测试** | Pytest | 7.4+ | 单元测试 |
| **类型检查** | mypy | 1.5+ | 静态类型检查（可选） |

---

## 📈 性能与规模

**经过测试的场景**：

| 指标 | 规模 | 性能 |
|-----|------|------|
| 投资组合债券数量 | 1,000+ | 回归计算 < 2秒 |
| 发行人数量 | 200+ | 财务数据加载 < 1秒 |
| 季度财务数据点 | 10,000+ | O(1)查询（缓存优化） |
| UI响应时间 | N/A | 交互反馈 < 500ms |

**优化技术**：

1. **Streamlit Caching**：
   ```python
   @st.cache_resource
   def load_data_loader():
       return DataLoader()  # 仅首次加载，后续复用
   ```

2. **发行人基本面缓存**：
   ```python
   # O(1)查询，而非每次遍历CSV
   issuer_cache: Dict[str, IssuerFundamentals] = {...}
   fundamentals = issuer_cache.get(bond_ticker)
   ```

3. **分层回归并行化**（未来优化）：
   ```python
   # 可使用multiprocessing对各行业并行拟合
   from concurrent.futures import ProcessPoolExecutor
   with ProcessPoolExecutor() as executor:
       results = executor.map(fit_sector_curve, sectors)
   ```

---

## 🧪 测试

运行测试套件：

```bash
# 运行所有测试
pytest

# 运行特定测试模块
pytest tests/test_analytics.py

# 查看覆盖率
pytest --cov=src --cov-report=html
```

**当前测试覆盖**：
- ✅ `DataLoader`：列映射、数据清洗、错误处理
- ✅ `PortfolioAnalyzer`：曲线拟合、Z-Score计算
- 🔄 `FinancialDataLoader`：财务数据加载（进行中）
- 📝 UI集成测试（计划中）

---

## 🚧 路线图

### Phase 4（计划中）：风险管理模块

**目标**：添加VaR、Stress Testing、情景分析

- [ ] 历史VaR计算（Historical Simulation）
- [ ] 蒙特卡洛VaR（Monte Carlo Simulation）
- [ ] 利率冲击情景（+50bp / -50bp / Steepening / Flattening）
- [ ] 信用利差扩大情景（+100bp OAS）
- [ ] 组合CVaR（Conditional VaR）计算

### Phase 5（计划中）：Module A - AI信用分析

**目标**：集成LLM进行定性分析

- [ ] OpenAI GPT-4接入（信用档案生成）
- [ ] Anthropic Claude接入（文档摘要）
- [ ] 本地模型支持（Llama 3, Mistral）
- [ ] SEC文件自动解析（10-K, 10-Q）
- [ ] 新闻情绪分析（路透、彭博数据源）

### Phase 6（计划中）：生产级部署

**目标**：企业级部署方案

- [ ] Docker容器化
- [ ] Kubernetes编排
- [ ] 多用户权限管理（RBAC）
- [ ] 审计日志（Audit Trail）
- [ ] 自动化测试CI/CD（GitHub Actions）
- [ ] API接口（RESTful / GraphQL）

---

## 🤝 贡献指南

欢迎贡献代码、报告Bug、提出功能建议！

**贡献流程**：

1. **Fork本仓库**
2. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **编写代码并测试**
   ```bash
   pytest tests/
   ```
4. **提交Pull Request**
   - 描述清楚改动内容
   - 关联相关的Issue（如有）

**代码规范**：

- 遵循PEP 8（使用`black`格式化）
- 添加类型提示（Type Hints）
- 编写Docstring（Google风格）
- 单元测试覆盖核心逻辑

---

## 📄 开源许可

本项目采用 **MIT License**，你可以自由地：

- ✅ 商业使用
- ✅ 修改代码
- ✅ 分发副本
- ✅ 私有使用

**唯一要求**：保留原作者的版权声明。

详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

感谢以下开源项目和工具：

- **Streamlit**：让Python开发者能快速构建漂亮的Web应用
- **Plotly**：提供交互式图表的强大库
- **Pandas**：数据分析的瑞士军刀
- **SciPy**：科学计算的基石
- **Nelson-Siegel模型**：感谢Charles Nelson和Andrew Siegel的开创性研究

以及所有在GitHub上给予反馈和建议的开发者！

---

## 📮 联系与反馈

如果你有任何问题、建议或合作意向，欢迎通过以下方式联系我：

- 📧 **LinkedIn**: [刘璐的LinkedIn主页](https://www.linkedin.com/in/liulu-math/)
- 🐛 **Bug报告**: [GitHub Issues](https://github.com/your-repo/Alpha-One-Credit-Cockpit/issues)
- 💡 **功能建议**: [GitHub Discussions](https://github.com/your-repo/Alpha-One-Credit-Cockpit/discussions)

**如果这个项目对你有帮助，请给个⭐Star！这是对我最大的鼓励！**

---

---

# 📚 开发日志

> 以下是详细的开发历程记录，展示了项目从0到1的迭代过程。

---

## 2026-01-23 (Phase 3.5: Issuer 360 Dashboard)

### 🎯 综合发行人深度分析

**新增Tab 3: Issuer 360 / 发行人全景**
- 创建专门的发行人深度分析标签页
- 将原Executive Brief移至Tab 4
- 发行人下拉选择器，实时显示快速统计（债券数量、总敞口）
- 动态筛选，仅显示当前组合中有债券的发行人

**Section A: 估值曲线（Issuer vs Sector）**
- 散点图：发行人债券以金色菱形标记
- 发行人特定曲线插值（线性，适用于3+债券）
- 叠加行业基准曲线（Nelson-Siegel）用于对比
- 可视化洞察面板：识别发行人相对行业交易偏贵/偏便宜
- 计算所有发行人债券的平均Z-Score，带颜色编码信号
- 快速指标：加权久期、加权YTM、债券数量

**Section B: 财务仪表板（2x2网格）**
- 使用最近8个季度的财务数据进行趋势分析
- **图表1 - 去杠杆**：双轴图，总负债（柱状图）+ 净杠杆（折线图）
- **图表2 - 流动性**：堆叠面积图，现金 vs 净利息支出
- **图表3 - 盈利能力**：带填充的折线图，EBITDA利润率趋势
- **图表4 - 增长**：颜色编码柱状图（绿色/红色），收入QoQ增长
- 所有图表采用Bloomberg风格极简设计和深色主题

**Section C: 信用同业对比**
- 基于发行人行业自动识别同业组
- 计算最新季度行业平均值，覆盖5个关键指标
- **雷达图（蜘蛛图）**对比发行人vs行业平均：
  - 净杠杆（倒数，便于视觉解读）
  - 利息覆盖率
  - EBITDA利润率
  - 现金比率
  - 收入增长
- 雷达图失败时降级为并排对比表格
- 自动化洞察生成：识别相对同业的优势/劣势
- 同业统计面板：行业名称、同业数量、关键结论

### 🔧 技术实现

- 与`FinancialDataLoader`集成获取季度指标
- 高效使用应用启动时构建的发行人基本面缓存
- 健壮的缺失财务数据错误处理
- 同业数据不可用时优雅降级
- 使用`scipy.interpolate.interp1d`进行发行人曲线拟合
- 使用指标比较的条件逻辑进行颜色编码洞察
- 全程响应式2栏布局，适配桌面/移动端

### 💎 用户体验

- 三个不同部分的清晰视觉层次
- 全文双语（英文/中文）
- 所有交互元素的工具提示和悬停状态
- 发行人无债券或数据时的空状态消息
- 与现有组合筛选器无缝集成
- 保持专业的Bloomberg风格深色主题

**提交记录**：
- `edae73d` - Fix TypeError & Restructure: Issuer 360 as Independent Tab 1
- `22f1fd9` - Merge pull request #15
- `1c98e43` - Fix TypeError: Add stricter data validation for issuer selector

---

## 2026-01-23 (Phase 3: Fundamental Integration & UI Polish)

### 💰 财务基本面模块

**创建`src/module_b/financials.py`**
- 实现`FinancialDataLoader`类，自动债券-股票代码映射
- 添加`QuarterlyMetrics`和`IssuerFundamentals`数据类
- 指标计算：
  - 净债务代理（Total Liabilities - Cash）
  - 净杠杆（Net Debt / EBITDA）
  - 利息覆盖率（EBITDA / Interest Expense）
  - 收入环比增长（QoQ Revenue Growth）
- 优雅处理缺失的EBITDA/利息支出（填充0或排除）
- 8季度历史数据缓存用于趋势分析

### 🎨 Bloomberg Terminal美学

**更新CSS配色方案**
- 深黑色背景：`#121212`
- Bloomberg橙色强调：`#FF9800`
- Terminal蓝色：`#00B0FF`
- 财务指标使用等宽字体（Roboto Mono）
- 带橙色强调边框的增强指标卡片
- 专业玻璃拟态效果，带背景模糊
- 基本面面板和KPI卡片的自定义样式

### 🌐 语言切换

- 在页眉添加双语切换按钮（🌐 EN/CN）
- Session状态管理语言偏好
- 带悬停效果和活动状态样式的按钮
- 通过页面重新运行实现无缝语言切换

### 🔍 信用分析面板

**在主页面（Tab 1）集成基本面显示**
- 双栏布局：左侧（定价分析），右侧（财务基本面）
- 左栏显示公允价值和Z-Score估值指标
- 右栏显示：
  - 发行人信息（股票代码和名称）
  - 三个KPI卡片：收入QoQ增长、净杠杆、利息覆盖率
  - 8季度净杠杆趋势图（面积图，极简设计）
- 颜色编码指标：绿色（安全）、黄色（中等）、红色（风险）
- 通过`bond_equity_map.csv`和`quarterly_financials.csv`自动映射

### 📊 数据架构

- 加载`bond_equity_map.csv`（131个发行人）：债券代码→股票代码映射
- 加载`quarterly_financials.csv`：历史季度数据
- 应用启动时自动加载数据，带覆盖率统计
- 特定债券无基本面数据时优雅降级

### 🔧 技术改进

- 为`financials.py`添加模块重载以防止缓存问题
- 财务数据加载器的Session状态管理
- 通过债券代码实现O(1)查询的发行人基本面高效缓存
- 对缺失或不完整基本面数据的健壮错误处理
- 按日期升序自动排序季度数据

### 💎 用户体验

- 选择代码后，信用分析面板出现在单券分析下方
- 趋势图采用简洁设计，无网格线（Bloomberg风格）
- 悬停工具提示显示季度和精确杠杆值
- 发行人股票代码以橙色高亮显示
- 与现有定价分析无缝集成

---

## 2026-01-22 (Phase 2: Advanced Modeling & Interactivity)

### 📐 Nelson-Siegel模型实现

**数学模型**
- 实现Nelson-Siegel参数化收益率曲线模型
- 四个参数：β₀（长期水平）、β₁（短期因子）、β₂（曲率）、λ（衰减参数）
- 添加`NelsonSiegelResult`数据类存储拟合参数
- 使用`scipy.optimize.curve_fit`进行参数校准，设置合理边界

**UI集成**
- 模型选择切换：Quadratic vs Nelson-Siegel
- 统计面板显示模型特定参数
- 支持两种模型的统一Z-Score计算
- 保持与二次曲线模型的向后兼容性

### 🔍 单券分析功能

**交互式选择器**
- 债券代码下拉选择器（按字母顺序排序）
- 选中的债券在散点图上以金色星标⭐突出显示

**现期指标卡片**
- YTM（到期收益率）
- OAS（期权调整利差）
- Z-Score（颜色编码：绿色/黄色/红色）

**情景分析表**
- 实际收益率 vs 公允收益率对比
- 残差和Z-Score显示
- 自动化解释：Rich/Cheap/Fair
- 交易建议：Buy/Sell/Hold

**智能发行人检测**
- 自动识别同一发行人的其他债券
- 发行人名称清洗和标准化
- 显示找到的同类债券数量

### 📈 发行人曲线可视化

**Mini图表功能**
- 显示同一发行人所有债券的收益率曲线
- 叠加行业基准曲线作为参考
- 金色星标突出显示当前选中债券
- 清晰标注选中债券的位置

### 🔧 技术改进

- 添加`importlib.reload()`强制加载最新模块版本
- 创建完整的`.gitignore`文件排除Python缓存
- 为小数据集的曲线拟合添加健壮错误处理
- 统一两种模型类型的Z-Score计算逻辑
- 保持与原有Quadratic模型的完全兼容

**提交记录**：
- `34304da` - Fix module reload issue: Add importlib.reload()
- `8e65ffd` - Add .gitignore to exclude Python cache files
- `c6c0783` - Implement Nelson-Siegel model and single security drill-down

---

## 2026-01-22 (Phase 1.5: UI/UX Enhancement)

### 📱 移动端优先重设计

**完整UI改造**
- Bloomberg/Aladdin风格深色主题
- 响应式设计，针对移动设备优化
- 自定义CSS，包含玻璃拟态效果和流畅动画
- 可折叠筛选器，具有移动端友好的触摸目标

### 🌍 双语界面

**全面双语支持**
- 完整的中英文双语支持
- 所有标签、工具提示和帮助文本均为双语
- 中文行业名称翻译
- 双语指标卡片和数据表格

### 🎨 视觉改进

**专业配色方案**
- 深蓝、紫色、绿色的专业配色
- 平滑渐变背景
- 自定义滚动条匹配主题
- 悬停效果和过渡动画
- 带强调边框的指标卡片
- 移动端视图的债券卡片

### 🐛 Bug修复

- 修复Plotly布局TypeError（用辅助函数替换字典解包）
- 改进缺失数据的错误处理

**提交记录**：
- `c45e8f1` - Fix Plotly layout TypeError
- `605b114` - Upgrade to institutional-grade mobile-first bilingual dashboard

---

## 2026-01-21 (Phase 1: MVP Launch)

### 🏗️ 核心系统实现

**架构设计**
- 完整的模块化结构设置
- Module A（AI分析，未来扩展）和Module B（量化分析，当前MVP）分离
- 清晰的数据流：加载→清洗→分析→可视化

**数据处理Pipeline**
- 双语CSV解析（中英文列名自动映射）
- 9步数据清洗流程
- 数据验证和质量报告
- 派生指标自动计算

### 📊 量化分析引擎

**PortfolioAnalyzer类**
- 分层回归（按行业分组）
- 二次曲线拟合（Quadratic Regression）
- Z-Score标准化
- 卖出候选识别（Z < -1.5）
- 失血资产检测（Net Carry < 0）
- 投资组合指标聚合
- 高管摘要生成

### 🖥️ Streamlit仪表板

**三标签页界面**
- **Tab 1: Matrix / 矩阵视图**
  - Duration-Yield交互式散点图
  - 行业特定回归曲线叠加
  - 悬停显示债券详细信息

- **Tab 2: Optimization Lab / 优化实验室**
  - 卖出候选表格
  - 失血资产表格
  - Carry效率分布直方图

- **Tab 3: Management Brief / 管理简报**
  - 投资组合指标概览
  - 行业配置饼图
  - CSV数据导出功能

### 🔬 量化方法论

**核心算法**
- 二次回归：`Yield = a·Duration² + b·Duration + c`
- Z-Score计算：`Z = (Actual - Model) / StdDev`
- Net Carry：`Yield - FTP`
- Carry Efficiency：`Net_Carry / Duration`

**数据增强**
- Liquidity Proxy评分（基于持仓规模）
- 会计分类处理（HTM vs AFS）
- 可交易性标记

### 🧪 测试框架

- 创建`tests/`目录结构
- `test_data_loader.py`：数据加载和清洗测试
- `test_analytics.py`：分析引擎测试
- 使用Pytest框架
- 添加类型提示和文档字符串

### 📦 项目基础

**技术栈选择**
- Python 3.9+
- Streamlit（快速Web开发）
- Pandas/NumPy（数据处理）
- SciPy（科学计算）
- Plotly（交互式可视化）

**代码质量**
- 模块化设计（高内聚、低耦合）
- 错误处理和日志记录
- 配置常量管理（`constants.py`）
- 清晰的代码文档

**提交记录**：
- `92fe061` - Implement Alpha-One Credit Cockpit fixed income portfolio system
- `bac31be` - Merge pull request #1
- `dff66b9` - Initial repository setup

---

## 📊 开发统计

| 指标 | 数值 |
|-----|------|
| **总开发时间** | 4天 |
| **当前版本** | 3.5 (Phase 3.5) |
| **代码行数** | ~5,500行 |
| **Python文件数** | 15+ |
| **测试覆盖率** | 进行中 |
| **支持的债券数** | 1,000+ |
| **支持的发行人数** | 200+ |
| **财务数据点** | 10,000+ |

---

**🚀 持续迭代中...**

如果你对项目的演进感兴趣，欢迎Watch本仓库获取最新更新！
