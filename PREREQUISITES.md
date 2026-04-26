# PREREQUISITES.md — Run this prompt FIRST if you need to install dev tools

**Why this exists:** the [HANDOFF-PROMPT.md](HANDOFF-PROMPT.md) prompts assume you have **Git**, **Python 3.11+**, and **VS Code** installed, plus a Claude AI agent set up in VS Code (either the Claude Code CLI in a terminal OR the Claude VS Code extension chat panel — both work). If you don't have those, paste the prompt below into your AI agent FIRST. It batches every install into a single elevated session so you see one permission prompt instead of many.

**On Claude Code CLI vs the VS Code extension:** for these install prompts, **either works**. The VS Code extension can clone repos, run terminal commands, edit files, and launch processes — that's all that's needed. The CLI is only worth installing if you specifically want to use it.

---

## Pick the variant matching your OS

### Windows variant — paste this into your agent

```
I'm about to install some FX research tools and I want to set up
permissions + prerequisites FIRST so the actual install runs with
minimum interruption. I'm on Windows 11. I'm AI-fluent but not a
developer — you handle setup, I approve major actions.

THE GOAL of this prep step:
1. Check what's already installed
2. Install anything missing in ONE batched elevated PowerShell session
   (so I see ONE UAC prompt instead of N — minimize popup fatigue)
3. Verify I'm authenticated to Claude via my plan, NOT an
   ANTHROPIC_API_KEY env var
4. STOP. I'll paste the next prompt (the actual tool install) after
   you confirm prerequisites are good.

Important Windows quirks for verification:
- Don't use bare `code --version` to check VS Code — on Windows in
  bash/git-bash, `code` may resolve to a Node.js binary inside
  VS Code's bundled folder and return a Node version. Use
  `code.cmd --version` from PowerShell, or use `where.exe code` to
  see all candidates and pick the right one.

Please follow this flow:

1. ENTER PLAN MODE FIRST. Run the version checks below and report
   what's installed. Don't install anything yet.

   Version checks (use PowerShell, not bash):
   - `git --version`
   - `python --version` (and `py --version` as fallback)
   - `where.exe code` (NOT `code --version` — see quirks above)

   Report: which of {git, python, vscode} is already installed and
   which is missing.

2. PROPOSE a batched install plan. The pattern I want is:
   - Use `winget install -e --id <id> --silent --accept-package-agreements --accept-source-agreements`
     for everything that has a winget package
   - Run all winget commands sequentially in ONE elevated PowerShell
     session (one UAC prompt total)

   Things you may need to install (only if missing per step 1):
   - Git for Windows:    winget id  Git.Git
   - Python 3.11:        winget id  Python.Python.3.11
   - VS Code:            winget id  Microsoft.VisualStudioCode

   Show me the full PowerShell command(s) you'd run. Don't run them
   yet.

3. WAIT for me to say "go". I'll review your plan and approve.

4. AFTER my "go", run the batched install. Tell me when each line
   completes. If UAC fires more than once, something's wrong with
   the batching — pause and tell me.

5. AUTH CHECK. Tell me whether I'm using:
   - My Claude plan login (good — what I want), OR
   - An ANTHROPIC_API_KEY env var (NOT what I want for these tools)

   If env var is set, run `Get-Item Env:\ANTHROPIC_API_KEY` to
   confirm, then suggest I unset it before proceeding:
   `Remove-Item Env:\ANTHROPIC_API_KEY`
   `[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $null, "User")`

6. STOP. Confirm: git OK, python OK, code.cmd OK, plan auth OK.
   I'll paste the next prompt (dashboard or workspace handoff) once
   you say "prerequisites complete".

(Optional — only if I ask: install the Claude Code CLI via
`npm install -g @anthropic-ai/claude-code` in a non-elevated
PowerShell after Node.js is installed via
`winget install -e --id OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements`.
But the install prompts work fine through whichever Claude agent
I'm already using — including the VS Code extension chat panel —
so don't push this on me.)

Common Windows dialog you'll see (pre-warning so I don't panic):
- ONE UAC prompt at the start of the batched winget install
  ("Do you want to allow this app to make changes?") -> click Yes
- SmartScreen on signed installers ("Windows protected your PC")
  -> click "More info" -> "Run anyway" if it's from python.org or
  code.visualstudio.com (winget signed sources usually skip this)
- "Allow Python through Windows Defender Firewall?" -> click Allow
- I will NEVER need to type my password into a terminal. If a step
  asks for that, stop and tell me.

Don't run anything until I say "go" after step 2's plan.
```

