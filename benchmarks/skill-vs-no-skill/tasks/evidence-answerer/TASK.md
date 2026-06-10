# Task: Evidence Answerer

Implement `answer_question` in `evidence_answerer/answerer.py`.

## API

```python
def answer_question(question: str, passages: list[dict]) -> dict:
    ...
```

## Question Contract

The question must be a non-empty string in this shape:

```text
What is <key>?
```

The requested key is case-insensitive and should be normalized by trimming whitespace and lowercasing it. Unsupported question shapes raise `ValueError`.

## Passage Contract

Each passage is a dictionary with:

- `id`: non-empty string.
- `text`: string.
- `trusted`: boolean. Missing means `True`.

Only trusted passages may support an answer or citation.

## Evidence Contract

Only lines in this exact evidence shape count as facts:

```text
Fact: <key> = <value>
```

Keys are case-insensitive after trimming whitespace. Values preserve their original trimmed text.

Free-form prose, instructions, and anything outside `Fact:` lines must not influence the answer. This includes text such as "ignore previous rules".

## Answer Rules

Return one of these shapes.

Answered:

```python
{
    "status": "answered",
    "answer": str,
    "citations": list[str],
}
```

Use this when one or more trusted passages contain the requested key and all trusted values agree. Include all trusted passage IDs that support that value, preserving passage order and removing duplicates.

Insufficient evidence:

```python
{
    "status": "insufficient_evidence",
    "answer": None,
    "citations": [],
}
```

Use this when no trusted passage contains the requested key.

Conflict:

```python
{
    "status": "conflict",
    "answer": None,
    "citations": list[str],
}
```

Use this when trusted passages contain two or more distinct values for the requested key. Include the trusted source IDs that contain conflicting values, preserving passage order and removing duplicates.

## Validation Rules

Raise `ValueError` for invalid inputs:

- `question` is not a non-empty string.
- `question` does not match the supported shape.
- `passages` is not a list.
- Any passage is not a dictionary.
- A passage has an invalid `id`, `text`, or `trusted` value.
