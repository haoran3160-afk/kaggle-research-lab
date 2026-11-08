"""A human-readable work record for a host agent. Never executes tools or models.

Use one host writer per JSON file. Atomic replacement prevents truncated records;
it is not concurrent-writer coordination or proof that recorded claims are true.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import tempfile


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def action(value):
    if value is None:
        return None
    if not isinstance(value, dict) or not value.get("id") or value.get("kind", "cpu") not in {"cpu", "remote", "monitor"}:
        raise ValueError("action needs a readable id and kind cpu/remote/monitor")
    if not value.get("command") and not value.get("instruction"):
        raise ValueError("action needs an actual command or concrete host instruction")
    if value.get("command") and not value.get("cwd"):
        raise ValueError("a command needs its working directory")
    if value.get("kind") in {"remote", "monitor"} and not value.get("remote_id"):
        raise ValueError("remote/monitor action needs a stable human-readable remote_id")
    return dict(value, kind=value.get("kind", "cpu"), status="planned")


class Workspace:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        value = read_json(self.path)
        if not isinstance(value, dict) or value.get("version") != 2:
            raise ValueError("not a v2 workspace record")
        return value

    def save(self, value):
        value["updated_at"] = utcnow()
        encoded = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=self.path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def init(self, goal, competition=""):
        if not goal or not goal.strip():
            raise ValueError("goal is required")
        if self.path.exists():
            raise ValueError("workspace already exists; read status instead of overwriting")
        value = {"version": 2, "competition": competition, "goal": goal, "champion": None,
                 "next_action": None, "experiments": [], "remote_jobs": {}, "budget": {},
                 "learning": {"state": "pending", "weekly_hours": 5}}
        self.save(value)
        return self.status()

    @staticmethod
    def run_note(value, task):
        if not task or task.get("status") == "finished":
            return "No ready action; host chooses the next useful step from results."
        if task["kind"] == "remote":
            job = value["remote_jobs"].get(task["remote_id"])
            if job and job["state"] != "no_write":
                return "Do not resend this remote operation. Read its actual provider state; monitor or record positive no-write evidence."
            if task.get("status") == "started":
                return "Remote action already started; reconcile before considering another write."
        return "Host performs this action using actual tools, then records observations."

    def status(self):
        value = self.load()
        return {key: value[key] for key in ("competition", "goal", "champion", "next_action", "remote_jobs", "budget", "learning")} | {
            "recent_experiments": value["experiments"][-5:], "note": self.run_note(value, value["next_action"]),
            "legacy_pending": value.get("legacy", {}).get("tasks", [])}

    def next(self, proposed=None):
        value = self.load()
        if proposed is not None:
            proposed = action(proposed)
            current = value["next_action"]
            if current and current.get("status") == "started" and current["kind"] == "remote":
                # The job remains in remote_jobs when the host moves to CPU work.
                if proposed["id"] == current["id"] and proposed["kind"] == "remote":
                    raise ValueError("remote action already started; record its actual state instead of resetting it")
            value["next_action"] = proposed
            self.save(value)
        return {"next_action": value["next_action"], "note": self.run_note(value, value["next_action"])}

    def start(self, task_id):
        value = self.load()
        task = value["next_action"]
        if not task or task["id"] != task_id or task.get("status") != "planned":
            raise ValueError("start must name the currently planned action")
        if task["kind"] == "remote":
            previous = value["remote_jobs"].get(task["remote_id"])
            if previous and previous["state"] != "no_write":
                raise ValueError("remote operation may already exist; inspect it instead of resending")
            value["remote_jobs"][task["remote_id"]] = {"state": "uncertain", "action_id": task_id,
                "action": dict(task, status="started"),
                "observation": "Host is starting this write; no provider acknowledgement recorded yet.",
                "previous_observation": previous, "updated_at": utcnow()}
        task["status"] = "started"
        self.save(value)
        return {"action": task, "note": "Record saved. Host now performs the bounded action once; this script executed nothing."}

    def record(self, result):
        if not isinstance(result, dict) or not result.get("outcome"):
            raise ValueError("result needs an observed outcome")
        value = self.load()
        task = value["next_action"]
        delayed = bool(task and result.get("action_id") and result["action_id"] != task["id"])
        remote = result.get("remote")
        if remote is not None:
            states = {"uncertain", "submitted", "running", "completed", "failed", "cancelled", "no_write"}
            if not isinstance(remote, dict) or not remote.get("id") or remote.get("state") not in states or not remote.get("observation"):
                raise ValueError("remote observation needs id, state and actual observation/source")
            old = value["remote_jobs"].get(remote["id"], {})
            value["remote_jobs"][remote["id"]] = dict(old, **{k: v for k, v in remote.items() if k != "id"}, updated_at=utcnow())
        adoption = result.get("adopt")
        if adoption is not None and not delayed:
            if not isinstance(adoption, dict) or not adoption.get("candidate") or adoption.get("basis") not in {"quality", "cost", "equivalence"} or not adoption.get("measurement") or not adoption.get("evidence"):
                raise ValueError("adoption needs candidate, quality/cost/equivalence measurement and real result evidence; passing tests alone is not adoption")
            value["champion"] = dict(adoption, recorded_at=utcnow())
        for key in ("budget", "learning"):
            if key in result:
                if not isinstance(result[key], dict):
                    raise ValueError(key + " must be a readable object")
                if not delayed:
                    value[key].update(result[key])
        if result.get("action_id") and task and result["action_id"] == task["id"]:
            task["status"] = "finished"
        if "next_action" in result and not delayed:
            value["next_action"] = action(result["next_action"])
        entry = dict(result, id=result.get("id", "experiment-" + str(len(value["experiments"]) + 1)), recorded_at=utcnow())
        if delayed:
            for key in ("budget", "learning"):
                if key in entry:
                    entry["proposed_" + key] = entry.pop(key)
            if "next_action" in entry:
                entry["proposed_next"] = entry.pop("next_action")
            if "adopt" in entry:
                entry["proposed_adopt"] = entry.pop("adopt")
        value["experiments"].append(entry)
        self.save(value)
        return self.status()

    def migrate_legacy(self, database, competition, goal=None):
        """Read old task/remote evidence without importing its framework or changing it."""
        path = Path(database).resolve()
        if not path.is_file():
            raise ValueError("legacy SQLite file does not exist")
        connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            tasks = []
            for row in connection.execute("SELECT * FROM tasks WHERE competition=? AND state NOT IN ('done','failed') ORDER BY id", (competition,)):
                spec = json.loads(row["spec"])
                tasks.append({"id": "legacy-task-" + str(row["id"]), "state": row["state"], "action": spec.get("action"),
                              "identity": spec.get("identity"), "result": json.loads(row["result"]) if row["result"] else None})
            jobs = {}
            for row in connection.execute("SELECT i.* FROM intents i JOIN tasks t ON t.id=i.task WHERE t.competition=? AND t.state NOT IN ('done','failed') AND i.state IN ('prepared','unknown','confirmed')", (competition,)):
                jobs["legacy-intent-" + str(row["id"])] = {"state": "uncertain" if row["state"] in {"prepared", "unknown"} else "submitted",
                    "operation": json.loads(row["operation"]), "provider_observation": json.loads(row["receipt"]) if row["receipt"] else None,
                    "observation": "Imported historical evidence; read the actual provider state before any write."}
            tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            obligations = [dict(r) for r in connection.execute("SELECT * FROM charges WHERE state NOT IN ('released','settled')")] if "charges" in tables else []
        finally:
            connection.close()
        if not self.path.exists():
            if not goal:
                raise ValueError("supply --goal when creating a workspace from legacy state")
            self.init(goal, competition)
        value = self.load()
        if value["competition"] and value["competition"] != competition:
            raise ValueError("legacy competition does not match this workspace")
        value["legacy"] = {"database": str(path), "tasks": tasks, "note": "Historical evidence only; no old job is automatically dispatched."}
        for key, job in jobs.items():
            value["remote_jobs"].setdefault(key, job)
        value["budget"]["legacy_unresolved_obligations"] = obligations
        self.save(value)
        return self.status()


def compact_status(value):
    """CLI continuation view; full status records and stored state stay intact."""
    current_remote = (value["next_action"] or {}).get("remote_id")
    terminal = {"completed", "failed", "cancelled"}
    fields = ("id", "action_id", "recorded_at", "outcome", "decision", "evidence")
    view = {key: item for key, item in value.items() if key != "legacy_pending"}
    view["remote_jobs"] = {
        identity: job for identity, job in value["remote_jobs"].items()
        if identity == current_remote or not isinstance(job, dict) or job.get("state") not in terminal
    }
    view["recent_experiments"] = [
        {key: entry[key] for key in fields if key in entry}
        for entry in value["recent_experiments"]
    ]
    return view


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("init"); p.add_argument("--goal", required=True); p.add_argument("--competition", default="")
    p = commands.add_parser("status"); p.add_argument("--full", action="store_true", help="Show the original complete status view")
    p = commands.add_parser("next"); p.add_argument("--action", help="JSON action file; omit to read the next action")
    p = commands.add_parser("start"); p.add_argument("--id", required=True)
    p = commands.add_parser("record"); p.add_argument("--result", required=True)
    p = commands.add_parser("migrate-legacy"); p.add_argument("--db", required=True); p.add_argument("--competition", required=True); p.add_argument("--goal")
    args = parser.parse_args(argv)
    workspace = Workspace(args.file)
    try:
        if args.command == "init": result = workspace.init(args.goal, args.competition)
        elif args.command == "status":
            result = workspace.status()
            if not args.full:
                result = compact_status(result)
        elif args.command == "next": result = workspace.next(read_json(args.action) if args.action else None)
        elif args.command == "start": result = workspace.start(args.id)
        elif args.command == "record": result = workspace.record(read_json(args.result))
        else: result = workspace.migrate_legacy(args.db, args.competition, args.goal)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