### Mac variant — paste this into your agent

```
I'm about to install some FX research tools and I want to set up
permissions + prerequisites FIRST so the actual install runs with
minimum interruption. I'm on macOS. I'm AI-fluent but not a
developer — you handle setup, I approve major actions.

THE GOAL of this prep step:
1. Check what's already installed
2. Install anything missing — using GUI password dialogs (the lock
   icon), NEVER terminal sudo
3. Verify I'm authenticated to Claude via my plan, NOT an
   ANTHROPIC_API_KEY env var
4. STOP. I'll paste the next prompt (the actual tool install) after
   you confirm prerequisites are good.

Please follow this flow:

1. ENTER PLAN MODE FIRST. Run version checks and report what's
   installed:
   - `git --version` (or note if it triggers the Xcode CLT install
     dialog)
   - `python3 --version`
   - `which code` (VS Code's CLI helper, if installed)

   Report: which of {git, xcode-clt, python, vscode} is already
   installed and which is missing.

2. PROPOSE an install plan that PREFERS GUI dialogs over terminal
   sudo. Captured rule from prior user research: typing a password
   into a black terminal window is uncomfortable; the GUI lock-icon
   dialog feels safe. Same security, very different feel.

   Things you may need to install (only if missing per step 1):
   - Xcode command-line tools — triggered automatically by first
     `git` command (system dialog: "The git command requires the
     command line developer tools — install?")
   - Homebrew — one-time bootstrap (uses GUI dialog when prompting
     for sudo). After that, `brew install` is much smoother.
   - Python 3.11 — prefer the official .pkg installer from
     python.org (uses Apple's GUI password dialog with lock icon)
     over `brew install python@3.11`
   - VS Code — `brew install --cask visual-studio-code` OR drag-to-
     Applications from code.visualstudio.com

   Show me the full plan. Don't run anything yet.

3. WAIT for me to say "go". I'll review your plan and approve.

4. AFTER my "go", run the installs. For each one that triggers a
   macOS popup, pre-warn me with what's about to appear and what to
   click. Common ones:
   - "The git command requires the command line developer tools —
     install?" → Click Install. Takes ~5 min.
   - "Python.pkg is from an unidentified developer — open?" →
     Right-click the .pkg → Open if Gatekeeper blocks the standard
     double-click.
   - "Terminal would like to access files in your Documents folder"
     → OK / Allow.
   - macOS asking for my password during install → ALWAYS use the
     Apple GUI password dialog (lock icon). NEVER terminal.

5. AUTH CHECK. Tell me whether I'm using:
   - My Claude plan login (good — what I want), OR
   - An ANTHROPIC_API_KEY env var (NOT what I want for these tools)

   If env var is set, suggest I unset it:
   `unset ANTHROPIC_API_KEY` (current session)
   Edit ~/.zshrc or ~/.bash_profile to remove the persistent setting
   if it's there.

6. STOP. Confirm: git OK, python3 OK, code (VS Code) OK, plan auth
   OK. I'll paste the next prompt once you say "prerequisites
   complete".

(Optional — only if I ask: install the Claude Code CLI via
`npm install -g @anthropic-ai/claude-code` after Node.js is
installed via `brew install node`. But the install prompts work
fine through whichever Claude agent I'm already using — including
the VS Code extension chat panel — so don't push this on me.)

Don't run anything until I say "go" after step 2's plan.
```

---

## What "prerequisites complete" looks like

Before pasting the dashboard or workspace handoff prompt, your agent should have confirmed:

- [ ] `git --version` returns a real version
- [ ] `python --version` (Windows) or `python3 --version` (Mac) returns 3.11+
- [ ] `code.cmd --version` (Windows) or `which code` (Mac) returns a real VS Code path
- [ ] You're authenticated to Claude via plan login, not via `ANTHROPIC_API_KEY`

Once those four are green, paste the [HANDOFF-PROMPT.md](HANDOFF-PROMPT.md) variant matching your OS.

## If you already have those four installed

Skip this PREREQUISITES file. Go straight to [HANDOFF-PROMPT.md](HANDOFF-PROMPT.md) — the handoff prompt itself checks prerequisites at the start, and if anything's missing it'll tell you to come back here.
