# Direct API workflow

All commands below assume the working directory is the installed skill directory. From another project, use the absolute path to `scripts/research.py`. Use a separate, persistent `--run` directory for each investigation, and reuse it for continuation.

## Initialize, collect, inspect

```bash
python3 scripts/research.py init --run /path/to/research-runs/topic --topic "Question" --depth standard
python3 scripts/research.py search --run /path/to/research-runs/topic --query "primary evidence for subquestion" --results 10
python3 scripts/research.py extract --run /path/to/research-runs/topic --url "https://example.org/article"
python3 scripts/research.py status --run /path/to/research-runs/topic
```

`init` and `status` are local, free operations. `init` refuses to overwrite an existing run. Default depth is demo; standard/deep must be selected explicitly. Custom initialization can override `--search-limit`, `--extract-limit`, and `--source-target`; any override labels the mode custom. Search limits may be zero for URL-only research. Extraction limits and targets must be positive, with target no greater than extraction cap.

`search` uses Exa and returns compact candidate metadata, an attempt ID, and a cache indicator. `--results` accepts 1–100 (default 10). Changing this value changes the request and cache key, and can change provider cost; it does not change the attempt cap. Empty successful searches are cached; try a different query for a gap.

`extract` returns a path to saved Markdown, source URL/title, provider, attempt ID, and retrieval time. Read that file before marking the source analyzed. `--provider auto` prefers Tabstack when its key exists, otherwise Exa. Set `--provider exa` or `--provider tabstack` to require that provider without fallback.

In auto mode, Tabstack fetch/content failures (404, 422, network, or 5xx) may fall back to Exa within the same extraction budget. The result records the fallback reason; failed attempts remain in the ledger. Authentication, quota/payment, and rate-limit errors stop the command instead of silently switching providers. Successful sibling commands remain usable.

## Resume and deepen

The agent keeps `notes.md` beside the ledger: coverage checklist, round decisions, evidence table, contradictions, rejected duplicates, and next queries. Read it with `status` before continuing. Notes describe reasoning; the ledger records actual collection.

After the user chooses a larger budget, promote the existing run:

```bash
python3 scripts/research.py budget --run /path/to/research-runs/topic --depth deep \
  --reason "User selected deep research to resolve the remaining coverage gaps"
```

For a larger custom pass:

```bash
python3 scripts/research.py budget --run /path/to/research-runs/topic \
  --search-limit 40 --extract-limit 160 --source-target 100 \
  --reason "User approved these total caps for the next research rounds"
```

Caps are **new totals, not additional allowances**. If 8 searches have already been attempted and the new cap is 20, 12 remain. Used attempts, pages, and cache entries are preserved. A reason and old/new configurations are logged. Limits cannot be reduced below usage. The command records a decision; the skill is responsible for obtaining the user's choice. It is not an access-control system against a caller modifying local files.

Do not reset the ledger, create new runs for individual workers, or call providers outside this script to evade the cap. All cooperating workers share an absolute run path; SQLite reserves each attempt before network access. A crash after reservation still counts conservatively, even if the provider never received the request. Duplicate concurrent cache misses can spend multiple attempts, but cannot exceed the shared caps.

## Cache, retries, and failures

- Successful identical searches and extractions reuse saved data. The run's cache does not expire automatically; check retrieval dates when resuming a time-sensitive question.
- `--fresh` bypasses the **local** cache and spends another attempt. Provider-side caches can still apply; it does not guarantee a newly crawled page. Previous responses and Markdown versions remain available in the run directory.
- Retries default to zero. `--retries 1` or `--retries 2` allows bounded extra attempts for connection failures, 429, and 5xx. Each retry needs remaining budget. `Retry-After` delays over ten seconds or unsupported dates stop the command instead of sleeping or retrying early.
- Missing keys make no request. Malformed responses and empty extraction text are failures, not sources. Errors exit nonzero; inspect `status`, fix the cause, or report the remaining gap.
- Budget exhaustion stops before sending the next request. A failed fetch followed by fallback needs two extraction slots. There is no promise that every attempt is billed identically by a provider.

`status` reports caps/usage, attempts by provider, failed/pending attempts, retrieved sources, source target shortfall, and budget history. `source_target_reached` means only that enough unique requested page URLs were retrieved. It says nothing about analysis, independent evidence, or completeness. Fragment URLs are deduplicated; tracking variants, redirects, and syndicated content require the agent's review.

## Saved data and credentials

- `state.sqlite3`: configuration, sanitized request bodies, successful JSON responses, attempt timestamps/errors, source metadata, and budget changes.
- `sources/<attempt-id>.md`: retrieved text; CLI output gives absolute file paths rather than dumping every page into the conversation.
- `notes.md`: agent-maintained research state, including analyzed sources and claim evidence.

Keep the directory local and out of version control; it contains research content and queries. `research-runs/` and `.env` files are ignored in this repository. API keys come only from environment variables. The collector does not save authentication headers, and redacts exact environment key values from saved responses/output. It does not sanitize unrelated private information in source content.

Provider quotas are not queried by this tool; `provider_quota` is explicitly unknown. The local caps do not limit other tools, runs, model tokens, or provider-internal operations. Check account dashboards when planning a paid run; do not present these presets as the account's remaining credits.

## HTTP contracts

| Operation | Endpoint | Authentication | Request |
|-----------|----------|----------------|---------|
| Search | `POST https://api.exa.ai/search` | `x-api-key: EXA_API_KEY` | `query`, `type: auto`, `numResults` |
| Exa extraction | `POST https://api.exa.ai/contents` | `x-api-key: EXA_API_KEY` | `ids: [url]`, `text: true` |
| Tabstack extraction | `POST https://api.tabstack.ai/v1/extract/markdown` | `Authorization: Bearer TABSTACK_API_KEY` | `url`, `content: main`, `effort: standard`, `metadata: true` |

No Tabstack search or autonomous research endpoint is called. Exa search returns `results`; Exa contents provides `results[].text`; Tabstack returns `content` and optional `metadata`. The client uses a 60-second timeout and rejects redirects rather than forwarding authentication headers.

Contracts checked against official documentation: [Exa search](https://exa.ai/docs/reference/search), [Exa contents](https://exa.ai/docs/reference/get-contents), [Tabstack Markdown extraction](https://docs.tabstack.ai/api/resources/extract/methods/markdown/).
