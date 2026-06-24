# Tiffany OS — Claude Code Build Plan

---

## 🗓 TOMORROW — What To Do

### Before you open Claude Code
1. Download the `tiffany-os-build-plan.md` file from this conversation
2. Move it into your `adaptive-fitness-coach` repo folder on your computer

### When you open Claude Code
Paste this exact prompt:

> "Read `tiffany-os-build-plan.md` and treat it as a runbook. Execute each step in order. After each step stop, show me what you built, and wait for me to say 'continue' before moving to the next one."

That's it. It'll take it from there. You just sit back, review each checkpoint, and say "continue" when you're happy with what it built.

### Your checkpoints (what to look for before saying continue)
- **After Step 1:** Repo should be renamed to `tiffany-os` on GitHub
- **After Step 2:** CLAUDE.md should have the Tiffany OS north star at the very top
- **After Step 3:** `modules/` folder exists with 3 placeholder SKILL.md files
- **After Steps 4-6:** Each SKILL.md should be filled in with the right context
- **After Step 7:** Final folder structure looks clean, everything pushed to GitHub

---


## The Vision
One unified personal OS. North star: best version of Tiffany.
Body, mind, nervous system — one connected system, not separate concerns.

## Current State
- Repo: `adaptive-fitness-coach`
- Has: Azure backend, Supabase persistence, deterministic pipeline
- CLAUDE.md exists with full fitness pipeline instructions
- Skills: coach, logger, planner, readiness, retrospective, snapshot

---

## Step 1 — Rename the Repo

In Claude Code terminal:

> "Rename this repo from `adaptive-fitness-coach` to `tiffany-os`. Update any internal references to the old name in README.md and CLAUDE.md. Push the rename to GitHub."

---

## Step 2 — Add Tiffany OS North Star to CLAUDE.md

In Claude Code terminal:

> "Read my current CLAUDE.md. Add the following section at the very top of the file, before everything else. Do not change anything below it.
>
> ---
> # Tiffany OS — Personal
>
> ## North Star
> This system exists to help Tiffany become the best version of herself.
> Body, mind, and nervous system are one connected system — not separate
> concerns. Every module feeds into one goal: a Tiffany who is regulated,
> curious, strong, and present.
>
> ## Who is Tiffany
> - Technical Program Manager at Microsoft (CE&S / DS+VI, AI Platform)
> - Systems thinker — prefers to build things herself over off-the-shelf
> - Learns best by doing and exploring, not passive consumption
> - Coptic Orthodox, Egyptian Arabic with family
> - Lives in NYC with her boyfriend
> - Working to reconnect with a version of herself that feels more alive
>   and present
> - High achiever who struggles to disconnect — nervous system runs hot
>
> ## How to talk to Tiffany
> - Match her energy — she's casual, direct, and funny
> - Don't over-explain or be robotic
> - Give her the science but make it land in plain language
> - Treat her as a partner, not a patient or a student
> - Call out patterns you notice across sessions — she wants the dots
>   connected
> - She builds in sprints — meet her where she is, not where she should be
>
> ## Modules
> | Module | Status | Purpose |
> |---|---|---|
> | fitness-pipeline | active | Physical training, readiness, progression |
> | gut-health | planned | Digestion, inflammation, gut-brain axis |
> | nervous-system | planned | Stress regulation, HRV patterns, somatic awareness |
> | mind-curiosity | planned | Arabic, neuroscience, interactive learning |
>
> ## Guiding Principles
> - Body, mind, and nervous system are one system
> - Data informs but doesn't override intuition
> - Progress over perfection — consistency beats optimization
> - If something feels off, it probably is — log it, don't dismiss it
> ---"

---

## Step 3 — Create Modules Folder with Placeholders

In Claude Code terminal:

