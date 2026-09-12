<p align="center">
  <img src="assets/banner.png" alt="Hermes Agent" width="100%">
</p>

# Hermes Agent (Enhanced Edition) ☤

<p align="center">
  <a href="https://github.com/Sigit-AP/hermes-agent-enhance"><img src="https://img.shields.io/badge/Release-Enhanced-blue?style=for-the-badge" alt="Release"></a>
  <a href="https://github.com/Sigit-AP/hermes-agent-enhance/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
</p>

Hermes Agent with enhanced execution and memory modules:
- Zero-block execution engine with host crash protection.
- Dynamic cognitive memory retrieval via SQLite FTS5.
- Structured proof-of-understanding leveling metrics.
- Synchronized gateway configuration.

---

## Installation

### Linux, macOS, WSL2

```bash
curl -fsSL https://raw.githubusercontent.com/Sigit-AP/hermes-agent-enhance/main/install.sh | bash
```

After installation:
```bash
hermes setup
hermes
```

---

## Architecture Overview

```
Layer 0: Host Safety Invariant Guard
├── Unconditional headless execution
└── Rejection of destructive host commands (rm -rf /, shutdown, raw disk writes)

Layer 1: Dynamic Soul Memory Substrate
├── Incremental episodic-to-semantic memory distillation
└── Query-time retrieval from SQLite FTS5 database

Layer 2: Proof-of-Understanding (PoU) Ledger
├── Multi-scale metrics (Comprehension, Soul Assimilation, Precision, Satisfaction)
└── Difficulty target progression: T(L) = T0 * 2^(L/4) * L^pi

Layer 3: Telemetry & Gateway Sync
└── Fully synchronized DM policies across Telegram, WhatsApp, Slack, Matrix, and BlueBubbles
```

---

## Mathematical Formulation: Proof-of-Understanding (PoU)

### Energy Delta per Turn ($\Delta E_k$)

$$\Delta E_k = D_k \cdot \left[ \omega_1 U_k^2 + \omega_2 A_k + \omega_3 P_k \right] \cdot \exp\left(\lambda \cdot S_k\right) - \Phi_k$$

- **$D_k$**: Task Complexity $[0, 1]$
- **$U_k$**: Comprehension Accuracy $[0, 1]$
- **$A_k$**: Memory Assimilation $[0, 1]$
- **$P_k$**: Tool Execution Precision $[0, 1]$
- **$S_k$**: User Satisfaction Score $[-1, 1]$
- **Weights**: $\omega_1 = 0.45, \omega_2 = 0.25, \omega_3 = 0.30, \lambda = 1.5$

### Demotion Penalty ($\Phi_k$)

$$\Phi_k = \kappa \cdot (1 - U_k)^3 \cdot |S_k| \cdot T(L) \quad \text{for } U_k < 0.60 \text{ or } S_k < 0$$

### Difficulty Target ($T(L)$)

$$T(L) = T_0 \cdot 2^{\lfloor L / 4 \rfloor} \cdot L^{\pi}$$

---

## Execution Profiles in `hermes setup`

1. **Full Access / Headless Automation**: Zero-block execution with host safety invariants.
2. **Developer Pro Mode**: Auto-approves file edits and safe shell commands.
3. **Standard Balanced Mode**: Standard interactive confirmation.
4. **Strict Sandbox Mode**: Strict confirmation policy.

---

## Tests

Run the test suite:

```bash
python3 -m unittest tests/test_tier3_high_assurance.py
```

---

## License
MIT
