"""Memory engine: ChromaDB (vector) + SQLite (relational).

3 layers:
- Working memory: in-RAM task context
- Episodic memory: ChromaDB collection "episodic"
- Semantic memory: ChromaDB collection "semantic"
- Procedural memory: SQLite table "skill_definitions"
- Approval history: ChromaDB collection "approval_history"
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from core.common.config import get_settings
from core.common.errors import MemoryError
from core.common.logging import get_logger

logger = get_logger(__name__)


class MemoryEngine:
    """Hierarchical memory management."""

    def __init__(self, chroma_path: str | None = None, database_url: str | None = None):
        self.settings = get_settings()
        self.chroma_path = Path(chroma_path or self.settings.chroma_path)
        self.database_url = database_url or self.settings.database_url

        self._chroma = None
        self._db_engine = None
        self._initialized = False

    async def initialize(self) -> None:
        """Lazy init: connect to ChromaDB and SQLite."""
        if self._initialized:
            return

        try:
            # ChromaDB
            import chromadb

            self.chroma_path.mkdir(parents=True, exist_ok=True)
            self._chroma = chromadb.PersistentClient(path=str(self.chroma_path))

            # Create collections if not exist
            for name in ["episodic", "semantic", "procedural", "approval_history"]:
                try:
                    self._chroma.get_collection(name=name)
                except Exception:
                    self._chroma.create_collection(
                        name=name,
                        metadata={"hnsw:space": "cosine"},
                    )

            # SQLite
            from sqlalchemy.ext.asyncio import create_async_engine

            if self.database_url.startswith("sqlite"):
                # Convert to aiosqlite for async
                url = self.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
                self._db_engine = create_async_engine(url, echo=False)
            else:
                self._db_engine = create_async_engine(self.database_url, echo=False)

            self._initialized = True
            logger.info("memory.initialized", chroma_path=str(self.chroma_path))

        except Exception as e:
            raise MemoryError(f"Failed to initialize memory: {e}") from e

    async def close(self) -> None:
        """Close connections."""
        if self._db_engine is not None:
            await self._db_engine.dispose()
            self._db_engine = None
        self._chroma = None
        self._initialized = False

    # === Episodic memory ===

    async def store_episode(
        self,
        task_id: str,
        user_id: str,
        task_type: str,
        domain: str,
        input_text: str,
        result_text: str,
        success: bool,
        confidence: float,
        tools_used: list[str] | None = None,
        duration_ms: int = 0,
    ) -> str:
        """Store an episode in long-term memory."""
        await self.initialize()
        coll = self._chroma.get_collection("episodic")
        episode_id = f"{user_id}:{task_id}"
        document = f"Input: {input_text}\n\nResult: {result_text}"
        # Truncate to avoid huge docs
        document = document[:2000]
        metadata = {
            "user_id": user_id,
            "task_id": task_id,
            "task_type": task_type,
            "domain": domain,
            "input_summary": input_text[:200],
            "result_summary": result_text[:200],
            "success": success,
            "duration_ms": duration_ms,
            "tools_used": ",".join(tools_used or []),
            "confidence": confidence,
            "date": datetime.utcnow().isoformat(),
        }
        coll.upsert(ids=[episode_id], documents=[document], metadatas=[metadata])
        logger.info("memory.episode_stored", episode_id=episode_id, task_id=task_id)
        return episode_id

    async def search_episodic(
        self,
        query: str,
        task_type: str | None = None,
        user_id: str | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Search episodic memory."""
        await self.initialize()
        coll = self._chroma.get_collection("episodic")
        where: dict[str, Any] = {}
        if task_type:
            where["task_type"] = task_type
        if user_id:
            where["user_id"] = user_id
        try:
            results = coll.query(
                query_texts=[query],
                n_results=top_k,
                where=where if where else None,
            )
            out: list[dict[str, Any]] = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"][0]):
                    out.append({
                        "id": doc_id,
                        "document": results["documents"][0][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "score": 1.0 - (results["distances"][0][i] if results.get("distances") else 0),
                    })
            return out
        except Exception as e:
            logger.warning("memory.search_episodic_error", error=str(e))
            return []

    async def get_task_history(
        self,
        task_type: str,
        domain: str,
        user_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get recent task history for familiarity scoring."""
        await self.initialize()
        coll = self._chroma.get_collection("episodic")
        try:
            results = coll.get(
                where={
                    "$and": [
                        {"task_type": task_type},
                        {"user_id": user_id},
                    ]
                },
                limit=limit,
            )
            out = []
            if results and results.get("metadatas"):
                for i, meta in enumerate(results["metadatas"]):
                    out.append({
                        "task_id": meta.get("task_id"),
                        "success": meta.get("success", False),
                        "confidence": meta.get("confidence", 0.0),
                        "date": meta.get("date"),
                    })
            return out
        except Exception as e:
            logger.warning("memory.get_history_error", error=str(e))
            return []

    # === Semantic memory ===

    async def store_rule(
        self,
        topic: str,
        rule: str,
        evidence_count: int = 1,
        confidence: float = 0.7,
    ) -> str:
        """Store a learned rule in semantic memory."""
        await self.initialize()
        coll = self._chroma.get_collection("semantic")
        rule_id = f"rule:{uuid.uuid4().hex[:12]}"
        metadata = {
            "topic": topic,
            "evidence_count": evidence_count,
            "confidence": confidence,
            "last_validated": datetime.utcnow().isoformat(),
        }
        coll.upsert(ids=[rule_id], documents=[rule], metadatas=[metadata])
        logger.info("memory.rule_stored", rule_id=rule_id, topic=topic)
        return rule_id

    async def search_semantic(
        self,
        query: str,
        top_k: int = 3,
        min_confidence: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Search semantic memory for relevant rules."""
        await self.initialize()
        coll = self._chroma.get_collection("semantic")
        try:
            results = coll.query(query_texts=[query], n_results=top_k)
            out = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"][0]):
                    meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                    if meta.get("confidence", 0) >= min_confidence:
                        out.append({
                            "id": doc_id,
                            "document": results["documents"][0][i] if results.get("documents") else "",
                            "metadata": meta,
                            "score": 1.0 - (results["distances"][0][i] if results.get("distances") else 0),
                        })
            return out
        except Exception as e:
            logger.warning("memory.search_semantic_error", error=str(e))
            return []

    # === Approval history ===

    async def store_approval(
        self,
        approval_id: str,
        task_id: str,
        user_id: str,
        task_type: str,
        domain: str,
        tool_name: str,
        risk_level: str,
        decision: str,
        modified: bool,
    ) -> str:
        """Store approval decision for future reference."""
        await self.initialize()
        coll = self._chroma.get_collection("approval_history")
        document = f"Task {task_id}: user {decision} tool {tool_name} (risk: {risk_level})"
        metadata = {
            "approval_id": approval_id,
            "task_id": task_id,
            "user_id": user_id,
            "task_type": task_type,
            "domain": domain,
            "tool_name": tool_name,
            "risk_level": risk_level,
            "decision": decision,
            "modified": modified,
            "date": datetime.utcnow().isoformat(),
        }
        coll.upsert(ids=[approval_id], documents=[document], metadatas=[metadata])
        return approval_id

    async def get_approval_precedents(
        self,
        tool_name: str,
        domain: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Get similar past approval decisions."""
        await self.initialize()
        coll = self._chroma.get_collection("approval_history")
        try:
            results = coll.query(
                query_texts=[f"tool {tool_name} domain {domain}"],
                n_results=top_k,
                where={"tool_name": tool_name} if tool_name else None,
            )
            out = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"][0]):
                    meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                    out.append({
                        "id": doc_id,
                        "metadata": meta,
                        "score": 1.0 - (results["distances"][0][i] if results.get("distances") else 0),
                    })
            return out
        except Exception as e:
            logger.warning("memory.precedents_error", error=str(e))
            return []
