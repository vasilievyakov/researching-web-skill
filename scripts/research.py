#!/usr/bin/env python3
"""Budgeted Exa/Tabstack collection. The calling agent plans and synthesizes."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
from urllib import error, parse, request


PROFILES = {
    "demo": {"search_limit": 2, "extract_limit": 5, "source_target": 5},
    "standard": {"search_limit": 8, "extract_limit": 24, "source_target": 15},
    "deep": {"search_limit": 20, "extract_limit": 80, "source_target": 50},
}
ENDPOINTS = {
    ("exa", "search"): "https://api.exa.ai/search",
    ("exa", "extract"): "https://api.exa.ai/contents",
    ("tabstack", "extract"): "https://api.tabstack.ai/v1/extract/markdown",
}
KEYS = {"exa": "EXA_API_KEY", "tabstack": "TABSTACK_API_KEY"}


def now():
    return datetime.now(timezone.utc).isoformat()


def redact(value):
    if isinstance(value, str):
        for name in KEYS.values():
            secret = os.environ.get(name)
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return value
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {redact(key): redact(item) for key, item in value.items()}
    return value


def canonical_url(value):
    parts = parse.urlsplit(value.strip())
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
        raise ValueError("Source URL must be HTTP(S), without embedded credentials.")
    return parse.urlunsplit((parts.scheme, parts.netloc.lower(), parts.path or "/", parts.query, ""))


class ResearchError(Exception):
    pass


class APIError(ResearchError):
    def __init__(self, message, status=0, retry_after=1):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after

    @property
    def retryable(self):
        return self.status == 0 or self.status == 429 or 500 <= self.status < 600


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def post_json(provider, kind, body, key):
    headers = {"Content-Type": "application/json", "User-Agent": "researching-web-skill/1"}
    headers["x-api-key" if provider == "exa" else "Authorization"] = key if provider == "exa" else f"Bearer {key}"
    req = request.Request(ENDPOINTS[provider, kind], data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        # Do not forward credentials to a redirected endpoint.
        with request.build_opener(NoRedirect).open(req, timeout=60) as response:
            result = json.load(response)
    except error.HTTPError as exc:
        try:
            delay = float(exc.headers.get("Retry-After", "1"))
        except ValueError:
            delay = 60  # HTTP-date or unknown delay: stop instead of retrying early.
        raise APIError(f"{provider} returned HTTP {exc.code}.", exc.code, delay) from None
    except (error.URLError, TimeoutError, OSError):
        raise APIError(f"{provider} connection failed or timed out; the attempt is counted.") from None
    except (ValueError, UnicodeError):
        raise APIError(f"{provider} returned invalid JSON.", 502) from None
    if not isinstance(result, dict):
        raise APIError(f"{provider} returned an unexpected response.", 502)
    return result


class Run:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.database = self.directory / "state.sqlite3"
        if not self.database.is_file():
            raise ResearchError("Run not found. Use init once, then reuse the same --run directory.")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @classmethod
    def create(cls, directory, topic, depth="demo", **overrides):
        config = dict(PROFILES[depth], topic=redact(topic), depth=depth, created_at=now())
        changes = {key: value for key, value in overrides.items() if value is not None}
        config.update(changes)
        if changes:
            config["depth"] = "custom"
        cls.validate_config(config)
        folder = Path(directory).resolve()
        try:
            folder.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise ResearchError("Run directory already exists; use status or budget to resume. Nothing was reset.") from None
        db = sqlite3.connect(folder / "state.sqlite3")
        try:
            db.executescript("""
                CREATE TABLE config (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL);
                CREATE TABLE attempts (
                    id INTEGER PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT,
                    provider TEXT NOT NULL, kind TEXT NOT NULL, cache_key TEXT NOT NULL,
                    request TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending',
                    response TEXT, error TEXT
                );
                CREATE TABLE sources (
                    url TEXT PRIMARY KEY, title TEXT NOT NULL, provider TEXT NOT NULL,
                    attempt_id INTEGER NOT NULL, retrieved_at TEXT NOT NULL, path TEXT NOT NULL
                );
                CREATE TABLE budget_history (changed_at TEXT, reason TEXT, old_config TEXT, new_config TEXT);
            """)
            db.execute("INSERT INTO config VALUES (1, ?)", (json.dumps(config),))
            db.commit()
        finally:
            db.close()
        (folder / "sources").mkdir()
        return cls(folder)

    @staticmethod
    def validate_config(config):
        for key in ("search_limit", "extract_limit", "source_target"):
            if not isinstance(config[key], int) or config[key] < (0 if key == "search_limit" else 1):
                raise ValueError(f"{key} must be a positive integer (search_limit may be zero).")
        if config["source_target"] > config["extract_limit"]:
            raise ValueError("source_target cannot exceed extract_limit; each page requires a request.")

    def budget(self, reason, depth=None, **overrides):
        if not reason.strip():
            raise ValueError("A reason is required for a budget change.")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = json.loads(db.execute("SELECT value FROM config").fetchone()[0])
            updated = dict(old)
            if depth:
                updated.update(PROFILES[depth], depth=depth)
            changes = {key: value for key, value in overrides.items() if value is not None}
            updated.update(changes)
            if changes:
                updated["depth"] = "custom"
            self.validate_config(updated)
            for kind in ("search", "extract"):
                used = db.execute("SELECT count(*) FROM attempts WHERE kind=?", (kind,)).fetchone()[0]
                if updated[kind + "_limit"] < used:
                    raise ValueError(f"Cannot set {kind} limit below {used} attempts already used.")
            db.execute("UPDATE config SET value=?", (json.dumps(updated),))
            db.execute("INSERT INTO budget_history VALUES (?, ?, ?, ?)",
                       (now(), redact(reason), json.dumps(old), json.dumps(updated)))
        return self.status()

    def reserve(self, provider, kind, body, cache_key):
        with self.connect() as db:
            # All workers reserve from the same ledger before any network access.
            db.execute("BEGIN IMMEDIATE")
            config = json.loads(db.execute("SELECT value FROM config").fetchone()[0])
            used = db.execute("SELECT count(*) FROM attempts WHERE kind=?", (kind,)).fetchone()[0]
            if used >= config[kind + "_limit"]:
                raise ResearchError(f"{kind} budget exhausted ({used}/{config[kind + '_limit']}). Stop or explicitly extend this run.")
            cursor = db.execute("INSERT INTO attempts (started_at, provider, kind, cache_key, request) VALUES (?, ?, ?, ?, ?)",
                                (now(), provider, kind, cache_key, json.dumps(redact(body))))
            return cursor.lastrowid

    def call(self, provider, kind, body, fresh=False, retries=0):
        cache_key = hashlib.sha256(json.dumps([provider, kind, body], sort_keys=True).encode()).hexdigest()
        if not fresh:
            with self.connect() as db:
                cached = db.execute("SELECT id, response FROM attempts WHERE cache_key=? AND state='success' ORDER BY id DESC LIMIT 1", (cache_key,)).fetchone()
            if cached:
                return json.loads(cached["response"]), cached["id"], True
        key = os.environ.get(KEYS[provider], "").strip()
        if not key:
            raise ResearchError(f"Missing {KEYS[provider]}. No request was sent; no built-in search or sample substitution.")
        for retry in range(retries + 1):
            attempt_id = self.reserve(provider, kind, body, cache_key)
            try:
                result = redact(post_json(provider, kind, body, key))
                self.validate_response(provider, kind, result)
            except APIError as exc:
                with self.connect() as db:
                    db.execute("UPDATE attempts SET state='failed', finished_at=?, error=? WHERE id=?", (now(), str(exc), attempt_id))
                if retry < retries and exc.retryable and 0 <= exc.retry_after <= 10:
                    time.sleep(exc.retry_after)
                    continue
                raise
            with self.connect() as db:
                db.execute("UPDATE attempts SET state='success', finished_at=?, response=? WHERE id=?", (now(), json.dumps(result), attempt_id))
            return result, attempt_id, False

    @staticmethod
    def validate_response(provider, kind, result):
        if not isinstance(result, dict):
            raise APIError("Unexpected API response.", 502)
        if kind == "search" or provider == "exa":
            rows = result.get("results")
            if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                raise APIError("Missing API results list.", 502)
            if kind == "search":
                return
            content = rows[0].get("text") if rows else None
        else:
            content = result.get("content")
        if not isinstance(content, str) or not content.strip():
            raise APIError("No page text was returned; this source was not retrieved.", 422)

    def search(self, query, results=10, fresh=False, retries=0):
        query = " ".join(query.split())
        if not query or not 1 <= results <= 100:
            raise ValueError("Provide a nonempty query and 1–100 results.")
        body = {"query": query, "type": "auto", "numResults": results}
        response, attempt_id, cached = self.call("exa", "search", body, fresh, retries)
        candidates = {}
        for row in response["results"]:
            try:
                url = canonical_url(row.get("url", ""))
            except (ValueError, AttributeError):
                continue
            candidates[url] = {key: row.get(key) for key in ("title", "id", "publishedDate", "author")}
            candidates[url]["url"] = url
        return {"query": redact(query), "attempt_id": attempt_id, "cached": cached,
                "candidates": list(candidates.values()), "note": "Search results are candidates, not analyzed sources."}

    def extract(self, url, provider="auto", fresh=False, retries=0):
        url = canonical_url(url)
        if not fresh:
            with self.connect() as db:
                source = db.execute("SELECT * FROM sources WHERE url=?", (url,)).fetchone()
            if source and (provider == "auto" or provider == source["provider"]) and Path(source["path"]).is_file():
                return dict(source, cached=True)
        selected = provider
        if selected == "auto":
            selected = "tabstack" if os.environ.get(KEYS["tabstack"], "").strip() else "exa"
        fallback = None
        try:
            response, attempt_id, cached = self.fetch(url, selected, fresh, retries)
        except APIError as exc:
            # Rate/quota/authentication errors must be visible, not hidden by another provider.
            if provider != "auto" or selected != "tabstack" or exc.status not in (0, 404, 422) and not 500 <= exc.status < 600:
                raise
            if not os.environ.get(KEYS["exa"], "").strip():
                raise
            fallback = str(exc)
            selected = "exa"
            response, attempt_id, cached = self.fetch(url, selected, fresh, retries)
        row = response["results"][0] if selected == "exa" else response
        content = row["text"] if selected == "exa" else row["content"]
        metadata = row.get("metadata") or {}
        title = row.get("title") or (metadata.get("title") if isinstance(metadata, dict) else None) or url
        filename = self.directory / "sources" / f"{attempt_id:06d}.md"
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=filename.parent, delete=False) as output:
            output.write(content)
            temporary = Path(output.name)
        temporary.replace(filename)
        with self.connect() as db:
            timestamp = db.execute("SELECT finished_at FROM attempts WHERE id=?", (attempt_id,)).fetchone()[0]
            db.execute("INSERT OR REPLACE INTO sources VALUES (?, ?, ?, ?, ?, ?)",
                       (url, title, selected, attempt_id, timestamp, str(filename)))
        return {"url": url, "title": title, "provider": selected, "attempt_id": attempt_id,
                "retrieved_at": timestamp, "path": str(filename), "cached": cached, "fallback_reason": fallback}

    def fetch(self, url, provider, fresh, retries):
        body = {"ids": [url], "text": True} if provider == "exa" else {
            "url": url, "content": "main", "effort": "standard", "metadata": True,
        }
        return self.call(provider, "extract", body, fresh, retries)

    def status(self):
        with self.connect() as db:
            db.execute("BEGIN")
            config = json.loads(db.execute("SELECT value FROM config").fetchone()[0])
            attempts = [dict(row) for row in db.execute("SELECT id, started_at, provider, kind, request, state, error FROM attempts ORDER BY id")]
            sources = [dict(row) for row in db.execute("SELECT * FROM sources ORDER BY attempt_id")]
            history = [dict(row) for row in db.execute("SELECT * FROM budget_history ORDER BY rowid")]
        budgets = {}
        for kind in ("search", "extract"):
            used = sum(row["kind"] == kind for row in attempts)
            limit = config[kind + "_limit"]
            budgets[kind] = {"used": used, "limit": limit, "remaining": limit - used}
        for row in attempts:
            row["request"] = json.loads(row["request"])
        for row in history:
            for key in ("old_config", "new_config"):
                row[key] = json.loads(row[key])
        shortfall = max(0, config["source_target"] - len(sources))
        return {"run": str(self.directory), "config": config, "budgets": budgets,
                "provider_attempts": {provider: sum(row["provider"] == provider for row in attempts) for provider in KEYS},
                "credentials_available": {provider: bool(os.environ.get(key, "").strip()) for provider, key in KEYS.items()},
                "provider_quota": "unknown; local attempt limits are not provider credits or monetary costs",
                "sources_retrieved": len(sources), "source_shortfall": shortfall,
                "collection_status": "demo" if config["depth"] == "demo" else "target_not_reached" if shortfall else "source_target_reached",
                "note": "Retrieved pages are not necessarily analyzed or independent. The agent must assess coverage and claims.",
                "sources": sources, "attempts": attempts, "budget_history": history}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "status", "budget", "search", "extract"):
        sub = commands.add_parser(name)
        sub.add_argument("--run", required=True, help="Persistent run directory; share across workers")
        if name in ("init", "budget"):
            sub.add_argument("--depth", choices=PROFILES, default="demo" if name == "init" else None)
            for key in ("search-limit", "extract-limit", "source-target"):
                sub.add_argument("--" + key, type=int)
        if name == "init":
            sub.add_argument("--topic", required=True)
        if name == "budget":
            sub.add_argument("--reason", required=True)
        if name in ("search", "extract"):
            sub.add_argument("--fresh", action="store_true", help="Bypass cache; spends the existing budget")
            sub.add_argument("--retries", type=int, choices=(0, 1, 2), default=0, help="Extra attempts; each counts against budget")
        if name == "search":
            sub.add_argument("--query", required=True)
            sub.add_argument("--results", type=int, default=10)
        if name == "extract":
            sub.add_argument("--url", required=True)
            sub.add_argument("--provider", choices=("auto", "exa", "tabstack"), default="auto")
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    directory = args.pop("run")
    try:
        if command == "init":
            result = Run.create(directory, **args).status()
        else:
            run = Run(directory)
            result = getattr(run, command)(**args)
        print(json.dumps(redact(result), ensure_ascii=False, indent=2))
        return 0
    except (ResearchError, ValueError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"error": redact(str(exc)), "next_step": "Inspect status for this run; do not reset it to bypass a limit."}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
