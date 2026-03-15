---
description: "Run all tests and report results"
agent: "agent"
tools: [execute, read]
---

Run the full pytest test suite for the work-notes project and report results:

```powershell
python -m pytest tests/ -v
```

Summarize: total tests, passed, failed, and any failure details.
