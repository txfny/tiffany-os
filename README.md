# Tiffany OS

One unified personal OS. North star: the best version of Tiffany. Body, mind, and nervous system as one connected system — not separate concerns. You talk to Claude in your terminal. Deterministic Azure Functions handle the data. No app, no dashboard — just a conversation.

**[Read the full backstory on why I built this.](docs/backstory.md)**

## Modules

| Module | Status | Purpose |
|---|---|---|
| [fitness-pipeline](skills/) | active | Physical training, readiness, progression |
| [gut-health](modules/gut-health/SKILL.md) | planned | Digestion, inflammation, gut-brain axis |
| [nervous-system](modules/nervous-system/SKILL.md) | planned | Stress regulation, HRV patterns, somatic awareness |
| [mind-curiosity](modules/mind-curiosity/SKILL.md) | planned | Arabic, neuroscience, interactive learning |

The fitness-pipeline (described below) is the first active module. The rest are scaffolded with context and will be filled in as I build each one.

---

## Module: fitness-pipeline

## Why This Exists

Most fitness apps treat everyone the same — fixed programs that ignore how you actually feel on any given day. Coach adapts to you. Every session starts with your biometrics (HRV, resting heart rate, sleep), subjective energy, symptoms, and soreness. The system runs that through a deterministic rule engine and generates a session calibrated to your readiness — not yesterday's plan.

## How It Works

You open your terminal, run `claude`, and tell it you want to train. Claude follows a strict pipeline defined in `CLAUDE.md`:

1. **Session type** — Azure Function determines what today's session is (upper, lower, cardio, rest) based on your weekly template. Claude doesn't decide this.
2. **Your snapshot** — You tell Claude how you're feeling (HRV, RHR, sleep, energy, soreness). Claude sends it to the readiness endpoint.
3. **Readiness tier** — The function returns LOW / MODERATE / HIGH with volume adjustments and RPE caps. Claude uses this to plan, not its own judgment.
4. **Data gaps** — The function checks if any recent sessions are missing from the log.
5. **Working weights** — Current weights per exercise come from the database. Claude never guesses these.
6. **Session plan** — Claude builds the plan using all of the above, grounded in the rules and progression model.
7. **Logging** — After your workout, you tell Claude what you did. It calls the save endpoint. Nothing is "logged" until the API confirms it.
8. **Validation** — Output validation checks the logged session for errors before closing out.

The key idea: **Claude owns reasoning. Code owns data.** The deterministic functions are the source of truth for session types, readiness scoring, and working weights. Claude's job is to synthesize that into a plan and communicate it naturally.

### What Gets Tracked

- **Biometrics**: HRV (ms), resting heart rate, heart rate recovery
- **Recovery signals**: sleep hours, subjective energy, mood
- **Hormonal context**: OC pill pack day (no phase-based intensity ceilings)
- **Symptoms**: bloating, GI, pain, fatigue — summed into a symptom load score
- **Soreness**: lower body, upper body, core — affects exercise selection
- **Equipment**: home gym (dumbbell-focused) or commercial gym (machines)

## Tech Stack

| Layer | Tech |
|-------|------|
| Coaching interface | [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (terminal) |
| Deterministic pipeline | Azure Functions (Node.js) |
| Data storage | Local JSON files (`data/sessions/`) — or swap in Azure Table Storage / Cosmos DB |
| Rules | YAML configs (`rules/`) |

## Getting Started

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — `npm install -g @anthropic-ai/claude-code`
- An [Anthropic API key](https://console.anthropic.com/) for Claude
- Node.js 18+
- An Azure account (for deploying the Functions pipeline)

### Setup

```bash
# 1. Clone
git clone https://github.com/txfny/tiffany-os.git
cd tiffany-os

# 2. Deploy Azure Functions
cd azure-functions
npm install
# Deploy to Azure (via VS Code Azure extension, Azure CLI, or GitHub Actions)
# After deploying, create azure-functions/.env.keys:
#   AZURE_FUNCTION_BASE_URL=https://<your-app>.azurewebsites.net/api
#   AZURE_FUNCTION_KEY=<your function key>

# 3. Customize your rules
# Edit rules/progression.yaml for your weekly template and exercise pool
# Edit rules/readiness.yaml for readiness scoring thresholds
# Update CLAUDE.md if you change endpoint URLs

# 4. Start coaching
cd ..
claude
# Then just say: "let's do today's session"
```

### Customization

This is designed to be forked and personalized:

- **`rules/progression.yaml`** — Weekly schedule, exercise pool, progression model
- **`rules/readiness.yaml`** — How biometrics map to readiness tiers
- **`rules/cycle-phase.yaml`** — Hormonal context rules
- **`CLAUDE.md`** — The instructions Claude follows (pipeline order, rules, endpoints)
- **`data/sessions/`** — Your training history (gitignored, stays local)

## File Map

```
azure-functions/        Deterministic pipeline (session-type, readiness, save, validate)
rules/                  Scoring and progression rules (YAML)
research/               Citation lookup table backing every rule
data/sessions/          Session logs (gitignored)
skills/                 Claude coaching skill definitions
CLAUDE.md               Pipeline instructions for Claude
```

## Research References

Scoring rules and coaching approach are informed by:

- Self-Determination Theory (Deci & Ryan) — autonomy, competence, relatedness
- JMIR mHealth studies on fitness app retention
- Behavior Change Technique taxonomy (Michie et al.) — goal setting, self-monitoring, feedback
- PMC research on adaptive training periodization

---

Built with [Claude Code](https://claude.com/claude-code).
