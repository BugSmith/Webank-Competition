# FundAdvice Agent

面向基金详情/建议场景的专用 Agent，输入单只基金的结构化信息，输出一条简洁、合规的投资提示。使用 agno + DashScope 默认模型，可按需替换为其他模型。

## 输入 Schema

```json
{
  "name": "基金名称",
  "code": "基金代码",
  "category": "混合型",
  "risk": "中高",
  "nav": 1.2345,
  "change": "+0.0123",
  "changePercent": "1.23%",
  "manager": "基金经理",
  "history": {
    "one_month": "-0.8%",
    "three_month": "4.6%"
  }
}
```

- `name` / `code` / `risk` / `changePercent` 为主要字段，其余字段可按需扩展。

## 输出

单条中文字符串（≤120 字），建议包含：
- 风险提示或投资风格说明；
- 结合涨跌幅给出适合的投资者类型；
- 明示“需结合自身风险承受能力”之类的合规措辞。

## 目录

| 文件 | 功能 |
|------|------|
| `builder.py` | 构建 `Agent` 与 prompt 渲染函数 |
| `service.py` | 提供 `FundAdviceService.generate_advice` 供业务调用 |

## 使用

```python
from agents.fund_advice import FundAdviceService

service = FundAdviceService()
advice = service.generate_advice({
    "name": "华夏回报混合A",
    "code": "002001",
    "risk": "中等",
    "changePercent": "1.24%",
    "manager": "张三"
})
print(advice)
```
