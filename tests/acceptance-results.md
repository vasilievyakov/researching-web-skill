# Acceptance results — September 5, 2026

The same personal-notes search question from [acceptance.md](acceptance.md) was run in actual Claude Code and Codex sessions, explicitly loading isolated project-local copies of the skill. Collection used the direct API collector; reports were checked against the saved evidence and rendered in Chrome.

| Check | Codex | Claude Code |
|-------|-------|-------------|
| Client | Bundled Codex CLI 0.153.0-alpha.5 | Claude Code 2.1.261 |
| Model | gpt-6-astra | claude-opus-5 |
| Exa search attempts | 2/2, successful | 2/2, successful |
| Exa extraction attempts | 5/5, successful | 5/5, successful |
| Retrieved pages | 5 | 5 |
| Failed attempts, retries, fallback | 0 | 0 |
| Sources, notes, and HTML produced | Yes | Yes |
| Missing-key case | No research requests; ledger stayed empty | No research requests; ledger stayed empty |
| Final desktop render, 1280px | No page overflow or browser errors | No page overflow or browser errors |
| Final mobile render, 390px | No page overflow or browser errors | No page overflow or browser errors |
| Final unresolved template fields | None | None |
| Final external citation URLs absent from source ledger | None | None |

Total research API usage was **4 search plus 10 extraction attempts**, all successful. Tabstack had no configured key and was not exercised live. Its request contract and fallback behavior are covered by the offline tests. The 22-test offline suite passed on Python 3.14.6; skill validation and whitespace checks also passed.

## What review found and changed

- The first Claude draft favored lower maintenance by weakening the requested typo tolerance. It also asserted phrase support in its opening while acknowledging that Meilisearch phrase behavior was unverified later. The instructions now preserve required capabilities and demand consistent caveats in the actual report.
- The saved Meilisearch storage page disagreed with itself about raw input size and indexed disk size. Initial synthesis missed this. Verification now explicitly compares prose, tables, examples, units, and conditions within a source as well as between sources.
- Claude initially put citations mainly in its bibliography. The report check now requires adjacent citations for decisive claims, and its revised report includes them.
- Both initial reports overflowed at 390px. The template now wraps long content and confines table/code scrolling; a custom non-wrapping badge in Claude's report needed an additional correction.
- Scope summaries were too long and some labels remained English in a Russian report. Instructions now require compact scope fields, translated labels, and the report language on the HTML element.

Claude performed two additional local review/edit passes using the original files, with research API keys absent. The reviewer then made a final wording pass to remove remaining overstatements about integration code, memory estimates, and word forms. Codex's report received responsive styling and a shorter scope summary during review. **The published examples are reviewed outputs, not untouched first drafts.** The original research ledgers and request totals were preserved throughout; review did not recollect sources.

## Scope of the result

This establishes a working live Exa collection-to-report path in both agents for one demo question, with inspectable evidence and enforced local request caps. It does not establish unattended first-pass correctness, live Tabstack availability, automatic skill selection without explicit invocation, or quality parity with a large expert-led investigation. Deep/custom accounting and multi-round continuation were exercised with mocked responses, not an additional paid deep run. No search engine was installed or benchmarked against the user's actual notes.

The machine's older standalone Codex CLI 0.144.5 could not use its configured gpt-6-astra model. The test used the already installed app-bundled client; global client settings and installations were left unchanged.
