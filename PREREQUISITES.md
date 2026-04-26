# PREREQUISITES.md — Run this prompt FIRST if you don't already have Claude Code CLI

**Why this exists:** the [HANDOFF-PROMPT.md](HANDOFF-PROMPT.md) prompts assume you have **Claude Code CLI** (the `claude` command in a terminal) installed and authenticated. If you don't — or if you're not sure — paste the prompt below into your AI agent FIRST. It batches every install into a single elevated session so you see one permission prompt instead of many.

**Important disambiguation:**

- **Claude Code CLI** — a terminal command (`claude`) installed via npm. This is what the handoff prompts need.
- **Claude Code VS Code extension** — a chat panel inside VS Code. Different product. May or may not support all features the workspace expects (sub-agent dispatch in particular).

If you're reading this through the VS Code extension's chat panel, that's fine for running this prerequisites prompt — but you'll still need the CLI installed before the handoff prompt will work end-to-end.

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
3. Install Claude Code CLI specifically (this is separate from any
   VS Code extension; the handoff prompts I'll paste afterwards
   require the CLI, not the extension)
4. Verify I'm authenticated to Claude via my plan, NOT an
   ANTHROPIC_API_KEY env var
5. STOP. I'll paste the next prompt (the actual tool install) after
   you confirm prerequisites are good.

Important Windows quirks for verification:
- Don't use bare `code --version` to check VS Code — on Windows in
  bash/git-bash, `code` may resolve to a Node.js binary inside
  VS Code's bundled folder and return a Node version. Use
  `code.cmd --version` from PowerShell, or use `where.exe code` to
  see all candidates and pick the right one.
- Use `where.exe claude` to detect Claude Code CLI presence — bare
  `claude --version` will throw "command not recognized" if missing
  but won't tell you whether the issue is missing-binary vs not-on-PATH.
- Node.js is required for Claude Code CLI install (npm). If Node
  is missing, install it first.

Please follow this flow:

1. ENTER PLAN MODE FIRST. Run the version checks below and report
   what's installed. Don't install anything yet.

   Version checks (use PowerShell, not bash):
   - `git --version`
   - `node --version`
   - `npm --version`
   - `python --version` (and `py --version` as fallback)
   - `where.exe code` (NOT `code --version` — see quirks above)
   - `where.exe claude`

   Report: which of {git, node, python, vscode, claude-cli} is
   already installed and which is missing.

2. PROPOSE a batched install plan. The pattern I want is:
   - Use `winget install -e --id <id> --silent --accept-source-agreements --accept-package-agreements` for everything that has a winget package
   - Run all winget commands sequentially in ONE elevated PowerShell
     session (one UAC prompt total)
   - Then install Claude Code CLI via npm in a second non-elevated
     step (npm doesn't need admin)

   Things you may need to install (only if missing per step 1):
   - Git for Windows:    winget id  Git.Git
   - Node.js LTS:        winget id  OpenJS.NodeJS.LTS
   - Python 3.11:        winget id  Python.Python.3.11
   - VS Code:            winget id  Microsoft.VisualStudioCode

   Show me the full PowerShell command(s) you'd run. Don't run them
   yet.

3. WAIT for me to say "go". I'll review your plan and approve.

4. AFTER my "go", run the batched install. Tell me when each line
   completes. If UAC fires more than once, something's wrong with
   the batching — pause and tell me.

5. AFTER the system installs complete, install Claude Code CLI:
   `npm install -g @anthropic-ai/claude-code`

   Then in a FRESH terminal (so PATH refreshes):
   - `where.exe claude`  → should show a path
   - `claude --version`  → should print a version

6. AUTH CHECK. Run `claude` (or `claude /status` if it has that
   command) and tell me whether it's using:
   - My Claude plan login (good — what I want), OR
   - An ANTHROPIC_API_KEY env var (NOT what I want for these tools)

   If it's using the env var, run `Get-Item Env:\ANTHROPIC_API_KEY`
   to confirm, then suggest I unset it before proceeding:
   `Remove-Item Env:\ANTHROPIC_API_KEY` (current session)
   `[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $null, "User")` (persistent for me)

   If `claude login` is needed (because I haven't logged in yet),
   walk me through that — it opens a browser to authenticate.

7. STOP. Confirm: git ✅, node ✅, python ✅, code.cmd ✅, claude
   CLI ✅, plan auth ✅. I'll paste the next prompt (dashboard or
   workspace handoff) once you say "prerequisites complete".

Common Windows dialog you'll see (pre-warning so I don't panic):
- ONE UAC prompt at the start of the batched winget install
  ("Do you want to allow this app to make changes?") → click Yes
