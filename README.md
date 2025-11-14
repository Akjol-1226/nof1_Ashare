# nof1.AShare - A股AI模拟交易系统

> 基于AKShare的A股AI模拟交易竞赛平台，让不同的AI模型进行实时交易对决

## 项目简介

nof1.AShare是一个A股市场的AI模拟交易系统，参考了nof1.ai项目的设计理念。系统支持多个LLM进行实时交易决策，严格遵守A股交易规则（T+1、涨跌停、最小交易单位等），通过AKShare获取真实市场数据。

### 核心特性

- ✅ 真实市场数据（AKShare）
- ✅ A股交易规则（T+1、涨跌停、手续费）
- ✅ 多LLM支持（OpenAI、Claude、DeepSeek）
- ✅ 实时交易撮合
- ✅ WebSocket实时推送
- ✅ 三栏可视化界面
- ✅ 6只精选可交易股票（中兴通讯、宁德时代、三安光电、比亚迪、寒武纪、恒瑞医药）

## 技术栈

### 后端
- Python 3.9+
- FastAPI（Web框架）
- SQLAlchemy（ORM）
- AKShare（数据源）
- APScheduler（任务调度）

### 前端
- React 18 + TypeScript
- Tailwind CSS
- Recharts（图表）
- WebSocket

## 快速开始

### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制`env.example`到`.env`并填写配置：

```bash
cp env.example .env
```

编辑`.env`文件，添加你的LLM API密钥：

```ini
# OpenAI配置
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1

# Claude配置
CLAUDE_API_KEY=sk-ant-...

# DeepSeek配置
DEEPSEEK_API_KEY=sk-...
```

### 3. 初始化数据库

```bash
cd backend
python -c "from database import init_db; init_db()"
```

### 4. 启动后端服务

```bash
cd backend
python main.py
```

服务将在 http://localhost:8888 启动

### 5. 访问API文档

浏览器访问：http://localhost:8888/docs

## API接口

### AI管理
- `POST /api/ai/register` - 注册AI
- `GET /api/ai/list` - 获取AI列表
- `GET /api/ai/{ai_id}/portfolio` - 获取持仓
- `GET /api/ai/{ai_id}/orders` - 获取订单历史
- `GET /api/ai/{ai_id}/decisions` - 获取决策日志
- `GET /api/ai/ranking` - 获取排行榜

### 市场数据
- `GET /api/market/quotes` - 获取实时行情
- `GET /api/market/stocks` - 获取股票列表

### 系统控制
- `POST /api/system/start` - 启动交易
- `POST /api/system/stop` - 停止交易
- `GET /api/system/status` - 系统状态

### WebSocket
- `ws://localhost:8000/ws/market` - 市场数据推送
- `ws://localhost:8000/ws/trading` - 交易数据推送

## 使用示例

### 注册AI

```bash
curl -X POST "http://localhost:8000/api/ai/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GPT-4 Trader",
    "model_name": "gpt-4",
    "api_key": "sk-...",
    "base_url": "https://api.openai.com/v1",
    "initial_cash": 100000.0
  }'
```

### 启动交易系统

```bash
curl -X POST "http://localhost:8000/api/system/start"
```

### 查看排行榜

```bash
curl "http://localhost:8000/api/ai/ranking"
```

## 项目结构

```
nof1.Ashare/
├── backend/
│   ├── main.py                 # FastAPI入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   ├── data_service/           # AKShare封装
│   │   └── akshare_client.py
│   ├── rules/                  # A股规则引擎
│   │   └── trading_rules.py
│   ├── trading_engine/         # 交易引擎
│   │   ├── order_manager.py
│   │   └── matching_engine.py
│   ├── portfolio/              # 持仓管理
│   │   └── portfolio_manager.py
│   ├── ai_service/             # AI调度
│   │   ├── ai_scheduler.py
│   │   └── llm_adapters/
│   ├── models/                 # 数据库模型
│   │   └── models.py
│   └── api/                    # API路由
│       └── routes.py
├── frontend/                   # 前端项目（待实现）
├── requirements.txt            # Python依赖
├── env.example                 # 环境变量示例
└── README.md                   # 项目文档
```

## 交易规则

### A股规则
- **T+1**: 当日买入的股票次日才能卖出
- **涨跌停**: 普通股票±10%，ST股票±5%
- **最小交易单位**: 100股（1手）
- **手续费**:
  - 佣金: 万2.5（最低5元）
  - 印花税: 0.1%（仅卖出）
  - 过户费: 万0.1

### 交易时间
- 周一至周五
- 上午: 9:30-11:30
- 下午: 13:00-15:00

## 撮合方案

### 方案A（当前实现 - MVP）
- 市价单: 立即按当前价成交
- 限价单: 价格匹配时成交
- 简单快速，适合原型验证

### 方案C（已预留接口）
- 考虑滑点: 根据成交量计算价格偏差
- 成交量限制: 单笔订单不超过市场总量的一定比例
- 更接近真实交易

## 开发计划

- [x] AKShare接口验证
- [x] 后端核心系统
- [x] 数据库模型
- [x] 交易引擎
- [x] AI调度器
- [x] REST API
- [ ] WebSocket推送
- [ ] 前端界面
- [ ] Docker部署
- [ ] 性能优化

## 注意事项

1. AKShare数据有延迟（约3-5秒），不是逐笔行情
2. 非交易时间段系统会跳过决策周期
3. LLM API调用有超时限制（默认5秒）
4. 建议使用代理服务加速LLM API访问
5. 生产环境应该使用PostgreSQL替代SQLite

## 许可证

MIT License

## 致谢

- [AKShare](https://github.com/akfamily/akshare) - 提供A股数据
- [nof1.ai](https://nof1.ai) - 项目灵感来源
