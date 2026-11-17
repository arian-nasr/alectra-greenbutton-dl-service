# Alectra GreenButton downloader

Downloads GreenButton XML usage data from the Alectra portal every four hours,
parses it, and stores it in SQLite. The scripted Playwright flow is attempted
first; if the portal markup changes, an LLM-guided [Browser Use](https://docs.browser-use.com/open-source/introduction)
flow takes over.

## Setup

```
pip install -r requirements.txt
playwright install chromium
```

Before starting the service, verify that your OpenRouter model supports tool
calling (Browser Use depends on it):

```
python scripts/smoke_test_model.py
```

## Environment

Secrets go in `.env` (gitignored).

| Variable | Default | Purpose |
| --- | --- | --- |
| `ALECTRA_ACCOUNT_NAME` | required | Portal account name |
| `ALECTRA_ACCOUNT_NUMBER` | required | Portal account number |
| `ALECTRA_ACCOUNT_PHONE` | required | Portal phone number |
| `OPENROUTER_API_KEY` | required when fallback enabled | OpenRouter key |
| `OPENROUTER_MODEL` | `openai/gpt-oss-20b` | Model used by the agent |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenAI-compatible endpoint |
| `LLM_FALLBACK_ENABLED` | `true` | Set `false` to disable the agent entirely |
| `ALERT_WEBHOOK_URL` | unset | Slack/Discord-compatible webhook for blockages |
| `AGENT_MAX_STEPS` | `12` | Model requests per agent step |
| `AGENT_TIMEOUT_S` | `300` | Timeout per agent step |
| `AGENT_USE_VISION` | `false` | If true, screenshots reach the model (may include field values) |
| `AGENT_JUDGE_ENABLED` | `true` | Judge pass; also detects CAPTCHAs/bot blocks |
| `BROWSER_HEADLESS` | `true` | Headless Chromium |
| `BROWSER_USER_DATA_DIR` | unset | Optional persistent browser profile (reuses logins) |
| `USAGE_DB_PATH` | `./usage_data.db` | SQLite path |
| `ARTIFACTS_DIR` | `./artifacts` | Failure traces (gitignored) |
| `CYCLE_INTERVAL_S` | `14400` | Seconds between cycles |

## Safety behaviour

Credentials are passed via Browser Use `sensitive_data`, so the model only sees
placeholder names. The agent is forbidden from solving CAPTCHAs or retrying
locked accounts; those cases raise `HumanInterventionRequired`, write a trace
to `artifacts/<timestamp>/`, send a webhook alert (if configured), and pause
the scheduler with backoff.
