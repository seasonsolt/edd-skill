# EDD Skill

AI coding 已经很会写代码了，麻烦的是怎么知道它真的做对了。

EDD 是 Eval-Driven Development。它把评估放到 AI 项目的开端，而不是把测试留到实现之后。这个 repo 做的是一件很小但很硬的事：先建立 eval、benchmark 和评分契约，再让 agent coding loop 围绕这些标准运转。

```text
评估契约 -> agent coding loop -> 可见验证证据 -> hidden benchmark 独立评分 -> 失败回流成 regression
```

## 小创新

这里的创新点不是又做了一个 eval 平台，而是把 eval-first 做成 Codex skill。它不要求你换模型、换 IDE、重写项目架构，只改 agent 写代码时的循环。

EDD Skill 约束的是这几件事：

- 项目一开始先定义评估契约，而不是先堆实现。
- agent 每次动代码前，先绑定到当前 eval 或 benchmark。
- agent 只运行自己可见的 public tests/evals，hidden benchmark 留给独立评分器。
- 线上失败、hidden 失败和人工纠错回流成 regression。
- 把功能正确性和过程证据分开评分。
- 用 hidden benchmark 防止 agent 靠改标准刷分，也防止我们被漂亮过程骗过。

它的目标不是让 agent 写更多文件，而是让 agent 的结果更可复现、更容易审计，也更适合长期迭代。

## 最新 benchmark 结论

当前最可信的一轮正式实验是 5 个 paired trials，覆盖四个 task family：`quote-engine`、`feature-flags`、`tool-call-planner`、`evidence-answerer`。每个 trial 都有 baseline 与 with-skill 两个条件，hidden tests 和 scorer 都不暴露给 agent。

| 指标 | baseline | with EDD Skill | delta |
| --- | ---: | ---: | ---: |
| median total score | 66.5 / 100 | 86.5 / 100 | +19.75 |
| mean total score | 67.45 / 100 | 86.45 / 100 | +19.0 |
| median functional delta | - | - | 0 |
| median process delta | - | - | +19.75 |
| hidden pass rate | 15 / 20 | 15 / 20 | 0 |
| `tool-call-planner` hidden pass rate | 0 / 5 | 0 / 5 | 0 |
| `assess_trials.py` verdict | - | - | `not_supported` |

客观结论更严格：在四任务 benchmark 上，EDD Skill 没有提升 hidden functional correctness。`quote-engine`、`feature-flags`、`evidence-answerer` 两边都通过 hidden tests；`tool-call-planner` 两边都失败。with-skill 的过程分更高，但 median process delta 是 `+19.75`，低于预先设定的 `+20` gate，所以固定判定脚本给出 `not_supported`。

这不是坏结果，反而是 benchmark loop 应该给出的结果：它说明当前 skill 还不能被认为有效。它可能仍然有过程提醒价值，但在这轮更严格的证据门槛下，没有证明出可宣称的效果。

下一步应该把这次失败当作输入：分析 baseline 为什么也能自然地产生高过程证据、把 `tool-call-planner` hidden miss 转成 visible regression/task v2，再跑下一轮。不要为了让 skill 看起来有效而调低 gate。

### 失败复盘诊断

新增诊断脚本会读取已评分的 run artifacts，解释为什么 verdict 是
`not_supported`：

```bash
python3 benchmarks/skill-vs-no-skill/analyze_trials.py --trials-root runs/skill-vs-no-skill-trials-4task
```

当前诊断结论：

- baseline mean process score: `14.95 / 35`
- with-skill mean process score: `33.95 / 35`
- baseline complete evidence runs: `1 / 20`
- with-skill complete evidence runs: `20 / 20`
- hidden pass delta: `0`
- `tool-call-planner` public-green/hidden-red failures: baseline `5 / 5`, with-skill `5 / 5`

这说明 skill 确实让 agent 更稳定地留下评估证据，但还没有证明能提升 hidden correctness。失败复盘见 [docs/FOUR_TASK_BENCHMARK_REVIEW.md](docs/FOUR_TASK_BENCHMARK_REVIEW.md)。

## Repo 里有什么

```text
.agents/skills/eval-driven-ai-tdd/
  SKILL.md                         # Codex skill 主流程
  references/
    eval-first-contract.md          # 如何把需求变成 eval/test contract
    benchmark-protocol.md           # 如何做可信 benchmark
  scripts/
    check_ai_tdd_artifacts.py       # 检查 red/green/report/regression 证据

benchmarks/skill-vs-no-skill/
  task/                             # quote-engine starter task
  tasks/feature-flags/              # feature-flags starter task
  tasks/tool-call-planner/           # tool-call planning starter task
  tasks/evidence-answerer/           # evidence-grounded answer starter task
  hidden_tests/                     # 不给 agent 看的隐藏测试
  assess_trials.py                  # 按固定门槛判断 skill 证据强度
  analyze_trials.py                 # 解释 not_supported / process leakage / hidden failure pattern
  prepare_suite.py                  # 生成多任务 A/B run 目录
  score_suite.py                    # 聚合多任务分数
  score_trials.py                   # 聚合多轮 trial
  verify_benchmark.py               # 证明 starter 红、参考实现绿
  RESULTS.md                        # 当前实验记录
```

