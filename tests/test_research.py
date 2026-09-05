import contextlib
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib import error


SPEC = importlib.util.spec_from_file_location("research", Path(__file__).resolve().parents[1] / "scripts" / "research.py")
research = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(research)


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = str(Path(self.temp.name) / "run")
        self.env = patch.dict(os.environ, {"EXA_API_KEY": "fake-exa-secret", "TABSTACK_API_KEY": "fake-tabstack-secret"}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.transport = patch.object(research, "post_json")
        self.post = self.transport.start()
        self.addCleanup(self.transport.stop)
        self.run = research.Run.create(self.directory, "Comparison topic")

    def cli(self, *args):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = research.main([*args, "--run", self.directory])
        return code, json.loads(output.getvalue() or errors.getvalue())

    def test_cli_round_trip_resume_and_cached_pages(self):
        self.post.return_value = {"results": [
            {"url": "https://example.org/page#one", "title": "Official source"},
            {"url": "https://example.org/page#two", "title": "Same page"},
        ]}
        code, search = self.cli("search", "--query", " primary   evidence ")
        self.assertEqual(code, 0)
        self.assertEqual(len(search["candidates"]), 1)
        self.post.assert_called_once_with("exa", "search", {"query": "primary evidence", "type": "auto", "numResults": 10}, "fake-exa-secret")
        self.post.return_value = {"content": "# Evidence\nActual source text", "metadata": {"title": "Primary evidence"}}
        code, source = self.cli("extract", "--url", search["candidates"][0]["url"])
        self.assertEqual(code, 0)
        self.assertEqual(Path(source["path"]).read_text(), "# Evidence\nActual source text")
        self.post.assert_called_with("tabstack", "extract", {"url": "https://example.org/page", "content": "main", "effort": "standard", "metadata": True}, "fake-tabstack-secret")
        resumed = research.Run(self.directory)
        self.assertTrue(resumed.search("primary evidence")["cached"])
        self.assertTrue(resumed.extract("https://example.org/page")["cached"])
        self.assertEqual(self.post.call_count, 2)
        state = resumed.status()
        self.assertEqual(state["sources_retrieved"], 1)
        self.assertEqual(state["source_shortfall"], 4)
        self.assertEqual(state["collection_status"], "demo")
        self.assertEqual(state["budgets"]["extract"]["used"], 1)

    def test_empty_search_is_not_a_source_and_is_cached(self):
        self.post.return_value = {"results": []}
        self.assertEqual(self.run.search("nothing")["candidates"], [])
        self.assertTrue(self.run.search("nothing")["cached"])
        self.assertEqual(self.run.status()["sources_retrieved"], 0)
        self.assertEqual(self.post.call_count, 1)

    def test_exa_only_when_tabstack_key_missing(self):
        del os.environ["TABSTACK_API_KEY"]
        self.post.return_value = {"results": [{"url": "https://example.org/", "text": "Exa text"}]}
        source = self.run.extract("https://example.org")
        self.assertEqual(source["provider"], "exa")
        self.post.assert_called_once_with("exa", "extract", {"ids": ["https://example.org/"], "text": True}, "fake-exa-secret")

    def test_fallback_is_visible_and_consumes_two_attempts(self):
        self.post.side_effect = [research.APIError("Tabstack fetch failed", 422), {"results": [{"text": "Fallback evidence"}]}]
        source = self.run.extract("https://example.org")
        self.assertEqual(source["provider"], "exa")
        self.assertEqual(source["fallback_reason"], "Tabstack fetch failed")
        state = self.run.status()
        self.assertEqual(state["budgets"]["extract"]["used"], 2)
        self.assertEqual(state["provider_attempts"], {"exa": 1, "tabstack": 1})
        self.assertEqual([row["state"] for row in state["attempts"]], ["failed", "success"])

    def test_auth_quota_rate_errors_do_not_silently_fallback(self):
        for code in (401, 402, 403, 429):
            with self.subTest(code=code):
                self.post.side_effect = research.APIError("Provider error", code)
                with self.assertRaises(research.APIError):
                    self.run.extract(f"https://example.org/{code}")
        self.assertEqual(self.post.call_count, 4)
        self.assertEqual(self.run.status()["provider_attempts"]["exa"], 0)

    def test_empty_extraction_cannot_count_as_success(self):
        self.post.return_value = {"results": [], "statuses": [{"status": "error"}]}
        with self.assertRaises(research.APIError):
            self.run.extract("https://example.org", provider="exa")
        self.assertEqual(self.run.status()["sources_retrieved"], 0)
        self.assertEqual(self.run.status()["attempts"][0]["state"], "failed")

    def test_missing_keys_make_no_requests(self):
        os.environ.clear()
        code, result = self.cli("search", "--query", "evidence")
        self.assertEqual(code, 1)
        self.assertIn("Missing EXA_API_KEY", result["error"])
        self.assertEqual(self.run.status()["budgets"]["search"]["used"], 0)
        self.post.assert_not_called()

    def test_retry_consumes_budget_and_stops_at_cap(self):
        self.post.side_effect = research.APIError("Unavailable", 503, 0)
        with self.assertRaisesRegex(research.ResearchError, "budget exhausted"):
            self.run.search("evidence", retries=2)
        self.assertEqual(self.post.call_count, 2)
        self.assertEqual(self.run.status()["budgets"]["search"]["remaining"], 0)

    def test_long_retry_after_does_not_retry_early(self):
        self.post.side_effect = research.APIError("Rate limited", 429, 120)
        with patch.object(research.time, "sleep") as sleep:
            with self.assertRaises(research.APIError):
                self.run.search("evidence", retries=2)
            sleep.assert_not_called()
        self.assertEqual(self.post.call_count, 1)

    def test_failed_tabstack_cannot_fallback_past_budget(self):
        self.run.budget("Small extraction budget", extract_limit=1, source_target=1)
        self.post.side_effect = research.APIError("Failed fetch", 422)
        with self.assertRaisesRegex(research.ResearchError, "budget exhausted"):
            self.run.extract("https://example.org")
        self.assertEqual(self.post.call_count, 1)

    def test_parallel_workers_share_atomic_budget(self):
        self.post.return_value = {"results": []}

        def worker(index):
            try:
                research.Run(self.directory).search(f"query {index}")
                return True
            except research.ResearchError:
                return False

        with ThreadPoolExecutor(max_workers=8) as pool:
            successful = list(pool.map(worker, range(20)))
        self.assertEqual(sum(successful), 2)
        self.assertEqual(self.post.call_count, 2)
        self.assertEqual(self.run.status()["budgets"]["search"]["used"], 2)

    def test_interrupted_pending_attempt_still_counts(self):
        self.run.reserve("exa", "search", {"query": "interrupted"}, "key")
        self.post.return_value = {"results": []}
        self.run.search("next")
        with self.assertRaisesRegex(research.ResearchError, "budget exhausted"):
            self.run.search("beyond cap")
        self.assertEqual(self.post.call_count, 1)

    def test_extension_preserves_history_and_cache(self):
        self.post.return_value = {"results": []}
        self.run.search("one")
        self.run.search("two")
        state = self.run.budget("User selected deeper research", depth="standard")
        self.assertEqual(state["budgets"]["search"], {"used": 2, "limit": 8, "remaining": 6})
        self.assertEqual(state["budget_history"][0]["old_config"]["depth"], "demo")
        self.assertEqual(state["collection_status"], "target_not_reached")
        self.assertTrue(self.run.search("one")["cached"])
        self.run.search("three")
        self.assertEqual(self.post.call_count, 3)
        with self.assertRaisesRegex(ValueError, "below"):
            self.run.budget("Too low", search_limit=1)

    def test_fresh_uses_budget_but_does_not_duplicate_source_count(self):
        self.post.return_value = {"content": "Evidence"}
        self.run.extract("https://example.org")
        self.run.extract("https://example.org", fresh=True)
        self.assertEqual(self.post.call_count, 2)
        self.assertEqual(self.run.status()["sources_retrieved"], 1)

    def test_existing_run_cannot_be_reset(self):
        with self.assertRaisesRegex(research.ResearchError, "Nothing was reset"):
            research.Run.create(self.directory, "other topic")
        self.assertEqual(self.run.status()["config"]["topic"], "Comparison topic")

    def test_secrets_not_written_to_ledger_or_source_files(self):
        self.post.return_value = {"content": "Echo fake-exa-secret fake-tabstack-secret"}
        source = self.run.extract("https://example.org")
        self.assertNotIn("fake-", Path(source["path"]).read_text())
        with self.run.connect() as db:
            dump = "\n".join(db.iterdump())
        self.assertNotIn("fake-exa-secret", dump)
        self.assertNotIn("fake-tabstack-secret", dump)

    def test_invalid_url_and_bad_budget_fail_before_network(self):
        for url in ("file:///etc/passwd", "https://user:secret@example.org"):
            with self.assertRaises(ValueError):
                self.run.extract(url)
        with self.assertRaises(ValueError):
            self.run.budget("Impossible target", source_target=100)
        self.post.assert_not_called()

    def test_multiround_collection_expands_beyond_demo_and_resumes(self):
        self.run.budget("User chose a larger investigation", search_limit=4, extract_limit=16, source_target=12)
        for round_number in range(3):
            # The agent selects a new coverage gap, then reads four new sources.
            self.post.return_value = {"results": [
                {"url": f"https://source-{round_number}-{index}.example/evidence"}
                for index in range(4)
            ]}
            resumed = research.Run(self.directory)
            candidates = resumed.search(f"coverage gap {round_number}")["candidates"]
            for candidate in candidates:
                self.post.return_value = {"content": f"Evidence from {candidate['url']}"}
                source = resumed.extract(candidate["url"])
                self.assertTrue(Path(source["path"]).is_file())
        state = research.Run(self.directory).status()
        self.assertEqual(state["sources_retrieved"], 12)
        self.assertEqual(state["collection_status"], "source_target_reached")
        self.assertEqual(state["budgets"]["search"]["used"], 3)
        self.assertEqual(state["budgets"]["extract"]["used"], 12)
        self.assertEqual(len(state["attempts"]), 15)
        self.assertIn("not necessarily analyzed", state["note"])


class HTTPTransportTests(unittest.TestCase):
    def test_fixed_endpoints_and_auth_headers(self):
        for provider, kind, expected_url, header, value in (
            ("exa", "search", "https://api.exa.ai/search", "X-api-key", "test-key"),
            ("exa", "extract", "https://api.exa.ai/contents", "X-api-key", "test-key"),
            ("tabstack", "extract", "https://api.tabstack.ai/v1/extract/markdown", "Authorization", "Bearer test-key"),
        ):
            with self.subTest(provider=provider, kind=kind), patch.object(research.request, "build_opener") as opener:
                opener.return_value.open.return_value = contextlib.closing(io.BytesIO(b'{"results": []}'))
                research.post_json(provider, kind, {"query": "test"}, "test-key")
                sent = opener.return_value.open.call_args.args[0]
                self.assertEqual(sent.full_url, expected_url)
                self.assertEqual(sent.get_header(header), value)
                self.assertEqual(json.loads(sent.data), {"query": "test"})
                self.assertEqual(sent.method, "POST")

    def test_invalid_json_is_a_reported_error(self):
        with patch.object(research.request, "build_opener") as opener:
            opener.return_value.open.return_value = contextlib.closing(io.BytesIO(b'not json'))
            with self.assertRaisesRegex(research.APIError, "invalid JSON"):
                research.post_json("exa", "search", {}, "test-key")

    def test_error_response_does_not_expose_body_or_credentials(self):
        with patch.object(research.request, "build_opener") as opener:
            opener.return_value.open.side_effect = error.HTTPError("https://api.exa.ai/search", 401, "secret", {}, io.BytesIO(b'secret'))
            with self.assertRaises(research.APIError) as raised:
                research.post_json("exa", "search", {}, "secret")
        self.assertEqual(str(raised.exception), "exa returned HTTP 401.")

    def test_redirects_are_rejected(self):
        self.assertIsNone(research.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.example"))


if __name__ == "__main__":
    unittest.main()
