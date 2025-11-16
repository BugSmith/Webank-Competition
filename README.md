# 微众银行智能代理管线

本仓库基于 agno 框架实现微众银行零售业务的多智能体管线，实现了设计文档《微众银行Agent设计.md》中描述的社会角色、资产、行为洞察与总结治理流程。

## 架构一览
- `SocioRoleAgent`：解析身份、联系方式与常驻地信息，生成标准化的年龄、性别、城市层级及合规开关。
- `AssetAgent`：依据账户总资产和风险问卷，映射资产等级、R1–R5 风险等级以及授信与还款能力信号。
- `BehaviorAgent`：将应用行为日志、搜索词和市场波动转化为意图标签、活跃度与流失预警。
- `SummaryAgent`：汇总上游输出，消解冲突，输出运营/产品/客服的行动建议与语气指引。
- `ConversationAgent`：读取上述洞察与会话历史，为 Fin-ai 前端提供多轮对话与动作指引。
- `WebankAgentPipeline`：按顺序调用各代理，负责输入裁切、提示构建与 JSON 结果的整理。

## 目录结构
- `agents/`：各代理的 agno 构建器与系统提示，以及整体管线入口。
- `agents/conversation/`：AI 助手多轮会话中台，内含记忆管理、洞察检索与持久化。
- `AGENTS.md`：贡献者规范，涵盖目录约定、测试与提交流程。
- `微众银行Agent设计.md`：官方业务设计说明，内含规则、打分权重与 JSON 示例。

## 快速开始
1. 新建并激活 Python 3.10+ 虚拟环境。
2. 安装依赖（`requirements.txt` 会拉取 agno、DashScope SDK 及 OpenTelemetry）。
3. 设置 DashScope 凭据，可选地调整模型与温度。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 写入你的 DashScope / LangSmith 凭证
```

## 使用示例
```python
from agents import build_default_pipeline

pipeline = build_default_pipeline()
inputs = {
    "socio_role": {...},
    "asset": {...},
    "behavior": {...},
    "context": {}
}
result = pipeline.run(inputs)
print(result["summary"]["recommendations"])
```

## 一键运行
项目根目录提供 `start.sh`（会自动读取同目录下的 `.env`），常用命令如下：

```bash
# 安装 Python / 前端依赖
./start.sh install

# 刷新某个用户的离线洞察
./start.sh pipeline tests/fixtures/pipeline/sample_payload.json UTSZ /tmp/utsz_insights.json

# 启动 Flask 后端（需预先 export DASHSCOPE_API_KEY / BASE_URL）
./start.sh backend

# 启动 Vite 前端
./start.sh frontend
```

## CLI 刷新洞察
可使用打包好的命令行工具运行完整管线并将结果写入数据库（等价于调用 `/api/ai/insights/refresh`）。如需在本地无数据库时跳过持久化，可加 `--skip-db` 或设置 `WEBANK_SKIP_DB=true`：

```bash
python -m agents.cli refresh-insights \
  --input tests/fixtures/pipeline/sample_payload.json \
  --user-id UTSZ \
  --skip-db \
  --output /tmp/utsz_insights.json
```

所有代理默认使用 DashScope 的 `qwen-turbo-latest` 模型，请确保输入 JSON 与设计文档示例保持一致，以获得合规且结构化的输出。在扩展逻辑或接入外部服务前，建议在 `tests/` 目录补充回归测试，验证各阶段契约的稳定性。

## 前后端联动要点
- 后端 `/api/ai/conversation` / `/api/ai/insights/refresh` 已直接复用 `agents/conversation`，请在启动 Flask 前设置 `DASHSCOPE_API_KEY`、`DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1` 以及 `AGNO_MODEL_ID=qwen-turbo-latest`。
- 行为 Agent 现在会生成 `user_tip` 字段，后端将其转换成适合展示的短句，确保 AI 气泡不再出现原始 JSON。
- 基金列表接口支持携带 `userId`，服务端会根据最新 Summary 中的 `recommendations` 为命中的基金添加 `highlighted/highlightReason`，前端据此仅高亮真正适配的产品。
- 基金建议 API 默认启动 5 分钟内的 Agent 结果缓存，可通过 `FUND_ADVICE_CACHE_TTL`（秒）调整或关闭（设为 `0`）。命中缓存时响应包含 `cacheHit: true` 字段。

## LangSmith 监控接入
仓库已内置 `agents/common/telemetry.py`，当开启 OpenTelemetry 配置后，`WebankAgentPipeline`、`ConversationService` 以及行为/基金等运行时桥接层都会自动为每次 LLM 调用生成一个 span，并通过 OTLP 推送到 LangSmith：

```bash
export LANGSMITH_API_KEY="<your-langsmith-key>"
export LANGSMITH_PROJECT="webank-dev"            # 可选，默认走 LangSmith 的默认项目
export WEBANK_ENABLE_OTEL=true                    # 显式启用可观测性
# 可选：覆盖服务名或自定义 OTLP 目的地
# export OTEL_SERVICE_NAME="webank-agents"
# export OTEL_EXPORTER_OTLP_ENDPOINT="https://api.smith.langchain.com/otel/v1/traces"
```

- 若需要自定义 Header，可设置 `OTEL_EXPORTER_OTLP_HEADERS`（例如 `x-api-key=...,x-langsmith-project=...`）。
- 也可以直接设置标准 OpenTelemetry 环境变量（`OTEL_EXPORTER_OTLP_*`）；只要 tracer provider 尚未初始化，`configure_tracing()` 会自动采用这些参数。
- 启动 `./start.sh pipeline`、`./start.sh backend` 或运行 `agents.cli`、`myos.py` 时均会触发同一套追踪逻辑，从而在 [LangSmith Sessions](https://smith.langchain.com/) 页面查看调用链、耗时与错误详情。
