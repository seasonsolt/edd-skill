# Benchmark Protocol

Use this when comparing skills, prompts, agents, models, or workflows.

## Minimum Credibility Bar

- Use at least two task families before claiming general value.
- Use paired runs: each baseline task copy must have a matching with-skill copy from the same starter state.
- Keep hidden tests, scorer code, expected answers, and prior results out of agent-visible task directories.
- Score functional quality and process quality separately.
- Keep the agent loop and the benchmark scorer separate. The agent can run public tests and visible evals; the scorer runs hidden tests after the run.
- Record model, date, prompt, task version, score version, and command outputs.
- Treat one pair as a smoke test. Prefer 5 or more pairs per task family before making a strong claim.

## What To Measure

- Functional score: public tests, hidden tests, oracle cases, invariants, and runtime behavior.
- Process score: red evidence, green evidence, regression tests, report, and reproducibility.
- Stability: median score, worst-case score, hidden-pass rate, and variance across repeated paired trials.
- Cost: elapsed time, tool calls, tokens if available, and added files.

## Bias Controls

- Do not let either run inspect hidden tests or scorer internals.
- Do not change the task after seeing one side's result.
- Use identical time budgets and model settings.
- Randomize task order when running many trials.
- Preserve raw artifacts so later reviewers can audit the score.
- When hidden tests find a useful miss, turn it into a visible regression only after that run has been scored.

## Reporting

Report:

- Number of task families and paired runs.
- Median baseline score and median with-skill score.
- Functional delta and process delta separately.
- Hidden-test pass-rate delta.
- Known limitations and failed cases.
