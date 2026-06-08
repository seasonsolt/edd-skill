# Eval-Driven AI TDD

AI coding 已经很会写代码了，麻烦的是怎么知道它真的做对了。

这个 repo 做的是一件很小但很硬的事：把 TDD 的 red-green-refactor 循环迁移到 AI coding agent 上。Agent 不再直接开写，而是先把任务变成测试、eval 或 benchmark，再围绕这些可执行标准迭代。

```text
先写失败用例 -> 实现最小改动 -> 跑公开和隐藏测试 -> 留下红/绿证据 -> 记录回归
```

## 小创新

这里的创新点不是又做了一个 eval 平台，而是把 eval-first 做成 Codex skill，让它直接进入 agent 的开发动作里。

传统 TDD 约束的是人写代码的顺序。这个 skill 约束的是 agent loop 的顺序：

- 先定义行为契约，而不是先改实现。
- 先留下 red state，而不是最后补测试。
- 把失败样本变成 regression，而不是只修一次。
- 把功能正确性和过程证据分开评分。
- 用 hidden benchmark 防止 agent 靠改标准刷分。

它的目标不是让 agent 写更多文件，而是让 agent 的结果更可复现、更容易审计，也更适合长期迭代。

## 已经测到的提升

第一轮真实 A/B forward test 跑在 `quote-engine` 任务上。

| 条件 | 总分 | 功能分 | 过程分 | hidden tests |
| --- | ---: | ---: | ---: | --- |
| baseline | 79 / 100 | 65 / 65 | 14 / 35 | pass |
| with `$eval-driven-ai-tdd` | 99 / 100 | 65 / 65 | 34 / 35 | pass |

这轮结果很克制：skill 没有提升功能正确性，因为 baseline agent 也把功能做对了。它提升的是开发过程质量，with-skill run 留下了 `AI_TDD_REPORT.md`、`evals/red.log`、`evals/green.log`，后续可以复盘 red state、green state 和新增回归。

这已经能证明一个实际价值：当功能都能做对时，skill 让结果更可审计。

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

如果 with-skill 只提高过程分，说明它主要改善可审计性。如果它还提高 hidden pass rate，才说明它开始影响最终质量。

## 为什么值得做成 skill

把这件事写进 prompt 很容易失效。Agent 忙着实现时，经常会跳过 red state、补测试、或者最后只说自己跑过了。

Skill 的价值在于把流程固定下来：

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
