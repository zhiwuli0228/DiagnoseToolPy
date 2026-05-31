# DiagnoseToolPy

轻量级 Web 诊断助手，面向系统稳定性工作。DiagnoseToolPy 扫描服务器端日志目录，流式处理日志内容，生成证据包，并维护基于文件存储的故障知识库，支持无 embedding 的相似案例检索。

## 架构

```
Web UI (React) → FastAPI API → 服务模块 → 文件存储
```

| 模块 | 职责 |
|------|------|
| `diagnose_tool/api/` | FastAPI 路由层 — 仅做校验和格式化，不含业务逻辑 |
| `diagnose_tool/core/` | 配置加载、路径安全校验、共享模型 |
| `diagnose_tool/analyzer/` | 日志分析：目录扫描、流式读取、解析、分类、采样 — **不依赖 FastAPI** |
| `diagnose_tool/casebase/` | 故障案例生命周期：`case.md` + `metadata.yaml`，维护 `index.yaml` |
| `diagnose_tool/retrieval/` | 相似案例检索：关键词、规则、BM25（无需 embedding） |
| `diagnose_tool/exporter/` | 导出：Markdown、JSONL、ZIP、bugfix 提示词 |

**核心约束：**
- 文件系统是事实来源 — 无强制数据库依赖
- 大日志按行流式读取，不一次性加载到内存
- 检索无需 embedding，向量检索可选且默认关闭
- AI 诊断仅为辅助 — 保留人工确认根因的字段

## 快速启动

### 环境要求

- Python 3.12+
- Node.js 18+（前端）
- uv（后端包管理器）

### 1. 创建目录

```bash
mkdir -p data/input data/output data/cases data/indexes data/runtime
```

### 2. 启动后端

```bash
uv run uvicorn diagnose_tool.main:app --host 0.0.0.0 --port 18080 --reload
```

API 访问 `http://127.0.0.1:18080`

### 3. 启动前端（可选）

```bash
cd frontend
npm install
npm run dev
```

前端访问 `http://localhost:3000`（代理 `/api` 到后端 18080）

## 配置

编辑 `config/app.yaml`：

```yaml
app:
  name: DiagnoseToolPy
  version: 0.1.0
server:
  host: 0.0.0.0
  port: 18080
paths:
  allowed_input_roots:
    - /path/to/your/logs    # 允许访问的日志目录
    - data/input
  data_dir: data
llm:
  enabled: false            # 设为 true 开启 AI 诊断
  model: "gpt-4o-mini"
  base_url: "https://api.openai.com/v1"
  api_key: "your-key-here"
  timeout: 60
```

`allowed_input_roots` 限制了工具可访问的服务器目录，路径遍历不在此列表中的请求会被拒绝。

## 使用流程

1. **放置日志** — 将日志文件放到 `allowed_input_roots` 中的某个目录下
2. **扫描** — 在 Web UI 输入目录路径；后端扫描文件元数据（不读内容），返回文件数量和大小
3. **搜索** — 设置时间范围、线程号、关键字（AND 逻辑）、排除关键字，搜索日志内容
4. **聚合** — 开启聚合功能，按异常类型/消息模板分组统计；可选择是否含线程号、时间
5. **诊断** — 将搜索结果和相似历史案例发给 LLM 进行 AI 辅助诊断
6. **归档** — 将分析结果保存为故障案例（`case.md` + `metadata.yaml`），供后续检索

## 开发命令

### 后端

```bash
# 安装依赖
uv add fastapi uvicorn pydantic pydantic-settings pyyaml jinja2 python-multipart
uv add rank-bm25
uv add --dev pytest pytest-cov ruff

# 启动开发服务器
uv run uvicorn diagnose_tool.main:app --host 0.0.0.0 --port 18080 --reload

# 运行测试
uv run pytest

# 带覆盖率运行测试
uv run pytest --cov=diagnose_tool

# 代码检查
uv run ruff check .
```

### 前端

```bash
cd frontend
npm install

# 开发服务器（代理 /api 到 localhost:18080）
npm run dev

# 生产构建
npm run build

# 运行测试
npm test

# 带覆盖率运行测试
npm run test:coverage
```

## 生产部署

### Docker

```bash
# 构建镜像
docker build -t diagnose-tool .

# 启动（使用 docker-compose.yml 中的卷挂载）
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

### 所需主机目录

```bash
mkdir -p /data/diagnose/input      # 只读：放入日志文件
mkdir -p /data/diagnose/output    # 分析任务输出
mkdir -p /data/diagnose/cases     # 故障案例库
mkdir -p /data/diagnose/indexes    # BM25/检索索引
mkdir -p /data/diagnose/runtime   # 临时运行时文件
```

### nginx 配置（可选）

```nginx
server {
    listen 80;
    root /var/www/diagnosetoolpy/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:18080/api/;
    }
}
```

## 日志格式支持

支持复杂日志头格式：

```
2026-05-15 12:00:00,218 ERROR [[module]thread] [logger] message
```

支持特性：
- 毫秒分隔符支持点或逗号：`12:00:00.218` 或 `12:00:00,218`
- 模块/线程区嵌套括号：`[[order-core]worker-1]`
- 空占位符括号：`[]`
- 消息正文中的嵌套括号：JSON、SQL、URL、Map 格式
- 平衡括号扫描器 — 解析失败时不会丢失日志内容

## 存储结构

```
data/
├── input/              # 服务器日志文件（配置中为只读）
├── output/             # 分析任务输出
│   └── {task_id}/
│       ├── task.yaml
│       ├── evidence-pack.md
│       ├── case-draft.md
│       └── artifacts/
├── cases/              # 归档故障案例
│   └── {case_id}_{slug}/
│       ├── case.md
│       ├── metadata.yaml
│       └── evidence-pack.md
└── indexes/
    └── bm25/
        └── corpus.jsonl   # 持久化 BM25 语料库（可重建）
```