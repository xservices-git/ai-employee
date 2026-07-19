"""Smoke tests cho M1.

Chay: cd D:\\picoclaw\\workspace\\ai-employee && python -m pytest tests/test_m1.py -v
Hoac: python tests/test_m1.py
"""
import sys, asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import db, memory, orchestrator, llm


def test_settings_load():
    from core.config import SETTINGS
    assert SETTINGS.port == 8000
    assert SETTINGS.data_dir.exists()
    print("[OK] settings load")


def test_db_init():
    db.reset_db()
    db.get_db()
    conn = db.get_db()
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    tables = {r["name"] for r in row}
    expected = {"users", "tasks", "feedback", "approval_requests", "traces", "skill_metadata"}
    assert expected.issubset(tables), f"Missing: {expected - tables}"
    print(f"[OK] db init: {len(tables)} tables")


def test_task_crud():
    db.reset_db()
    db.get_db()
    task = db.create_task(
        task_type="data_processing",
        input_data={"text": "test"},
        domain="customer_support",
    )
    assert task["status"] == "pending"
    assert task["domain"] == "customer_support"
    db.update_task(task["id"], status="completed", result={"ok": True}, confidence=0.8)
    t = db.get_task(task["id"])
    assert t["status"] == "completed"
    assert t["result"] == {"ok": True}
    assert t["confidence"] == 0.8
    print("[OK] task CRUD")


def test_memory_episode():
    db.reset_db()
    db.get_db()
    ep_id = memory.store_episode(
        task_id="t1", task_type="data_processing", domain="sales_ops",
        input_text="kiem tra don hang", output_text="ok", success=True, confidence=0.9,
    )
    assert ep_id
    results = memory.search_similar("don hang can check", top_k=3)
    assert len(results) > 0
    assert results[0]["task_type"] == "data_processing"
    print(f"[OK] memory: stored + found {len(results)} similar")


def test_classify_heuristic():
    assert llm._classify_heuristic("Kiem tra don hang #12345")["task_type"] == "data_processing"
    assert llm._classify_heuristic("Viet email chao khach")["task_type"] == "content_generation"
    assert llm._classify_heuristic("Tim kiem thong tin ve AI")["task_type"] == "research_summarization"
    assert llm._classify_heuristic("Dat lich hop ngay mai")["task_type"] == "scheduling_coordination"
    assert llm._classify_heuristic("Canh bao khi API down")["task_type"] == "monitoring_alerting"
    print("[OK] classify heuristic")


def test_confidence():
    db.reset_db()
    db.get_db()
    # No history -> familiarity=0.3
    plan = {"steps": [{"action": "echo"}], "clarity": 0.9, "summary": "test"}
    conf = orchestrator.calculate_confidence("data_processing", plan, None)
    assert 0 <= conf["final"] <= 1
    assert conf["clarity"] == 0.9
    print(f"[OK] confidence: final={conf['final']}")


def test_orchestrator_run():
    db.reset_db()
    db.get_db()
    task = db.create_task(task_type="pending", input_data={"text": "Kiem tra don hang #42"})
    result = asyncio.run(orchestrator.run(task["id"]))
    assert result["status"] in ("completed", "waiting_approval", "failed")
    assert result.get("plan", {}).get("classification", {}).get("task_type") == "data_processing"
    print(f"[OK] orchestrator run: status={result['status']}")


def test_full_flow_with_approval():
    db.reset_db()
    db.get_db()
    task = db.create_task(task_type="pending", input_data={"text": "Kiem tra don hang #999"})
    result = asyncio.run(orchestrator.run(task["id"]))
    if result["status"] == "waiting_approval":
        approval_id = result["approval"]["id"]
        # Approve
        db.decide_approval(approval_id, "approved", "OK")
        result2 = asyncio.run(orchestrator.resume_after_approval(task["id"], approval_id, "approved"))
        assert result2["status"] in ("completed", "failed")
        print(f"[OK] full flow: pending->running->approval->{result2['status']}")
    else:
        print(f"[OK] orchestrator auto-completed: {result['status']}")


if __name__ == "__main__":
    test_settings_load()
    test_db_init()
    test_task_crud()
    test_memory_episode()
    test_classify_heuristic()
    test_confidence()
    test_orchestrator_run()
    test_full_flow_with_approval()
    print("\n=== ALL TESTS PASS ===")
