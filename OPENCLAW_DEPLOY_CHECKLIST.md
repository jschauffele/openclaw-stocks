# OpenClaw Deploy Checklist

Use this checklist for small OpenClaw hotfixes and normal deployments.

## Rules

- Mac is the development machine.
- GitHub `main` is the source-control truth.
- VPS is the runtime environment.
- Do not assume Mac, GitHub, and VPS match without checking.
- Do not run `python3 main.py` on the VPS.
- Prefer clean git deploys on the VPS.
- If the local repo is dirty with unrelated work, use a clean clone for hotfixes.

## 1. Confirm You Are On The Right Machine

On Mac:

```bash
hostname && pwd
```

On VPS:

```bash
hostname && pwd
```

## 2. Check Local Repo State On Mac

```bash
cd /Users/openclawcontrol/Documents/openclaw-stocks && git status --short
```

If the repo contains unrelated refactor work, use a clean clone:

```bash
cd /Users/openclawcontrol/Documents && rm -rf openclaw-stocks-hotfix && git clone https://github.com/DickMcGreggor/openclaw-stocks.git openclaw-stocks-hotfix
```

## 3. Make The Smallest Fix Locally

Work in the correct repo, test locally, then commit only the intended fix.

```bash
cd /Users/openclawcontrol/Documents/openclaw-stocks-hotfix && git checkout -b codex/short-hotfix-name
git status --short
git add <file>
git commit -m "Short clear message"
git push -u origin codex/short-hotfix-name
```

## 4. Merge The Hotfix Into GitHub Main

```bash
cd /Users/openclawcontrol/Documents/openclaw-stocks-hotfix && git checkout main
git pull origin main
git merge --ff-only codex/short-hotfix-name
git push origin main
```

## 5. Update The VPS From GitHub

Before any VPS deploy, fetch, pull, merge, restore, or `scp` write, verify the
VPS root filesystem is mounted read-write. If the filesystem is read-only or
the result is ambiguous, stop and report the ambiguity. Do not retry sync,
restore, or copy operations until the filesystem state is resolved.

When `CODEX_VPS` and a direct VPS terminal disagree about filesystem state, the
direct VPS terminal is authoritative for deploy decisions.

Use the VPS git checkout now that SSH deploy access is configured:

```bash
cd /opt/openclaw-stocks && git fetch origin
git merge --ff-only origin/main
```

## 6. Run The Bot Manually On The VPS

Use the wrapper script so the virtual environment is loaded:

```bash
cd /opt/openclaw-stocks && ./run_bot.sh
```

Do not use:

```bash
cd /opt/openclaw-stocks && python3 main.py
```

## 7. Verify The Latest Result

Starting or restarting `openclaw.timer` may immediately trigger a natural
systemd run. After starting the timer, wait for `openclaw.service` to settle
back to inactive before classifying runtime behavior.

Inspect both `last_run_report.json` and the latest `logs/*.jsonl` before
deciding whether the run was expected timer behavior or unexpected runtime
drift.

```bash
cd /opt/openclaw-stocks && tail -n 50 last_run_report.json
```

## 8. Verify VPS Repo Is Clean

```bash
cd /opt/openclaw-stocks && git status -sb
```

Expected result after a normal deploy:

```bash
## main...origin/main
```

## 9. If You Must Copy A Single File

Prefer `scp` from Mac to VPS over manual paste into `nano`:

```bash
scp /Users/openclawcontrol/Documents/openclaw-stocks-hotfix/<file> root@146.190.54.10:/opt/openclaw-stocks/
```

Then verify on the VPS:

```bash
cd /opt/openclaw-stocks && git diff -- <file>
```

If the file should match GitHub `main`, finish with:

```bash
cd /opt/openclaw-stocks && git restore --source=origin/main --worktree --staged <file>
```

## 10. Nano

If `nano` opens:

- Save: `Ctrl+O`, then `Enter`
- Exit: `Ctrl+X`
