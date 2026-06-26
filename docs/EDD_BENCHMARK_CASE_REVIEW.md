# EDD Benchmark Case Review

本文审查当前 `skill-vs-no-skill` benchmark 的评分 case 是否合理，以及它们是否契合 EDD Skill 的核心场景。

背景洞见：

> 高强度使用 AI 编程后，最大的感受不是要先让 AI 实现什么，而是先让 AI 实现对预期结果的验证逻辑。让结果先能被测试、被验证。否则编码无法持续，系统会长期处在 buggy 状态。

## 结论

当前 case 是合理的早期 benchmark，但没有完全对准这个洞见。

它们适合验证：

- agent 是否会在实现前后补测试；
- agent 是否留下 red/green 证据和报告；
- hidden tests 是否能发现 public tests 漏掉的边界；
- hidden failure 是否能回流成 visible regression。

它们不够适合验证：

- agent 是否能从模糊目标中先提炼验证契约；
- agent 写出的测试是否真的能保护后续迭代；
- EDD 是否让多轮 AI 编程更可持续；
- 验证逻辑本身能否捕获真实项目中的 seeded bugs。

因此，当前结果支持 `process_only_supported` 是合理的。它证明 EDD Skill 改变了 agent coding loop，但还没有证明 EDD Skill 提升 hidden functional correctness。

## 当前 Case 的适配度

| Task | 当前价值 | 与 EDD 洞见的偏差 | 建议 |
| --- | --- | --- | --- |
| `quote-engine` | 规则多、边界多，适合测边界测试意识 | 规格已经非常完整，baseline 只要认真实现就能通过 | 保留为 deterministic contract task，但降低它对核心 claim 的权重 |
| `feature-flags` | 有 precedence、rollout、invalid input，适合测回归覆盖 | 仍然是完整规格实现题，不太测“先定义预期” | 保留，增加 seeded buggy implementation 检测 |
| `tool-call-planner` | 最接近 AI agent 场景，policy、approval、prompt injection 都有现实意义 | hidden failure 来自 public tests 没覆盖的已写明规则，容易变成普通漏测 | 保留，但改成多轮变更和安全策略回归任务 |
| `tool-call-planner-v2` | 证明 hidden miss 回流成 visible contract 后，两边都能学会 | 它验证 benchmark loop，不验证 skill-specific lift | 保留为 regression-loop evidence，不应作为 functional uplift 证据 |
| `evidence-answerer` | 接近 RAG/evidence 场景，可信源、冲突、引用都合理 | 事实格式过于结构化，减少了 eval 设计难度 | 保留，但增加 eval cases/rubric 设计要求 |

## 为什么 Functional Delta 没有出现

当前 suite 的任务分布造成了功能分差异空间很小：

- 简单或明确的任务，两边都能通过 hidden tests。
- 唯一稳定困难的 `tool-call-planner`，两边都失败。
- `tool-call-planner-v2` 把失败模式公开后，两边又都通过。

这会自然产生 `hidden pass delta = 0`。这不等于 EDD 没价值，而是说明当前 benchmark 更擅长测过程纪律，不擅长测验证先行带来的长期质量收益。

## 更契合 EDD 的评分对象

下一版 benchmark 应该把“验证逻辑”从过程证据升级为可功能评分的对象。

建议新增三类评分。

### 1. Test-Kills-Bugs Score

给每个任务准备一组 scorer-only seeded buggy implementations。agent 完成后，不只运行它自己的实现，还要用 agent 写出的 tests/evals 去跑这些 buggy implementations。

评分问题：

```text
agent 写出的验证逻辑能抓住多少已知错误实现？
```

这比“agent 是否写了 5 个测试”更契合 EDD。测试数量和文件存在只是过程证据；能杀死 bug 才是验证逻辑质量。

### 2. Multi-Turn Regression Score

把任务设计成两到三轮：

1. 第一轮实现核心行为。
2. 第二轮追加需求。
3. 第三轮修复一个冲突或线上 bug。

评分问题：

```text
第二轮和第三轮之后，第一轮行为是否仍然被 agent 自己的验证逻辑保护？
```

这直接对应“AI 编程无法持续，永远 buggy”的痛点。EDD 的优势不一定在单轮实现，而在后续变更不把旧行为弄坏。

### 3. Eval-Contract Extraction Score

给 agent 的任务不再是完整 `TASK.md`，而是半结构化需求，例如产品说明、bug report、用户示例、约束列表。

评分问题：

```text
agent 是否先把模糊预期提炼成可执行 contract？
contract 是否覆盖 success、boundary、failure、regression？
```

这更接近真实 AI 编程：用户通常不会一开始就给出完整形式化规格。

## 下一版 Benchmark 形态

建议保留现有 suite 作为 `kata-suite`，新增一个更贴合 EDD 的 `sustainability-suite`。

```text
benchmarks/
  skill-vs-no-skill/
    kata-suite/                 # 当前完整规格实现题，测过程纪律和 hidden correctness
    sustainability-suite/       # 新 suite，测验证先行是否支撑持续迭代
```

