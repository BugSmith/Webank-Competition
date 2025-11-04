# 微众银行智能代理管线

本仓库基于 agno 框架实现微众银行零售业务的多智能体管线，实现了设计文档《微众银行Agent设计.md》中描述的社会角色、资产、行为洞察与总结治理流程。

## 架构一览
- `SocioRoleAgent`：解析身份、联系方式与常驻地信息，生成标准化的年龄、性别、城市层级及合规开关。
- `AssetAgent`：依据账户总资产和风险问卷，映射资产等级、R1–R5 风险等级以及授信与还款能力信号。
- `BehaviorAgent`：将应用行为日志、搜索词和市场波动转化为意图标签、活跃度与流失预警。
- `SummaryAgent`：汇总上游输出，消解冲突，输出运营/产品/客服的行动建议与语气指引。
- `WebankAgentPipeline`：按顺序调用各代理，负责输入裁切、提示构建与 JSON 结果的整理。

## 目录结构
- `agents/`：各代理的 agno 构建器与系统提示，以及整体管线入口。
- `AGENTS.md`：贡献者规范，涵盖目录约定、测试与提交流程。
- `微众银行Agent设计.md`：官方业务设计说明，内含规则、打分权重与 JSON 示例。

## 快速开始
1. 新建并激活 Python 3.10+ 虚拟环境。
2. 安装依赖（确保包含 `agno`）。
3. 设置 DashScope 凭据，可选地调整模型与温度。

```bash
python -m venv .venv
source .venv/bin/activate
pip install agno
export DASHSCOPE_API_KEY="<your-key>"
export AGNO_MODEL_ID="qwen3-max"  # 可选，默认即为该模型
export AGNO_TEMPERATURE="0.3"      # 可选
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

所有代理默认使用 DashScope 的 `qwen3-max` 模型，请确保输入 JSON 与设计文档示例保持一致，以获得合规且结构化的输出。在扩展逻辑或接入外部服务前，建议在 `tests/` 目录补充回归测试，验证各阶段契约的稳定性。
