# Conversation Agent

负责将现有资产 / 行为 / 社会角色等洞察与用户多轮对话串联，提供合规的 App 内 AI
助手体验。

## 输入

```json
{
  "user_id": "UTSZ",
  "message": "我是否要增加债券配置？",
  "session_id": "sess-123",
  "context": {
    "pageType": "financing",
    "fundCode": "161725"
  }
}
```

- `user_id`：必填，唯一标识客户。
- `session_id`：选填；为空时由服务端生成。
- `context`：来自前端的页面上下文，写入 `ai_sessions.page_context` 方便审计。

## 输出

```json
{
  "sessionId": "sess-123",
  "response": "结合您近 3 个月的现金流...",
  "actions": [
    {"type": "navigate", "page": "fund_detail", "payload": {"code": "161725"}}
  ],
  "insight_refs": ["asset:2024-10-01", "behavior:2024-10-05"]
}
```

## 目录结构

| 文件 | 说明 |
|------|------|
| `builder.py` | 封装 agno Agent 以及 prompt 拼装 |
| `memory.py` | 读写 `ai_sessions` / `ai_session_messages` |
| `retriever.py` | 统一查询资产、行为、社会角色、摘要快照 |
| `persistence.py` | 将 pipeline 结果写入快照表 |
| `service.py` | 面向后端的高阶接口，负责多轮对话编排 |

## 依赖表

| 表名 | 作用 |
|------|------|
| `user_asset_snapshots` | 资产细分与授信快照 |
| `user_behavior_insights` | 行为意图、运营信号 |
| `user_socio_roles` | 社会角色标签 |
| `user_insight_summary` | Summary Agent 输出 |
| `ai_sessions` | 多轮会话 Session |
| `ai_session_messages` | 会话消息记录 |

## 使用方式

```python
from agents.conversation import ConversationService

service = ConversationService(history_limit=10)
result = service.generate_reply(
    user_id="UTSZ",
    message="我想了解理财组合建议",
    context={"pageType": "financing"}
)
print(result["response"])
```

配套的 `persist_pipeline_output` 可由离线任务调用，确保洞察总是最新。
