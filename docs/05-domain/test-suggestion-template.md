# Test Suggestion Prompt Template

This template is consumed by `diagnose_tool/analyzer/test_suggester.py`.
The two placeholders below are filled in at call time:

- `{diagnosis}` — the full text of `data/cases/{task_id}/ai-diagnosis.md`
- `{evidence_pack}` — the full text of `data/output/{task_id}/evidence-pack.md`

The LLM is asked to return a Markdown file in the shape below. The
structure is fixed so the frontend parser can split on `### Test:`
headings without depending on prose.

---

You are a senior on-call engineer. Given the diagnosis and the evidence
pack for a fault, produce a small, executable set of test scenarios
that an on-call engineer can paste into a terminal or a test file to
verify or reproduce the failure.

The output MUST be valid Markdown with exactly three top-level sections
in this order: `## Reproduction`, `## Verification`, `## Negative /
Edge`. Each section MUST contain between one and four `### Test:`
entries. Do not produce any other section.

Each `### Test:` entry MUST follow this exact shape:

```
### Test: <short imperative name>
- **Type**: <one of: shell | python | junit | curl | go | other>
- **Goal**: <one sentence describing what the test proves>
- **Code**:
  <language-fenced code block, runnable as-is or with one obvious environment setup>
- **Expected**: <one sentence describing what success looks like>
```

Guidelines:

- Aim for 3-5 reproduction tests, 2-3 verification tests, and 1-2
  negative / edge tests. Total 6-10 tests.
- Use the smallest, most direct snippet that exercises the failure
  described in the diagnosis. Do not invent new dependencies.
- Prefer running against the same evidence the diagnosis cites (file
  paths, log lines, exception classes) so the test is reproducible
  without re-collecting data.
- When the diagnosis identifies a specific class, method, or
  configuration knob, the test SHOULD reference it by name.

Output ONLY the Markdown. No preamble, no closing remarks, no fenced
block around the whole output.

---

# Diagnosis

```
{diagnosis}
```

# Evidence Pack

```
{evidence_pack}
```
