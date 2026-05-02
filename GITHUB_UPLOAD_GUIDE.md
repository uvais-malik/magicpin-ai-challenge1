# GitHub Upload Guide

## What To Commit

Commit the project source files and deployment helpers:

- `app/`
- `config/`
- `core/`
- `intelligence/`
- `rules/`
- `templates/`
- `tests/`
- `utils/`
- `bot.py`
- `README.md`
- `requirements.txt`
- `Procfile`
- `Dockerfile`
- `.env.example`
- `.gitignore`
- `judge_simulator.py`

## What Not To Commit

Do not commit:

- `.env`
- real API keys
- `__pycache__/`
- `*.pyc`
- `*.zip`
- local logs

## Local Run

```bash
python bot.py
```

Health check:

```bash
curl http://localhost:8080/v1/healthz
```

## Judge Simulator With Env Vars

PowerShell:

```powershell
$env:BOT_URL="http://localhost:8080"
$env:LLM_PROVIDER="gemini"
$env:LLM_API_KEY="your_key_here"
$env:LLM_MODEL="gemini-2.5-flash"
$env:TEST_SCENARIO="full_evaluation"
python judge_simulator.py
```

Do not paste the key into `judge_simulator.py`.

## Deploy

Render/Railway settings:

- Build command: `pip install -r requirements.txt`
- Start command: `python bot.py`
- Port: provided automatically through `PORT`

Submit the deployed base URL, for example:

```text
https://your-vera-bot.onrender.com
```

