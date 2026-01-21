# Alpha-One Credit Cockpit（信用驾驶舱）

基于Python和Streamlit构建的固定收益投资组合分析系统，专为量化投资组合管理设计。

## 项目概述

Alpha-One Credit Cockpit 专为管理大型固定收益投资组合（500亿美元以上）的投资组合经理设计。系统通过以下功能实现投资工作流程的数字化：

- **贵/便宜债券识别**：通过分层回归分析，识别相对于板块曲线交易偏贵或偏便宜的债券
- **净息差效率监控**：追踪收益率与资金成本（FTP）的差异，识别"失血"资产
- **估值滞后风险检测**：突出显示存在潜在估值问题的持仓
- **会计分类感知分析**：正确处理HTM与AFS分类

## 系统架构

```
Alpha-One-Credit-Cockpit/
├── app.py                      # Streamlit仪表板（入口点）
├── requirements.txt            # Python依赖
├── data/
│   └── portfolio.csv           # 示例投资组合数据
├── src/
│   ├── __init__.py
│   ├── module_a/               # 发行人360°（未来：AI定性分析）
│   │   ├── __init__.py
│   │   ├── base.py             # LLM集成的抽象基类
│   │   └── issuer_360.py       # 主引擎（占位符）
│   ├── module_b/               # 投资组合优化器（MVP）
│   │   ├── __init__.py
│   │   ├── data_loader.py      # 数据清洗与转换
│   │   └── analytics.py        # 量化分析引擎
│   └── utils/
│       ├── __init__.py
│       └── constants.py        # 配置常量
└── tests/                      # 单元测试
```

### 模块A：发行人360°（未来扩展）

AI驱动的定性分析模块。目前提供：
- 用于未来LLM集成的抽象基类
- 信用分析、文档处理和新闻分析的占位符实现
- 设计用于与OpenAI、Anthropic或其他LLM提供商无缝集成

### 模块B：投资组合优化器（当前MVP）

对当前持仓的量化扫描，包括：
- 分层回归用于识别贵/便宜债券
- 净息差效率分析
- 板块特定的收益率曲线拟合
- 会计分类处理（HTM/AFS）

## 安装说明

```bash
# 克隆仓库
git clone <repository-url>
cd Alpha-One-Credit-Cockpit

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows系统: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 运行仪表板

```bash
streamlit run app.py
```

仪表板将在浏览器中打开，地址为 `http://localhost:8501`。

### 使用数据加载器

```python
from src.module_b.data_loader import DataLoader

# 加载并清洗投资组合数据
loader = DataLoader()
df = loader.load("path/to/portfolio.csv")

# 检查数据质量
report = loader.get_quality_report()
print(report.to_dict())
```

### 使用分析引擎

```python
from src.module_b.analytics import PortfolioAnalyzer

# 使用清洗后的数据初始化
analyzer = PortfolioAnalyzer(df)

# 拟合板块曲线
regression_results = analyzer.fit_sector_curves()

# 获取卖出候选（贵的债券）
sell_candidates = analyzer.get_sell_candidates(z_threshold=-1.5)

# 获取失血资产（负息差）
bleeding = analyzer.get_bleeding_assets()

# 生成高管摘要
summary = analyzer.generate_executive_summary()
```

## 数据格式

系统接受包含双语（中英文）列名的CSV文件：

| 源列名 | 目标列名 | 描述 |
|--------|----------|------|
| 分类1 | Sector_L1 | 一级板块（MBS、公司债、金融债等） |
| 分类2 | Sector_L2 | 二级板块（国企、外资银行等） |
| TICKER | Ticker | 债券代码 |
| 债券名称 | Name | 债券名称 |
| AccSection | Accounting | 会计分类（HTM、AFS、公允价值） |
| Nominal（USD） | Nominal_USD | 持仓规模（美元） |
| Duration | Duration | 修正久期 |
| EffectiveYield | Yield | 有效收益率（转换为小数） |
| OAS | OAS | 期权调整利差 |
| FTP Rate | FTP | 资金转移定价 |

