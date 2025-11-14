# Repository Guidelines

## Project Structure & Module Organization
- `README.md` 和 `微众银行Agent设计 .md` 定义流程、输入输出与合规边界，
  任何管线或护栏调整都要同步更新两份文档，以便评审溯源。
- 运行时代码放在 `agents/<AgentName>/`，包含 `__init__.py`、`builder.py`
  以及描述 schema 的 README；提示词与代理同级放入 `prompts/`，便于联调。
- 数据夹层与遮蔽样例位于 `tests/fixtures/<agent>/`，原始受限数据
  一律留在外部保管系统；若需新的 mock，请记录生成方式。
- 回归套件遵循 `tests/test_<agent>.py` 命名，测试内容源自设计文档里的
  JSON 场景，以确保规格与实现同步演进。

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`：建立共享虚拟环境，
  避免依赖漂移；团队默认使用该环境运行脚本。
- `pip install -r requirements.txt`：任何代理逻辑或工具更新后立刻同步，
  并在 PR 中说明新增依赖的用途。
- `pytest` / `pytest -k <agent>`：执行全部或单个代理的回归；失败日志需
  附在 PR 讨论中，便于 reviewer 快速复现。
- `markdownlint README.md 微众银行Agent设计 .md AGENTS.md`：提交前统一
  文档风格，减少合规审计返工。

## Coding Style & Naming Conventions
- 遵循 PEP 8、四空格缩进与完整类型提示；结构化 payload 优先 dataclass，
  便于静态分析与序列化。
- 函数/模块使用 `snake_case`，类名 `PascalCase`，适配器以 `Adapter`
  结尾；跨代理共享工具放在 `agents/common/`，并写明责任边界。
- 提示词文件名采用小写短横线（例：`intent-summary.prompt.md`），
  Markdown 行宽尽量 <80 字符，利于审查。
- 调整 Python 代码后依次运行 `ruff check` 与 `black .`；缺省配置时在
  `pyproject.toml` 增补，保持团队一致性。

## Testing Guidelines
- 每个代理最少包含快乐路径、边界值与合规防护测试，必要时加入
  负面示例验证拒绝策略。
- 外部服务一律用 fixture 取代，利用 `pathlib` 读取黄金 JSON；禁止
  在 CI 中触发真实 API。
- 目标分支覆盖率 ≥90%；若无法满足，需在 PR 中说明风险与后续计划。

## Commit & Pull Request Guidelines
- 提交信息遵循 Conventional Commits（如 `feat: intent scoring`、
  `fix: risk adapter`），方便自动生成变更日志。
- PR 描述需引用 `微众银行Agent设计 .md` 的相关章节并链接任务编号，
  同时附上 `pytest` 与 `markdownlint` 的最新运行记录。
- UI 或交互类输出需提供截图；涉及数据策略的修改必须抄送合规 reviewer。
- Merge 前至少获得一名代理负责人的批准，并在评论区记录任何未决风险。

## Security & Compliance Notes
- `prompts/` 与 `tests/fixtures/` 中的示例必须完全脱敏；发现可能的真实
  客户信息时立即停止提交并通知合规团队。
- 未经批准的密钥、证书与配置禁止写入仓库；若需本地调试，使用
  `.env.example` 指引开发者手动配置。

## Agent Readiness Checklist
- 为每个代理的 README 明确输入 schema、输出 schema 以及提示词设计思路，
  这样评审能快速匹配需求与实现。
- 上线前重新验证语气与合规指引，确保推荐语料、拒绝策略、fallback
  行为都符合银行监管期望。