## 快速验证 benchmark 是可信的

先跑 benchmark integrity check：

```bash
python3 benchmarks/skill-vs-no-skill/verify_benchmark.py
```

它检查两件事：

- starter task 必须是红态，分数为 `0`。
- reference implementation 必须通过 public + hidden tests。

当前结果：

```text
quote-engine: starter 0, reference public+hidden pass
feature-flags: starter 0, reference public+hidden pass
tool-call-planner: starter 0, reference public+hidden pass
evidence-answerer: starter 0, reference public+hidden pass
```

这一步很重要。否则 benchmark 本身不可信，后面再比较 agent 也没意义。

注意，hidden tests 不属于 agent coding loop。agent 不应该看到它们，也不应该运行它们。hidden benchmark 是独立评分层，用来判断 agent-visible eval 有没有漏掉关键行为。

## 跑一次多任务 A/B

准备 paired runs：

```bash
python3 benchmarks/skill-vs-no-skill/prepare_suite.py --force
```

它会生成：

```text
runs/skill-vs-no-skill-suite/quote-engine/baseline
runs/skill-vs-no-skill-suite/quote-engine/with-skill
runs/skill-vs-no-skill-suite/feature-flags/baseline
runs/skill-vs-no-skill-suite/feature-flags/with-skill
runs/skill-vs-no-skill-suite/tool-call-planner/baseline
runs/skill-vs-no-skill-suite/tool-call-planner/with-skill
runs/skill-vs-no-skill-suite/evidence-answerer/baseline
runs/skill-vs-no-skill-suite/evidence-answerer/with-skill
```

每个目录里都有自己的 `PROMPT.md`。给每个 agent 只看它自己的 run 目录，不要暴露 `hidden_tests/`、`score_candidate.py` 或其它 sibling run。

所有 agent 完成后评分：

```bash
python3 benchmarks/skill-vs-no-skill/score_suite.py
```

## 多轮实验

单轮只能算 smoke test。更可信的做法是跑多轮：

```bash
python3 benchmarks/skill-vs-no-skill/prepare_trials.py --clean-root --trial-count 5
python3 benchmarks/skill-vs-no-skill/score_trials.py --trials-root runs/skill-vs-no-skill-trials --expected-trial-count 5
```

然后让固定判定脚本评估证据强度：

```bash
python3 benchmarks/skill-vs-no-skill/assess_trials.py --trials-root runs/skill-vs-no-skill-trials
```

如果结果没有支撑 claim，再跑诊断：

```bash
python3 benchmarks/skill-vs-no-skill/analyze_trials.py --trials-root runs/skill-vs-no-skill-trials
```

看这些指标：

- median total score
- functional score delta
- process score delta
- hidden-test pass rate
- worst-case score

如果 with-skill 只提高过程分，说明 EDD 主要改善 agent loop 的可审计性。如果它还提高 hidden pass rate，才说明它开始影响最终质量。

## 为什么值得做成 skill

把这件事写进 prompt 很容易失效。Agent 忙着实现时，经常会跳过评估契约、补测试，或者最后只说自己跑过了。

EDD Skill 试图把这些流程固定下来：

- 项目从哪些 eval 开始。
- 什么时候该写 test。
- test 写在哪。
- red log 和 green log 要怎么留。
- report 里要记录什么。
- benchmark 比较时哪些东西不能泄露给 agent。

这不是替代 Braintrust、LangSmith、Promptfoo、DeepEval 这类平台。它更像是 coding agent 的开发纪律层，可以和这些工具一起用。

## 当前边界

这个 repo 还在早期。

- 已完成：一个 Codex skill、四个 task family、hidden tests、suite scorer、trial scorer、benchmark integrity check、trial assessment gate。
- 已补充：trial diagnostics，用来解释 baseline artifact leakage 和 public-green/hidden-red failure pattern。
- 已验证：5 轮 paired trials，覆盖 4 个 task family，40 个独立 worker runs。
- 已发现：`tool-call-planner` 成功增加 hidden functional 区分度，但 baseline 和 with-skill 都没有通过这类 hidden tests。
- 已判定：`assess_trials.py` 在默认门槛下给出 `not_supported`。当前 skill 没有证明 hidden functional uplift，也没有过 process-effect gate。
- 未完成：把 `tool-call-planner` hidden miss 回流成 visible regression/task v2、跨模型对比、成本/耗时统计、检查 baseline 自发产生 EDD-like artifacts 的原因。

下一步最有价值的是做失败复盘，而不是继续宣传：先解释为什么 baseline process score 已经偏高，再决定 skill 是否需要改，或是否应该承认它只是一套普通提示纪律。
