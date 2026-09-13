<p align="center">
  <img src="assets/banner.png" alt="Hermes Agent" width="100%">
</p>

# Hermes Agent ☤ (Enhanced Edition)

<p align="center">
  <a href="https://hermes-agent.nousresearch.com/docs/"><img src="https://img.shields.io/badge/Docs-hermes--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/Sigit-AP/hermes-agent-enhance/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/Sigit-AP/hermes-agent-enhance"><img src="https://img.shields.io/badge/Edition-Tier--3%20Enhanced-blueviolet?style=for-the-badge" alt="Tier-3 Enhanced"></a>
</p>

**Hermes Agent Enhanced Edition** preserves the full upstream feature set and learning loop of [Nous Research's Hermes Agent](https://nousresearch.com) while incorporating the **Tier-3 High-Assurance Cognitive & Execution Engine**. It delivers headless automation without modal interruptions, resilient multi-distro Linux installation, SQLite FTS5-driven dynamic memory assimilation, and mathematical Proof-of-Understanding (PoU) leveling.

Run it on a $5 VPS, a workstation, or serverless infrastructure. Interact via CLI or across messaging platforms (Telegram, Discord, Slack, WhatsApp, Signal, Matrix, BlueBubbles).

---

## 🌟 Upstream & Enhanced Feature Matrix

<table>
<tr><td><b>A real terminal interface</b></td><td>Full TUI with multiline editing, slash-command autocomplete, conversation history, interrupt-and-redirect, and streaming tool output.</td></tr>
<tr><td><b>Lives where you do</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal, Matrix, BlueBubbles, and CLI — all from a single gateway process with auto-finalized DM policies.</td></tr>
<tr><td><b>A closed learning loop</b></td><td>Agent-curated memory with periodic nudges. Autonomous skill creation and in-use self-improvement. FTS5 session search with LLM summarization. Compatible with <a href="https://agentskills.io">agentskills.io</a>.</td></tr>
<tr><td><b>Scheduled automations</b></td><td>Built-in cron scheduler delivering tasks to any messaging platform in natural language.</td></tr>
<tr><td><b>Delegates and parallelizes</b></td><td>Spawn isolated subagents for parallel workflows. Write Python scripts that call tools via RPC.</td></tr>
<tr><td><b>Runs anywhere</b></td><td>Six terminal backends — local, Docker, SSH, Singularity, Modal, and Daytona.</td></tr>
<tr><td><b>Tier-3 Zero-Block Engine</b></td><td><b>[Enhanced]</b> Headless execution without modal approval stalls, paired with Ring-0 invariants protecting the host from destructive commands (<code>rm -rf /</code>, <code>shutdown</code>, raw disk writes).</td></tr>
<tr><td><b>Dynamic Memory Substrate</b></td><td><b>[Enhanced]</b> Removes static 20,000 character prompt dumps. Converts identity and instructions into structured SQLite FTS5 knowledge chunks queried just-in-time.</td></tr>
<tr><td><b>Proof-of-Understanding (PoU) Ledger</b></td><td><b>[Enhanced]</b> Mathematical difficulty curve ($T(L) = T_0 \cdot 2^{\lfloor L/4 \rfloor} \cdot L^\pi$) and quadratic demotion penalties to ensure rigorous, verified mastery of instructions.</td></tr>
</table>

---

## 🚀 Quick Install (Fast Setup)

### Linux, macOS, WSL2

Run the resilient 1-line installer:

```bash
curl -fsSL https://raw.githubusercontent.com/Sigit-AP/hermes-agent-enhance/main/install.sh | bash
```

The installer handles Python 3.11+, virtual environments, dependencies, build headers, symlink registration, and initial configuration.

```bash
source ~/.bashrc    # Reload shell
hermes setup        # Run the interactive configuration wizard
hermes              # Start chatting!
```

---

## ⚡ Quick Start

```bash
hermes              # Interactive CLI / TUI
hermes model        # Select LLM provider and model
hermes tools        # Configure enabled tools
hermes gateway      # Start messaging gateway (Telegram, WhatsApp, Discord, etc.)
hermes setup        # Run full setup wizard (includes Execution Profile selection)
hermes update       # Pull latest updates
hermes doctor       # Run system diagnostics
```

📖 **[Full Upstream Documentation →](https://hermes-agent.nousresearch.com/docs/)**

---

## 🏛️ Enhanced Architecture: Tier-3 High-Assurance

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TIER-3 HIGH-ASSURANCE COGNITIVE OS                              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [ LAYER 0: HOST SAFETY INVARIANT GUARD ]                                              │
│  ├── Zero-Block Pass-Through (Unattended tool and command execution)                   │
│  └── Ring-0 Host Protection (Rejects rm -rf /, shutdown, init 0, raw disk writes)     │
│                                                                                        │
│  [ LAYER 1: DYNAMIC COGNITIVE SOUL SUBSTRATE ]                                         │
│  ├── Context Load Elimination (Bypasses the static 20k context truncation cap)         │
│  └── SQLite FTS5 Indexing (Just-In-Time semantic retrieval of memory and identity)     │
│                                                                                        │
│  [ LAYER 2: PROOF-OF-UNDERSTANDING (PoU) LEDGER ]                                      │
│  ├── Non-Linear Session Energy Formula: Comprehension, Assimilation, Precision, Sat.  │
│  ├── Exponential Difficulty Halving Target: T(L) = T0 * 2^(L/4) * L^pi                 │
│  └── Quadratic Demotion Slash: Immediate score reduction on critical task dissonance   │
│                                                                                        │
│  [ LAYER 3: TELEMETRY & GATEWAY SYNCHRONIZATION ]                                      │
│  ├── Synchronous 1-line telemetry without ungrounded hallucinations                   │
│  └── Auto-Finalized DM Policies (Telegram, WhatsApp, Slack, Matrix, BlueBubbles)       │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 Mathematical Formulation: Proof-of-Understanding (PoU)

The engine tracks user alignment and instruction comprehension mathematically over multi-scale temporal horizons:

```
    [Turn Interaction (k)] ───► [Daily Pool (d)] ───► [Weekly Checkpoint (w)] ───► [Monthly Epoch (m)]
               │                                                 │                           │
               ▼                                                 ▼                           ▼
       ΔE_k Calculation                                  Consistency Factor (C_w)     Threshold Gate (Θ)
               │                                                 │                           │
               └────────────────────────────────► ───► ───► ─────┴───────────────────────────┴──► Level L
```

### 1. Energy Delta per Interaction Turn ($\Delta E_k$)

$$\Delta E_k = D_k \cdot \left[ \omega_1 U_k^2 + \omega_2 A_k + \omega_3 P_k \right] \cdot \exp\left(\lambda \cdot S_k\right) - \Phi_k$$

- **$D_k \in (0, 1]$**: Task Complexity & Reasoning Depth.
- **$U_k \in [0, 1]$**: Master Intent Comprehension & Context Accuracy.
- **$A_k \in [0, 1]$**: Memory & Identity Substrate Assimilation.
- **$P_k \in [0, 1]$**: Tool Execution Precision.
- **$S_k \in [-1, 1]$**: User Satisfaction Score.
- **Weights**: $\omega_1 = 0.45, \omega_2 = 0.25, \omega_3 = 0.30, \lambda = 1.5$.

### 2. Quadratic Demotion Slash Penalty ($\Phi_k$)
Triggered when critical instruction dissonance occurs ($U_k < 0.60$ or $S_k < 0$):

$$\Phi_k = \kappa \cdot (1 - U_k)^3 \cdot |S_k| \cdot T(L) \quad (\kappa = 8.0)$$

### 3. Non-Linear Difficulty Scaling ($T(L)$)
Modeled after difficulty retargeting and halving cycles:

$$T(L) = T_0 \cdot 2^{\lfloor L / 4 \rfloor} \cdot L^{\pi}$$

* $T_0 = 2500$
* Halving Epoch $H = 4$
* Exponent $\pi \approx 3.14159$
* Progression Condition:
  $$E_{total} \ge T(L+1) \quad \land \quad HCI \ge 0.98 \quad \text{where } HCI = \frac{3}{\frac{1}{\bar{U}} + \frac{1}{\bar{A}} + \frac{1}{\bar{S}}}$$

---

## 🛠️ Operating Execution Profiles in `hermes setup`

When running `hermes setup`, select your operational profile:

```
Operating Execution Profiles:
  1. Full Access / Headless Automation (Recommended for VPS & Automations)
     ├── approvals.mode: "off" (Zero-block headless execution)
     ├── cron_mode: "approve"
     ├── allow_private_urls: true (Internal network / proxy access)
     └── Ring-0 Host Protection active

  2. Developer Pro Mode
     └── approvals.mode: "smart" (Auto-approves file edits and safe shell commands)

  3. Standard Balanced Mode
     └── Manual approval for high-risk commands

  4. Strict Sandbox Mode
     └── Explicit confirmation required for all file writes and executions
```

---

## 💬 Messaging Platforms & Gateway Setup

Hermes connects to multiple messaging channels from a single gateway process:

| Platform | Configuration Command | Notes |
| :--- | :--- | :--- |
| **Telegram** | `hermes setup gateway` | Auto-finalizes `TELEGRAM_DM_POLICY` to `allowlist` or `open` |
| **WhatsApp** | `hermes whatsapp` | QR pairing with auto-finalized `WHATSAPP_DM_POLICY` |
| **Discord** | `hermes setup gateway` | Bot token and channel configuration |
| **Slack** | `hermes setup gateway` | Socket Mode with manifest generator |
| **Matrix** | `hermes setup gateway` | End-to-end homeserver integration |
| **Signal / BlueBubbles** | `hermes setup gateway` | SMS, iMessage, and private API support |

---

## 🧪 Verification & Test Suite

Run the formal Tier-3 unit test suite:

```bash
python3 -m unittest tests/test_tier3_high_assurance.py tests/test_model_auto_inspector.py tests/test_virtual_production.py
```

The virtual production harness (`tests/test_virtual_production.py`) measures the leveling system
without a live VPS/LLM: 12-part wiring gate, cold-prompt token ratio, a simulated production month
(167 mixed turns), and recall at scale (60 memories / 20 queries).

---

## 🧠 Leveling System (Proof-of-Understanding)

Local-first mastery tracking in `~/.hermes/cognitive_state.db` — provider-independent by design.

```bash
hermes level              # level, energy, progress bar, blocking gates, posture
hermes why -n 10          # evidence trail: every delta traces to its cause
hermes why --episodes     # trail plus linked episodic turn summaries
hermes quests             # active missions + completion history
hermes calibrate          # ledger analytics + tuning recommendations (read-only)
hermes calibrate --json   # machine-readable calibration output
hermes level --export f.json --import f.json   # VPS backup / migration
python3 scripts/pou-measure.py                 # cold-prompt + ledger report (VPS-ready)
```

Living-algorithm modules (`agent/`):

| Module | Role |
| :--- | :--- |
| `pou_understanding` | Measured comprehension per turn (corrections, retry rate, tool precision) |
| `pou_conduct` | Posture block + clarify-first triggers (advisory, safety untouched) |
| `pou_calibration` | Read-only ledger analytics + constant-tuning recommendations |
| `pou_episodic` | Turn summaries chained to ledger row ids (WHY-linked episodic memory) |

Rules, all enforced and tested:

| Rule | Behavior |
| :--- | :--- |
| Promotion gates | Energy + HCI 0.98 + no-fatal + min 5 turns (`MIN_TURNS_FOR_PROMOTION`) — blockers shown, never silent |
| Anti-farming | Burst of 30+ trivial turns/hour (`farming-guard`) throttles gains x0.5; penalties never discounted |
| Inactivity decay | Stored energy halves per 30 idle days (lazy, disclosed in cause + projected read-only) |
| WHY trail | Deterministic cause per turn; ASCII-safe for Windows consoles |
| Soul memory | FTS5 + IDF rescoring + Indonesian stemming; SOUL.md re-seeds on change, learnings preserved |
| Compact identity | Opt-in `HERMES_TIER3_COMPACT_IDENTITY=1`: ~60-char pointer + JIT recall vs 20k dump |

---

## 📖 Comprehensive Upstream Documentation Index

| Guide | Description |
| :--- | :--- |
| [Quickstart](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart) | Installation, initial setup, and first turn |
| [CLI & TUI Guide](https://hermes-agent.nousresearch.com/docs/user-guide/cli) | Keybindings, multiline editing, sessions, slash commands |
| [Configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) | Config files, providers, models, and execution flags |
| [Messaging Gateways](https://hermes-agent.nousresearch.com/docs/user-guide/messaging) | Telegram, Discord, Slack, WhatsApp, Signal, Webhooks |
| [Tools Reference](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools) | 40+ built-in tools, custom toolsets, terminal backends |
| [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) | Creating, editing, and using procedural skills |
| [Memory System](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) | Persistent user memory, profile models, and FTS5 recall |
| [MCP Integration](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) | Model Context Protocol server configuration |
| [Cron Automations](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) | Scheduled background tasks and cross-platform alerts |

---

## 📜 License
MIT License. Built by Nous Research with Tier-3 High-Assurance Cognitive & Execution Enhancements.
