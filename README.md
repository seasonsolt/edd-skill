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

## 已经测到的提升

第一轮真实 A/B forward test 跑在 `quote-engine` 任务上。

| 条件 | 总分 | 功能分 | 过程分 | hidden tests |
| --- | ---: | ---: | ---: | --- |
| baseline | 79 / 100 | 65 / 65 | 14 / 35 | pass |
| with EDD Skill | 99 / 100 | 65 / 65 | 34 / 35 | pass |

这轮结果很克制：EDD Skill 没有提升功能正确性，因为 baseline agent 也把功能做对了。它提升的是 agent loop 的可审计性，with-skill run 留下了报告、`evals/red.log`、`evals/green.log`，后续可以复盘评估契约、验证证据和新增回归。

这已经能证明一个实际价值：当功能都能做对时，EDD Skill 让 agent coding loop 更可审计。

还不能证明的是：它稳定提高所有任务的功能正确性。要下这个结论，需要更多 task family 和多轮 paired trials。

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
  hidden_tests/                     # 不给 agent 看的隐藏测试
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
```

每个目录里都有自己的 `PROMPT.md`。给每个 agent 只看它自己的 run 目录，不要暴露 `hidden_tests/`、`score_candidate.py` 或其它 sibling run。

所有 agent 完成后评分：

```bash
python3 benchmarks/skill-vs-no-skill/score_suite.py
```

## 多轮实验

单轮只能算 smoke test。更可信的做法是跑多轮：

```bash
python3 benchmarks/skill-vs-no-skill/prepare_suite.py --force --runs-root runs/skill-vs-no-skill-trials/trial-001
python3 benchmarks/skill-vs-no-skill/prepare_suite.py --force --runs-root runs/skill-vs-no-skill-trials/trial-002
python3 benchmarks/skill-vs-no-skill/score_trials.py --trials-root runs/skill-vs-no-skill-trials
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

EDD Skill 的价值在于把流程固定下来：

- 项目从哪些 eval 开始。
- 什么时候该写 test。
- test 写在哪。
- red log 和 green log 要怎么留。
- report 里要记录什么。
- benchmark 比较时哪些东西不能泄露给 agent。

这不是替代 Braintrust、LangSmith、Promptfoo、DeepEval 这类平台。它更像是 coding agent 的开发纪律层，可以和这些工具一起用。

## 当前边界

这个 repo 还在早期。

- 已完成：一个 Codex skill、两个 task family、hidden tests、suite scorer、trial scorer、benchmark integrity check。
- 已验证：`quote-engine` 单轮 A/B，with-skill 总分 +20，差异来自过程证据。
- 未完成：`feature-flags` 的真实 A/B run，多轮 paired trials，跨模型对比。

下一步最有价值的是跑 5 轮以上 paired trials，再看 median delta 是否稳定。
