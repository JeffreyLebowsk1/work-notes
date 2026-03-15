# Security Policy

## Supported Versions

This repository is a living knowledge base, not a versioned software release. The **current state of the `main` branch** is the only supported version. Older commits are not maintained.

| Component | Supported |
| --------- | --------- |
| `main` branch (latest) | ✅ |
| Any previous commit / snapshot | ❌ |

---

## Preventive Controls

This repository uses [ggshield](https://github.com/GitGuardian/ggshield) (GitGuardian's CLI) as a **pre-commit hook** to automatically block commits that contain secrets such as API keys, passwords, or tokens. Setup instructions are in [`SETUP.md`](SETUP.md#-secret-scanning-with-gitguardian-ggshield). The hook configuration lives in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

---

## Data Privacy & FERPA Notice

This repository stores **work procedures, policies, meeting notes, and coordination materials** for the Registrar's Office at Central Carolina Community College. It must **never** contain:

- Student personally identifiable information (PII): names, student IDs, SSNs, grades, enrollment status, or any other education records protected under [FERPA (20 U.S.C. § 1232g)](https://www.law.cornell.edu/uscode/text/20/1232g)
- Employee personal information (home addresses, SSNs, personal contact details)
- Credentials, API keys, or passwords of any kind

If you discover that this repository contains any of the above, please report it immediately using the process below.

For full data-handling guidelines, see [`personal-data/handling-guidelines.md`](personal-data/handling-guidelines.md) and [`personal-data/ferpa-reference.md`](personal-data/ferpa-reference.md).

---

## Reporting a Vulnerability

If you find a security vulnerability — including accidental exposure of student/employee PII, an exposed credential, or a security flaw in the web app tools (`tools/app.py`, `tools/ai_providers.py`, etc.) — please report it **privately** rather than opening a public issue.

### How to report

1. **GitHub Private Vulnerability Reporting** *(preferred)*  
   Use GitHub's built-in [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) for this repository. This keeps the details confidential until the issue is resolved.

2. **Direct contact**  
   If you are unable to use the above channel, contact the repository owner directly through GitHub.

### What to include in your report

- A clear description of the vulnerability or data exposure
- The file(s) or commit(s) involved
- Steps to reproduce (for web app vulnerabilities)
- Potential impact

### What to expect

- **Acknowledgement** within 2 business days
- **Assessment and triage** within 5 business days
- **Resolution** (fix or data removal + history rewrite if PII was committed) as quickly as possible, prioritized by severity

Reported vulnerabilities that are confirmed will be addressed promptly. If a report is determined to be out of scope or not a vulnerability, you will receive an explanation.