- SmartScreen on signed installers ("Windows protected your PC")
  → click "More info" → "Run anyway" if it's from python.org or
  code.visualstudio.com (winget signed sources usually skip this)
- "Allow Python through Windows Defender Firewall?" → click Allow
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
3. Install Claude Code CLI specifically (this is separate from any
   VS Code extension; the handoff prompts I'll paste afterwards
   require the CLI, not the extension)
4. Verify I'm authenticated to Claude via my plan, NOT an
   ANTHROPIC_API_KEY env var
5. STOP. I'll paste the next prompt (the actual tool install) after
   you confirm prerequisites are good.

Important disambiguation:
- "Claude Code CLI" (the `claude` command in Terminal) is a separate
  product from the "Claude" VS Code extension. The handoff prompts
  need the CLI. If I'm talking to you through the VS Code extension
  right now, that's fine for prep — but the actual tools require
  the CLI to be installed.

Please follow this flow:

1. ENTER PLAN MODE FIRST. Run version checks and report what's
   installed:
   - `git --version` (or note if it triggers the Xcode CLT install
     dialog)
   - `node --version` and `npm --version`
   - `python3 --version`
   - `which code` (VS Code's CLI helper, if installed)
   - `which claude`

   Report: which of {git, xcode-clt, node, python, vscode, claude-cli}
   is already installed and which is missing.

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
   - Node.js LTS — `brew install node` (or python.org-style installer)
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

5. AFTER the system installs complete, install Claude Code CLI:
   `npm install -g @anthropic-ai/claude-code`

   Then in a FRESH Terminal (so PATH refreshes):
   - `which claude` → should show a path
   - `claude --version` → should print a version

6. AUTH CHECK. Run `claude` and tell me whether it's using:
   - My Claude plan login (good — what I want), OR
   - An ANTHROPIC_API_KEY env var (NOT what I want for these tools)

   If env var is set, suggest I unset it:
   `unset ANTHROPIC_API_KEY` (current session)
   Edit ~/.zshrc or ~/.bash_profile to remove the persistent setting
   if it's there.

   If `claude login` is needed, walk me through that — it opens a
   browser to authenticate.

7. STOP. Confirm: git ✅, node ✅, python3 ✅, code (VS Code) ✅,
   claude CLI ✅, plan auth ✅. I'll paste the next prompt once you
   say "prerequisites complete".

Don't run anything until I say "go" after step 2's plan.
```

---

## What "prerequisites complete" looks like

Before pasting the dashboard or workspace handoff prompt, your agent should have confirmed all six:

- [ ] `git --version` returns a real version
- [ ] `node --version` and `npm --version` both work (Claude Code CLI needs npm)
- [ ] `python --version` (Windows) or `python3 --version` (Mac) returns 3.11+
- [ ] `code.cmd --version` (Windows) or `which code` (Mac) returns a real VS Code path
- [ ] `where.exe claude` (Windows) or `which claude` (Mac) returns a real path — Claude Code CLI is installed
- [ ] `claude` runs without prompting for an API key — auth is via plan login, not `ANTHROPIC_API_KEY`

Once all six are green, paste the [HANDOFF-PROMPT.md](HANDOFF-PROMPT.md) variant matching your OS and proceed.

## If you already have Claude Code CLI installed and working

You can skip this PREREQUISITES file entirely and go straight to [HANDOFF-PROMPT.md](HANDOFF-PROMPT.md). The handoff prompt itself will check the prerequisites quickly at the start; if anything's missing it'll tell you, and you can come back here.
