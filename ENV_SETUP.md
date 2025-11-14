# 🔑 环境变量配置指南

## 设置API Keys

在项目根目录创建 `.env` 文件，或直接在终端设置环境变量：

### 方法1：使用.env文件（推荐）

在项目根目录创建 `.env` 文件：

```bash
# Qwen (阿里云百炼)
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# Kimi (月之暗面)
MOONSHOT_API_KEY=sk-xxxxxxxxxxxxxxxx

# 可选：其他LLM
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 方法2：终端设置（临时）

```bash
# 每次启动前设置
export DASHSCOPE_API_KEY='sk-xxxxxxxxxxxxxxxx'
export MOONSHOT_API_KEY='sk-xxxxxxxxxxxxxxxx'
```

### 方法3：永久设置（推荐）

**macOS/Linux** - 添加到 `~/.zshrc` 或 `~/.bashrc`:

```bash
# 编辑配置文件
nano ~/.zshrc

# 添加以下内容
export DASHSCOPE_API_KEY='sk-xxxxxxxxxxxxxxxx'
export MOONSHOT_API_KEY='sk-xxxxxxxxxxxxxxxx'

# 保存后重新加载
source ~/.zshrc
```

---

## 🔒 安全说明

### ✅ 正确做法

1. **API Key存环境变量**，不存数据库
2. **`.env`文件加入`.gitignore`**，不提交到Git
3. **生产环境**使用密钥管理服务

### ❌ 错误做法

- ❌ 不要把API Key写死在代码里
- ❌ 不要把API Key存入数据库
- ❌ 不要把`.env`文件提交到Git

---

## 📋 你的API Key信息

根据你提供的调用代码，以下是配置信息：

### Qwen3-Max (阿里云百炼)
```bash
export DASHSCOPE_API_KEY='你的key'
# 或在 ais_config.py 中已配置：
# base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
# model: qwen-plus
```

### Kimi K2 (月之暗面)
```bash
export MOONSHOT_API_KEY='你的key'
# 或在 ais_config.py 中已配置：
# base_url: https://api.moonshot.cn/v1
# model: kimi-k2-turbo-preview
```

---

## 🚀 验证配置

设置完环境变量后，验证是否生效：

```bash
# 验证环境变量
echo $DASHSCOPE_API_KEY
echo $MOONSHOT_API_KEY

# 导入AI到数据库
cd backend
python3 scripts/import_ais.py
```

---

## 💡 工作流程

1. **配置环境变量**（上面的方法）
2. **修改`backend/ais_config.py`**（添加/删除AI）
3. **运行导入脚本**：`python3 scripts/import_ais.py`
4. **启动服务**：API Key自动从环境变量读取

---

## 🔍 运行时如何读取

系统会在需要调用LLM时：

```python
import os

# 从环境变量读取（不从数据库）
api_key = os.getenv('DASHSCOPE_API_KEY')
```

**优点**：
- ✅ 安全：Key不存数据库
- ✅ 灵活：可以随时更换Key
- ✅ 标准：符合12-Factor App原则

