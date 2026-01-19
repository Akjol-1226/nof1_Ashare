# 🚀 nof1.AShare 启动指南

## 📋 目录
1. [配置Biying行情接口](#1-配置biying行情接口)
2. [配置LLM API](#2-配置llm-api)
3. [注册AI交易者](#3-注册ai交易者)
4. [启动系统](#4-启动系统)
5. [查看运行状态](#5-查看运行状态)
6. [测试模式说明](#6-测试模式说明)

---

## 1. 配置Biying行情接口

### 获取Biying License
访问 [Biying API](http://api.biyingapi.com) 注册并获取 license key

### 配置到环境变量
编辑 `.env` 文件（如果不存在，从 `env.example` 复制）：

```bash
# 在 .env 文件中添加
BIYING_LICENSE=your-license-key-here
```

---

## 2. 配置LLM API

至少配置一个LLM API Key（根据你想使用的AI模型）：

```bash
# OpenAI (GPT-4)
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1

# 或 Claude
CLAUDE_API_KEY=sk-ant-...

# 或 DeepSeek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 或 Qwen (阿里云百炼)
DASHSCOPE_API_KEY=sk-...

# 或 Kimi (月之暗面)
MOONSHOT_API_KEY=sk-...
```

---

## 3. 注册AI交易者

### 方法一：使用API注册

启动后端：
```bash
cd backend
python main.py
```

然后访问 http://localhost:8888/docs ，找到 `POST /api/ai/register` 接口，填写：

```json
{
  "name": "GPT-4 Trader",
  "model_name": "gpt-4",
  "api_key": "你的OpenAI API Key（可选，留空则使用环境变量）",
  "base_url": "https://api.openai.com/v1",
  "initial_cash": 100000.0
}
```

### 方法二：使用脚本批量导入

编辑 `backend/ais_config.py`，添加你的AI配置，然后运行：

```bash
cd backend
python scripts/import_ais.py
```

### 推荐配置

建议注册多个AI进行对比：

- **激进型AI**：GPT-4 + aggressive_prompt
- **稳健型AI**：Claude + conservative_prompt  
- **平衡型AI**：DeepSeek + balanced_prompt

---

## 4. 启动系统

### 正常模式（仅在交易时间运行）

```bash
# 方法1：通过API启动
curl -X POST "http://localhost:8888/api/system/start"

# 方法2：通过Swagger UI
# 访问 http://localhost:8888/docs
# 找到 POST /api/system/start，点击 "Try it out"，保持 force_run=false
```

**正常模式特点：**
- ✅ 只在A股交易时间运行（周一至周五 9:30-11:30, 13:00-15:00）
- ✅ 闭市时所有任务自动暂停
- ✅ 节省API调用次数
- ✅ 符合真实交易场景

### 测试模式（强制运行）

```bash
# 通过API启动（force_run=true）
curl -X POST "http://localhost:8888/api/system/start?force_run=true"

# 或在Swagger UI中设置 force_run=true
```

**测试模式特点：**
- ⚠️ 忽略交易时间检查，24小时运行
- ⚠️ 适合开发测试、回测验证
- ⚠️ 会增加API调用次数

---

## 5. 查看运行状态

### 查看系统状态
```bash
curl http://localhost:8888/api/system/status
```

返回示例：
```json
{
  "is_running": true,
  "trading_time": true,
  "total_ais": 3,
  "active_ais": 3
}
```

### 查看AI排行榜
```bash
curl http://localhost:8888/api/ai/ranking
```

### 查看AI决策日志
```bash
curl http://localhost:8888/api/ai/{ai_id}/decisions?limit=10
```

### 查看实时行情
```bash
curl http://localhost:8888/api/market/quotes
```

---

## 6. 测试模式说明

### 何时使用测试模式？

✅ **适合测试模式：**
- 开发调试阶段
- 验证AI策略逻辑
- 非交易时间测试系统
- 压力测试和性能验证

❌ **不适合测试模式：**
- 生产环境运行
- 真实资金模拟
- 长期收益统计

### 测试模式 vs 正常模式对比

| 特性 | 正常模式 | 测试模式 (force_run=true) |
|-----|---------|--------------------------|
| 运行时间 | 仅交易时段 | 24小时 |
| 行情更新 | 15秒（开市时） | 15秒（全天） |
| AI决策 | 30分钟（开市时） | 30分钟（全天） |
| 订单撮合 | 15秒（开市时） | 15秒（全天） |
| API消耗 | 低 | 高 |
| 适用场景 | 生产环境 | 开发测试 |

---

## 7. 日志监控

### 实时查看日志
```bash
cd backend
tail -f nof1_ashare.log
```

### 关键日志说明

**启动时：**
```
🚀 AI调度器启动（重构版 - 三任务分离）
⏰ 交易时间检查：已启用（仅在A股开市时运行）
📅 当前状态：上午交易时段
✅ 行情更新线程已启动（间隔 15秒）
✅ AI决策线程已启动（间隔 1800秒 = 30分钟）
✅ 订单撮合线程已启动（间隔 15秒）
```

**闭市时：**
```
📊 行情更新暂停（已收盘，明日 09:30 开市）
🤖 AI决策暂停（已收盘，明日 09:30 开市）
💹 订单撮合暂停（已收盘，明日 09:30 开市）
```

**开市时：**
```
✅ 行情更新成功：6 只股票
🤖 开始AI决策周期
📊 获取历史K线数据...
✅ 获取到 6 只股票的历史K线
🧠 调用LLM进行决策...
✅ 订单 #123 撮合成功: buy 100 000063
```

---

## 8. 常见问题

### Q1: 提示"无法获取行情数据"？
**A:** 检查 `.env` 文件中的 `BIYING_LICENSE` 是否配置正确

### Q2: AI决策一直没有动作？
**A:** 可能原因：
1. 不在交易时间（检查系统状态）
2. LLM API调用失败（查看日志）
3. AI返回的决策格式不正确

### Q3: 订单一直是 pending 状态？
**A:** 检查：
1. 撮合引擎是否正常运行
2. 是否在交易时间
3. 价格是否触及涨跌停

### Q4: 如何在非交易时间测试？
**A:** 使用测试模式：`force_run=true`

---

## 9. 完整启动流程示例

```bash
# 1. 配置环境变量
vim .env
# 添加 BIYING_LICENSE 和至少一个 LLM API Key

# 2. 启动后端
cd backend
python main.py

# 3. 在另一个终端，注册AI
curl -X POST "http://localhost:8888/api/ai/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GPT-4 Trader",
    "model_name": "gpt-4",
    "initial_cash": 100000.0
  }'

# 4. 启动交易系统
curl -X POST "http://localhost:8888/api/system/start"

# 5. 查看系统状态
curl http://localhost:8888/api/system/status

# 6. 查看AI排行榜
curl http://localhost:8888/api/ai/ranking

# 7. 监控日志
tail -f backend/nof1_ashare.log
```

---

## 10. 数据库查看

### 使用DBeaver/Navicat
数据库文件位置：`backend/nof1_ashare.db`

### 使用命令行
```bash
cd backend
sqlite3 nof1_ashare.db

.tables              # 查看所有表
SELECT * FROM ai;    # 查看AI列表
SELECT * FROM order; # 查看订单
.quit
```

---

## 📞 技术支持

如有问题，请查看：
- 后端日志：`backend/nof1_ashare.log`
- API文档：http://localhost:8888/docs
- 系统状态：http://localhost:8888/api/system/status



