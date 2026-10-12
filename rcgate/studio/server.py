"""Local JSON API for the research studio. Binds to localhost and does not call providers."""

from __future__ import annotations

import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from ..demo.fixtures import RESEARCH
from .catalog import Catalog
from .scoring import StudioScorer, local_weights_present

_STATE: dict | None = None
_STATE_LOCK = threading.Lock()


def get_state(cache_dir=None) -> dict:
    global _STATE
    with _STATE_LOCK:
        if _STATE is None:
            catalog = Catalog.load()
            scorer = StudioScorer(catalog, cache_dir=cache_dir)
            _STATE = {"catalog": catalog, "scorer": scorer, "jobs": {}, "jobs_lock": threading.Lock()}
        return _STATE


class StudioServer(ThreadingHTTPServer):
    def __init__(self, address, handler, state):
        super().__init__(address, handler)
        self.state = state


def make_handler(state: dict):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args) -> None:
            return

        def do_GET(self) -> None:  # noqa: N802
            self._route("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._route("POST")

        def _route(self, method: str) -> None:
            try:
                parsed = urlparse(self.path)
                parts = [part for part in parsed.path.split("/") if part]
                query = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
                if parts[:1] != ["api"]:
                    self._send(404, {"error": "not found"})
                    return
                self._dispatch(method, parts[1:], query)
            except Exception as exc:
                self._send(500, {"error": f"{type(exc).__name__}: {exc}"})

        def _dispatch(self, method: str, parts: list[str], query: dict) -> None:
            catalog: Catalog = state["catalog"]
            scorer: StudioScorer = state["scorer"]
            if parts == ["health"] and method == "GET":
                self._send(200, _health(catalog, scorer))
                return
            if parts == ["meta"] and method == "GET":
                self._send(200, {"research": dict(RESEARCH), "playback_label": "Recorded demo · stored RAGTruth responses"})
                return
            if parts == ["library"] and method == "GET":
                self._send(200, _library(catalog, scorer, query))
                return
            if len(parts) == 2 and parts[0] == "library" and method == "GET":
                record = catalog.record(
                    parts[1],
                    checkpoint_ready=scorer.checkpoint_ready,
                    local_ready=scorer.local_ready,
                )
                if record is None:
                    self._send(404, {"error": f"unknown source {parts[1]}"})
                    return
                self._send(200, record)
                return
            if parts == ["score"] and method == "POST":
                self._score()
                return
            if len(parts) == 2 and parts[0] == "jobs" and method == "GET":
                with state["jobs_lock"]:
                    job = state["jobs"].get(parts[1])
                if job is None:
                    self._send(404, {"error": "unknown job"})
                    return
                self._send(200, job)
                return
            self._send(404, {"error": "not found"})

        def _score(self) -> None:
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length > 20_000:
                self._send(413, {"error": "body too large"})
                return
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                self._send(400, {"error": "score body must be JSON"})
                return
            source_id = str(body.get("source_id") or "")
            response_id = str(body.get("response_id") or "")
            if "sentence_index" not in body:
                self._send(400, {"error": "sentence_index is required"})
                return
            try:
                sentence_index = int(body["sentence_index"])
            except (TypeError, ValueError):
                self._send(400, {"error": "sentence_index must be an integer"})
                return
            scorer: StudioScorer = state["scorer"]
            catalog: Catalog = state["catalog"]
            row = catalog.precomputed_rows.get(f"{response_id}#{sentence_index}")
            fast = row is not None and str(row.get("question_id")) == source_id
            if fast or _cache_ready(scorer, source_id, response_id, sentence_index):
                result = scorer.score(source_id, response_id, sentence_index)
                self._send(200, {"job_id": None, "status": result["status"], "message": result["reason"], "result": result})
                return
            job_id = uuid.uuid4().hex
            job = {"job_id": job_id, "status": "running", "message": "Preparing the stored record", "result": None}
            with state["jobs_lock"]:
                state["jobs"][job_id] = job

            def run() -> None:
                def progress(message: str) -> None:
                    with state["jobs_lock"]:
                        current = state["jobs"].get(job_id)
                        if current and current["status"] == "running":
                            current["message"] = message

                result = scorer.score(source_id, response_id, sentence_index, progress=progress)
                with state["jobs_lock"]:
                    state["jobs"][job_id] = {
                        "job_id": job_id,
                        "status": result["status"],
                        "message": result["reason"] or result["feature_source"],
                        "result": result,
                    }

            threading.Thread(target=run, daemon=True).start()
            self._send(202, job)

        def _send(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    return Handler


def _health(catalog: Catalog, scorer: StudioScorer) -> dict:
    return {
        "ok": all(item["match"] for item in catalog.file_hashes.values()),
        "live_provider_calls": False,
        "inventory": catalog.inventory(
            checkpoint_ready=scorer.checkpoint_ready,
            local_ready=scorer.local_ready,
        ),
        "local_weights_present": local_weights_present(),
        "checkpoint_ready": scorer.checkpoint_ready,
        "local_extraction_ready": scorer.local_ready,
        "load_error": scorer.load_error,
    }


def _library(catalog: Catalog, scorer: StudioScorer, query: dict) -> dict:
    def optional_int(name: str, default: int) -> int:
        raw = query.get(name)
        if raw in (None, ""):
            return default
        return int(raw)

    return catalog.search(
        q=query.get("q", ""),
        task=query.get("task", ""),
        topic=query.get("topic", ""),
        generator=query.get("generator", ""),
        score=query.get("score", ""),
        sort=query.get("sort", "auto"),
        page=optional_int("page", 1),
        page_size=optional_int("page_size", 20),
        checkpoint_ready=scorer.checkpoint_ready,
        local_ready=scorer.local_ready,
    )


def _cache_ready(scorer: StudioScorer, source_id: str, response_id: str, sentence_index: int) -> bool:
    if not scorer.checkpoint_path.is_file():
        return True
    try:
        prepared = scorer.catalog.prepare(source_id, response_id, sentence_index)
    except (KeyError, IndexError, RuntimeError):
        return True
    return scorer._cache_path(prepared).is_file()


def serve(host: str = "127.0.0.1", port: int = 8765, state: dict | None = None) -> StudioServer:
    bound = state or get_state()
    httpd = StudioServer((host, port), make_handler(bound), bound)
    return httpd


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m rcgate.studio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    httpd = serve(args.host, args.port)
    print(f"RC-Gate studio API at http://{args.host}:{httpd.server_address[1]}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0