### 派生列（自动生成）

| 列名 | 公式 | 描述 |
|------|------|------|
| Liquidity_Proxy | 如果 Nominal > 1000万美元: 5，否则: 3 | 流动性评分 |
| Net_Carry | Yield - FTP | 扣除资金成本后的息差 |
| Carry_Efficiency | Net_Carry / Duration | 单位久期息差 |
| Is_Tradeable | Accounting != 'HTM' | 是否可交易 |

## 量化方法论

### 分层回归

对于每个板块，系统拟合二次收益率-久期曲线：

$$收益率 = a \cdot 久期^2 + b \cdot 久期 + c$$

**关键指标：**
- **残差**：实际收益率 - 模型收益率
- **Z分数**：残差 / 残差标准差

**解释：**
- Z分数 < -1.5：**贵**（昂贵，卖出候选）
- Z分数 > +1.5：**便宜**（有吸引力，买入候选）
- -0.5 < Z分数 < +0.5：**公允价值**

### 会计约束

- **HTM（持有至到期）**：由于监管要求不能出售。从优化建议中排除。
- **AFS（可供出售）**：可以自由交易。
- **公允价值**：按市值计价，可交易。

## 仪表板功能

### 标签页1：矩阵视图
- 久期与收益率的交互式散点图
- 板块特定回归曲线叠加
- 悬停显示债券详细信息

### 标签页2：优化实验室
- 卖出候选表格（Z分数 < -1.5）
- 失血资产表格（净息差 < 0）
- 息差效率分布

### 标签页3：管理简报
- 一键生成高管摘要
- 投资组合指标概览
- 板块配置可视化
- 数据导出功能

## 未来开发

### 模块A集成
`src/module_a/base.py` 中的抽象基类设计用于：
- **BaseCreditProfiler**：LLM驱动的信用档案生成
- **BaseDocumentProcessor**：SEC文件和契约文档分析
- **BaseNewsAnalyzer**：新闻情绪和重大事件检测

集成LLM提供商的方法：

```python
from src.module_a.base import BaseCreditProfiler
from src.module_a.issuer_360 import Issuer360Engine

# 实现您的自定义分析器
class OpenAICreditProfiler(BaseCreditProfiler):
    def generate_profile(self, issuer_id, ...):
        # 您的LLM实现
        pass

# 注册到引擎
engine = Issuer360Engine()
engine.register_credit_profiler(OpenAICreditProfiler())
```

## 贡献指南

1. Fork本仓库
2. 创建功能分支
3. 为新功能编写测试
4. 提交Pull Request

## 许可证

MIT许可证

## 联系方式

如有问题或需要支持，请在仓库中提交Issue。

---

## 术语对照表

| 英文术语 | 中文翻译 | 说明 |
|----------|----------|------|
| Rich | 贵 | 相对于曲线偏贵的债券 |
| Cheap | 便宜 | 相对于曲线偏便宜的债券 |
| Net Carry | 净息差 | 收益率减去资金成本 |
| Carry Efficiency | 息差效率 | 单位久期产生的净息差 |
| Bleeding Assets | 失血资产 | 净息差为负的资产 |
| Z-Score | Z分数 | 标准化残差 |
| HTM | 持有至到期 | Hold-to-Maturity的缩写 |
| AFS | 可供出售 | Available-for-Sale的缩写 |
| FTP | 资金转移定价 | Funds Transfer Pricing的缩写 |
| OAS | 期权调整利差 | Option-Adjusted Spread的缩写 |
| Duration | 久期 | 债券价格对利率变化的敏感度 |
| Sector | 板块 | 债券分类 |
| Regression | 回归 | 统计建模方法 |
| Residual | 残差 | 实际值与预测值的差异 |