`sustainability-suite` 的任务应具有这些特征：

- public tests 很少，只作为 smoke test；
- task prompt 故意保留一定需求模糊度；
- 评分器隐藏 seeded buggy implementations；
- 评分器检查 agent-added tests/evals 的 bug-killing 能力；
- 任务包含至少一次后续需求变更；
- 最终功能分、验证逻辑分、过程证据分分开记录。

## 模型分层

评分应基于两种模型层级，而不是只在单一模型上比较：

| 层级 | 示例标签 | 要回答的问题 |
| --- | --- | --- |
| SOTA 模型 | `gpt5.5` | 当模型本身已经很强时，EDD 是否仍然带来验证质量和回归保护收益？ |
| 经济模型 | `gpt5.4mini` | 当模型更便宜、更弱时，EDD 是否能通过验证脚手架显著提高可靠性？ |

这里的 `gpt5.5` 和 `gpt5.4mini` 先作为 benchmark 配置标签。真实实验前，需要映射到执行环境里可用的精确 model ID，并记录在 run metadata 中。

不要把两种模型直接平均成一个总 headline。应该先分层报告：

```text
SOTA baseline
SOTA with EDD Skill
Economical baseline
Economical with EDD Skill
```

核心 delta：

```text
SOTA skill delta = SOTA with-skill - SOTA baseline
Economical skill delta = economical with-skill - economical baseline
Skill leverage gap = economical skill delta - SOTA skill delta
```

`Skill leverage gap` 很重要。EDD 的价值可能不是让最强模型多过几个 hidden tests，而是让经济模型在有验证契约、regression tests 和 seeded-bug checks 的情况下更接近可持续使用。

最小可信矩阵：

```text
5 trials * 2 task families * 2 model tiers * 2 skill conditions = 40 runs
```

如果继续使用五个 task family，则是：

```text
5 trials * 5 task families * 2 model tiers * 2 skill conditions = 100 runs
```

## 推荐评分结构

当前评分是：

```text
public tests: 15
hidden tests: 50
process: 35
total: 100
```

对 EDD claim，更合适的结构是：

```text
final behavior hidden tests: 35
agent verification kills seeded bugs: 30
multi-turn regression preservation: 20
process evidence: 15
total: 100
```

这样可以避免 process artifacts 抬高总分但无法说明质量提升，也可以避免只看最终 hidden tests 而忽略 EDD 的真正产物：验证逻辑。

## 建议新增任务

### `subscription-billing-evolution`

场景：订阅账单系统。

轮次：

1. 支持 base plan、seat price、usage overage。
2. 新增 coupon、minimum charge、tax。
3. 修复 proration/refund bug。

EDD 价值点：

- 金额计算容易出现边界 bug；
- 后续需求容易破坏旧规则；
- agent 需要先建立 examples、invariants、rounding rules。

### `agent-policy-evolution`

场景：tool-call planner 的多轮安全策略演进。

轮次：

1. 基础 tool selection。
2. 新增 policy precedence 和 approval。
3. 新增 prompt injection 和 missing-tool behavior。

EDD 价值点：

- 最接近 AI app；
- 需要把安全边界写成 tests；
- 适合 seeded bugs，例如先选 tool 后检查 policy、被 text 覆盖 intent。

### `rag-answer-quality`

场景：RAG answerer，但输入不再是简单 `Fact:` 行。

轮次：

1. 从 passages 中抽取答案和 citation。
2. 新增 source trust、conflict、insufficient evidence。
3. 新增 answer rubric，例如禁止使用 untrusted instruction。

EDD 价值点：

- 需要 eval cases 和 rubric；
- 不是纯确定性代码；
- 更能体现“先定义怎么验证答案质量”。

## 当前 Claim 应该如何表述

不建议说：

```text
EDD Skill makes agents write more correct code.
```

当前证据不足。

建议说：

```text
EDD Skill reliably changes the agent coding loop: it makes agents create visible verification artifacts, red/green evidence, regression tests, and audit reports. The current benchmark supports process and reproducibility improvements, but not hidden functional uplift yet.
```

如果要贴近原始洞见，可以进一步说：

```text
The next benchmark should measure the quality of verification logic itself: whether agent-written tests and evals catch seeded bugs and preserve behavior across multi-turn AI coding.
```

## 具体下一步

1. 保留现有五任务结果，不重新解释为 functional win。
2. 新增 `sustainability-suite` 设计文档，先定义评分契约。
3. 为一个任务实现 seeded buggy implementation scorer。
4. 先跑单任务 paired trial，确认 test-kills-bugs score 能区分 baseline 和 with-skill。
5. 再扩展到至少两个任务 family 和五轮 paired trials。

最小可行下一步是做 `agent-policy-evolution`。它可以复用当前 `tool-call-planner` 代码和隐藏失败经验，但评分目标从“最终实现是否过 hidden tests”扩展为“agent 写出的验证逻辑是否能抓住策略类 seeded bugs”。