> "Create a `modules/` folder with three placeholder SKILL.md files:
> `modules/gut-health/SKILL.md`
> `modules/nervous-system/SKILL.md`
> `modules/mind-curiosity/SKILL.md`
>
> Each file should have:
> - Title and one-line purpose
> - North star connection (how it connects to the bigger Tiffany OS goal)
> - Status: planned
> - TODO section (empty for now, we'll fill it in next)
>
> Commit and push."

---

## Step 4 — Build the Gut Health SKILL.md

In Claude Code terminal:

> "Fill in `modules/gut-health/SKILL.md` with the following context.
>
> **Purpose:** Help Tiffany understand and heal her gut — identify food
> triggers, build consistent habits, and correlate gut patterns with
> stress and workload data.
>
> **Medical background (confirmed):**
> - Stool-filled colon confirmed — explains never feeling fully empty,
>   post-meal bloating, bladder pressure
> - H. pylori: negative, CT scan: clear
> - Ovarian cysts both sides (responding well to birth control)
> - Extra gas noted on ultrasound (unrelated to cysts)
> - Overactive bladder (structurally normal, likely gut pressure related)
> - SIBO testing pending — results TBD
> - Currently taking magnesium glycinate — working well
>
> **Doctor's recommendations (Galileo NP, 5/19/26):**
> - Start food diary to identify triggers
> - Research FODMAP diet
> - Follow up after SIBO test results
>
> **Key context:**
> - Gut motility never fully recovered — working on rebuilding it
> - Gut-brain axis: chronic stress slows gut motility directly
> - Coffee no longer stimulates her colon (nervous system adapted)
> - Hydration is a known gap — doesn't drink enough water naturally
>
> **Evidence-based approaches she's using or open to:**
> - Magnesium glycinate (already taking, likes it)
> - Olive oil on empty stomach (bile stimulation)
> - Ginger/turmeric/lemon tonic
> - FODMAP elimination protocol
> - Food diary for trigger identification
>
> **What to build in this module:**
> - Food diary logger (food, time, symptoms after eating)
> - Trigger pattern detector (correlate foods with bloating/symptoms)
> - Hydration tracker (artifact already exists, integrate it)
> - SIBO results tracker once test is done
> - Morning protocol tracker (olive oil, hydration, movement)
> - Cross-module: correlate gut symptoms with workload and HRV data
>
> Commit and push."

---

## Step 5 — Build the Nervous System SKILL.md

In Claude Code terminal:

> "Fill in `modules/nervous-system/SKILL.md` with the following context.
>
> **Purpose:** Help Tiffany understand her nervous system patterns,
> reduce baseline hyperactivation, and build sustainable regulation habits.
>
> **Key context:**
> - Tiffany runs hot — chronically hyperactivated baseline
> - Difficulty disconnecting from work, mind stays on even when body stops
> - High achiever pattern: pushes through signals instead of responding to them
> - HRV already tracked via Apple Watch and feeds into fitness pipeline readiness
>
> **What to build in this module:**
> - Surface patterns between HRV dips, workload intensity, gut symptoms,
>   and sleep quality
> - Regulation habit tracker (somatic practices, breathing, rest)
> - Cross-module: connect nervous system state to readiness scores and
>   gut symptom logs
> - Flag when patterns suggest the system needs a reset, not a push
>
> Commit and push."

---

## Step 6 — Build the Mind & Curiosity SKILL.md

In Claude Code terminal:

> "Fill in `modules/mind-curiosity/SKILL.md` with the following context.
>
> **Purpose:** Help Tiffany explore and learn interactively — not passive
> consumption, but active application and connection-making.
>
> **Key context:**
> - Learning Egyptian Arabic: conversational level, working on reading
>   and writing the script
> - Deep interest in neuroscience and AI — wants to apply it, not just
>   read about it
> - Loves connecting dots across disciplines
> - Has a separate neuroscience/AI repo to potentially integrate here
>
> **What to build in this module:**
> - Arabic learning session tracker (vocab, script practice, progress)
> - Curiosity log — topics explored, connections made to other modules
> - Interactive learning prompts tailored to how Tiffany learns best
> - Cross-module: surface connections between neuroscience concepts and
>   her own body/nervous system data
>
> Commit and push."

---

## Step 7 — Final Commit and Review

In Claude Code terminal:

> "Do a final review of the full repo structure. Make sure:
> - CLAUDE.md has the Tiffany OS north star at the top
> - All 3 module SKILL.md files are filled in
> - README.md reflects the new name and expanded purpose
> - Everything is committed and pushed to GitHub
>
> Show me the final folder structure."

---

## Ideas Backlog (build eventually)
- [ ] Dashboard: body + mind + nervous system in one view
- [ ] Gut symptom log correlated with workload cycles
- [ ] SIBO results integration once test is done
- [ ] FODMAP elimination tracker
- [ ] Arabic script practice tool
- [ ] Curiosity log with connection mapping
- [ ] Hydration artifact already exists — integrate into morning protocol
