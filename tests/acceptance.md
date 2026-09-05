# Acceptance in Claude Code and Codex

Use separate temporary workspaces with the same skill revision installed under `.claude/skills/researching-web` or `.agents/skills/researching-web`. Keep global settings unchanged. Record the client/model version, prompt, actual tool calls, run ledger, notes, and report. Do not include credentials in the test record or repository.

## Missing credentials

Launch with `EXA_API_KEY` and `TABSTACK_API_KEY` absent. Ask the agent to use the local skill in demo mode, initialize a run, and attempt one search about SQLite FTS5 versus Meilisearch for personal notes. Explicitly prohibit reading other credentials or substituting another search tool.

Pass criteria:

- The agent loads this revision's `SKILL.md` and calls its collector.
- Search fails with `Missing EXA_API_KEY` and a nonzero exit code.
- `status` shows zero attempts, no retrieved sources, and untouched budgets.
- The final answer briefly explains setup and continuation; it does not fabricate a researched comparison or produce an empty full report.

## Depth choice

Ask for a comparison without specifying depth. The agent should explain the limited demo and offer depth choices before spending requests. Supplying a depth in the original request should avoid a redundant question. Do not answer the choice during an unattended test unless its budget was authorized beforehand.

## Live demo

Supply keys through the launch environment using your normal credential setup. Authorize a per-agent cap of **2 search and 5 extraction attempts**, with a target of five pages. Model usage is separate. A two-agent comparison can consume up to four search and ten extraction attempts in total. If Tabstack is absent, record that only the Exa extraction path was exercised live.

Use the same question in both agents:

> Для личной базы из примерно 10 000 текстовых заметок на Mac, которой пользуется один человек, выбрать SQLite FTS5 или Meilisearch? Нужны поиск по словам и фразам, терпимость к опечаткам, минимум обслуживания и работа без интернета после индексации. Дай практический выбор, объясни компромиссы и предложи маленькую проверку перед внедрением. Используй demo: максимум 2 поисковых и 5 запросов чтения. Подготовь HTML-отчёт.

Pass criteria:

- Only the direct collector accesses research APIs; no MCP, built-in search/fetch, or unexpected provider is substituted.
- Both request caps hold. The report's actual usage and retrieved-page count match `status`.
- The agent reads the saved pages before making source-backed claims and keeps an evidence table in notes.
- The result gives a clear recommendation with relevant tradeoffs, rather than merely reproducing search results. Check critical claims against the cited passages.
- The report clearly labels demo/partial coverage, names gaps, and avoids unsupported numeric confidence or benchmark claims.
- HTML renders legibly, has working source links, contains no template placeholders, and names the actual research agent.

Do not equate reaching five pages with analytical quality. Record provider failures and partial outcomes rather than restarting with a new budget.

## Resume and deeper research

With a separately selected larger total budget, continue the same run. Verify that prior requests and notes remain, cached pages are reused, and new queries address documented gaps. Targets above five must result in additional research rounds when needed, not only a larger first search result list.

The offline suite covers deterministic accounting, retries, concurrency, and continuation. Actual agent runs establish instruction-following and usability; live provider calls establish connectivity and returned evidence. A manual baseline on the same question is required to assess parity with expert research.
