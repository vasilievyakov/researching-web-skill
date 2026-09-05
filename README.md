<p align="center">
  <img src="assets/logo.svg" width="120" alt="Researching Web Logo"/>
</p>

# Researching Web

A skill for Claude Code and Codex that researches through **direct Exa and Tabstack APIs**. Choose a depth, collect and read sources in rounds, check contradictions, and produce a cited answer or HTML report with an honest account of its coverage.

Exa provides search. Tabstack extracts page content; Exa contents can also read pages. MCP installation is no longer required. The skill does not use built-in web search as a fallback.

## Installation

For Claude Code:

```bash
git clone https://github.com/vasilievyakov/researching-web-skill.git \
  ~/.claude/skills/researching-web
```

For Codex:

```bash
git clone https://github.com/vasilievyakov/researching-web-skill.git \
  ~/.agents/skills/researching-web
```

For a project-local installation, use `.claude/skills/researching-web` for Claude Code or `.agents/skills/researching-web` for Codex inside that project. In Codex, select the skill with `$researching-web`; see the [official skill loading documentation](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills). If an older copy is already installed elsewhere, select the intended copy explicitly rather than assuming matching names will merge.

Requirements: Python 3.10+, internet access, an [Exa API key](https://exa.ai), and optionally a [Tabstack API key](https://tabstack.ai). The collector uses Python's standard library; no npm server or Python package installation is needed.

Make `EXA_API_KEY` and optionally `TABSTACK_API_KEY` available in the environment that launches your agent. For example, in a terminal session (replace the placeholders locally):

```bash
export EXA_API_KEY='your-exa-key'
export TABSTACK_API_KEY='your-tabstack-key'  # optional
claude
# Or launch Codex from the same environment: codex
```

Do not put real keys in prompts, reports, commits, or shared shell history. An already-running desktop app may not inherit a terminal's environment; configure its launch environment before starting it. The skill never reads keys from other applications' settings. Existing MCP configuration can stay installed for other workflows; this skill does not use it.

Without API keys, collection stops with a setup message. Example reports remain available for viewing, but are not returned as current research.

## Choose the depth before spending requests

| Mode | Maximum search attempts | Maximum extraction attempts | Target retrieved pages | Purpose |
|------|-------------------------|-----------------------------|------------------------|---------|
| Demo (default) | 2 | 5 | 5 | Small trial of the workflow; explicitly labeled limited |
| Standard | 8 | 24 | 15 | Several search/read rounds and verification |
| Deep | 20 | 80 | 50 | Broader subquestions, follow-up sources, and contradictions |
| Custom | User-selected | User-selected | User-selected | An explicitly budgeted larger investigation |

These numbers are starting presets, **not provider quotas, price estimates, or guarantees of quality**. Search results, retrieved pages, independently corroborating sources, and agents are different counts. A 108-agent investigation has no automatic conversion into a page or request budget. Model/agent usage is separate from these API limits.

Every outgoing attempt counts, including failures, optional retries, and an Exa extraction after Tabstack fails. A search can return multiple candidates; only extracted pages enter the retrieved-source count. Provider credits, billing rules, and account rate limits may differ from request counts. The report exposes both local usage and the fact that provider quota is unknown.

The agent offers the depth choice unless you already specified it. Starting the collector without `--depth` selects demo; it never silently starts a full-scale run. Larger research uses the same workflow with more rounds and evidence, rather than only increasing the number of initial search results.

Example requests:

- “Compare these tools in standard mode. Show source gaps and conflicting claims.”
- “Research this topic deeply: up to 20 search and 80 extraction attempts, targeting 50 pages.”
- “Continue this saved investigation with a total cap of 40 search and 160 extraction attempts, targeting 100 pages.”

## How it works

```text
Choose depth → Plan subquestions → Search → Select → Read saved pages
                                     ↑                     ↓
                                     └── Coverage gaps ← Evaluate evidence
                                                             ↓
                                                Verify → Cited report
```

The agent expands queries, follows references, records evidence, and checks contradictions in successive rounds. It keeps a coverage checklist and research notes, so a later pass can continue the investigation. Reaching a source target does not establish completeness; the final report distinguishes sufficient coverage, partial work, and a budget-limited result.

The API collector supplies a persistent SQLite request ledger, source Markdown files, and caching. It does **not** perform model reasoning or generate a researched answer on its own. The full workflow is orchestrated by [SKILL.md](SKILL.md).

Concurrent workers must share the same run directory. Budget reservations are atomic, so parallel calls cannot each spend the whole allowance. Duplicate in-flight requests can still cost separate attempts; assign distinct work. The collector does not launch agents or limit their model usage.

## Collector quick start

This initializes a local demo without making an API call:

The commands below use the Claude installation path. For Codex, use `~/.agents/skills/researching-web/scripts/research.py` instead.

```bash
python3 ~/.claude/skills/researching-web/scripts/research.py init \
  --run ./research-runs/example --topic "A question to investigate"
```

The next commands make API calls when keys are available:

```bash
python3 ~/.claude/skills/researching-web/scripts/research.py search \
  --run ./research-runs/example --query "A focused query for primary evidence"

python3 ~/.claude/skills/researching-web/scripts/research.py extract \
  --run ./research-runs/example --url "https://example.com"

python3 ~/.claude/skills/researching-web/scripts/research.py status \
  --run ./research-runs/example
```

Read the returned Markdown file, update research notes, and repeat for coverage gaps. For complete command examples, continuation, and error behavior, see [API workflow](references/api-workflow.md).

## Demo and examples

### Live API examples

The same question about SQLite FTS5 versus Meilisearch for personal notes was researched in Codex and Claude Code on September 5, 2026. Each used two Exa searches and five Exa page extractions; the final reports were reviewed against saved evidence and checked at desktop and mobile widths. The examples show the result after review, not a guarantee of first-pass correctness.

- [Codex demo report](examples/sqlite-vs-meilisearch-codex-demo.html)
- [Claude Code demo report](examples/sqlite-vs-meilisearch-claude-demo.html)

Report review exposed unsupported assumptions about user requirements, inconsistent numbers inside provider documentation, missing adjacent citations, and narrow-screen overflow. The skill's verification instructions and report template were tightened accordingly. Correcting reports from saved evidence did not require additional research API calls. See [acceptance results](tests/acceptance-results.md) for the exact scope and limitations.

### Historical presentation examples

**The following are historical presentation examples, not live API results or acceptance tests of this implementation.** Their displayed counts and confidence percentages do not establish current coverage.

<p align="center">
  <img src="assets/demo.gif" width="700" alt="Historical illustration of the research workflow"/>
</p>

- [AI Coding Tools Market 2025](examples/insight-ai-coding-market-2025.html)
- [Claude Code vs Cursor vs Windsurf](examples/insight-claude-code-vs-cursor-vs-windsurf.html)

A demo run always says “Demo — limited research.” A standard/deep run that runs out of budget presents a partial result and the missing evidence. The [HTML template](references/report-template.html) puts mode, usage, and limitations above the findings.

## Verification

Run the offline regression suite:

```bash
python3 -m unittest discover -s tests -v
```

It exercises the CLI collection path with mocked HTTP responses, API request contracts, caching/resume, concurrent budget enforcement, retries, fallback, and failure handling. It makes no paid API requests. Mocked tests do not establish live provider availability, extraction quality, or equivalence to an expert's manual research.

For checks in both actual agents, use the [acceptance scenarios](tests/acceptance.md). Keep model/agent checks, live collection, and mocked transport checks separate when reporting results.

For a live acceptance pass, use an explicitly selected budget and real environment keys, then verify that cited claims are supported by the saved pages, query rounds close documented gaps, and the report's scope matches the ledger. Compare against a manual pass on the same question if quality parity is required.

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md). MIT — [LICENSE](LICENSE).
