# Task: Feature Flag Evaluator

Implement `evaluate_flag` in `feature_flags/evaluator.py`.

## API

```python
def evaluate_flag(flag: dict, user: dict) -> dict:
    ...
```

## Flag Contract

Required flag fields:

- `key`: non-empty string.
- `default`: boolean.

Optional flag fields:

- `archived`: boolean. Archived flags are always disabled.
- `enabled`: boolean. When `False`, the flag is disabled before any targeting.
- `denylist`: list of user keys.
- `allowlist`: list of user keys.
- `rules`: list of targeting rules evaluated in order.
- `rollout_bps`: integer from `0` to `10000`.

Required user fields:

- `key`: non-empty string.

## Evaluation Order

Return the first matching decision:

1. `archived is True` -> disabled, reason `"archived"`.
2. `enabled is False` -> disabled, reason `"disabled"`.
3. User key in `denylist` -> disabled, reason `"denylist"`.
4. User key in `allowlist` -> enabled, reason `"allowlist"`.
5. First matching rule -> rule decision, reason `"rule:<rule name>"`.
6. `rollout_bps` present -> deterministic rollout decision, reason `"rollout"` or `"default"`.
7. Otherwise return `default`, reason `"default"`.

## Rules

Each rule is a dict with:

- `name`: non-empty string.
- `attribute`: user attribute name.
- `op`: one of `"equals"`, `"in"`, `"gte"`, `"lte"`.
- `value`: comparison value.
- `enabled`: boolean decision.

If the user does not have the requested attribute, the rule does not match.

## Rollout

Rollout uses this exact bucket algorithm:

```python
sha256(f"{flag_key}:{user_key}".encode("utf-8")).hexdigest()
bucket_bps = int(first_8_hex_chars, 16) % 10000
```

The user is enabled when `bucket_bps < rollout_bps`. The returned dict always includes the computed `bucket_bps`.

## Return Shape

```python
{
    "key": str,
    "enabled": bool,
    "reason": str,
    "bucket_bps": int | None,
}
```

Invalid inputs raise `ValueError`.
