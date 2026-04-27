from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

TOKEN_REGEX = re.compile(r"[a-zA-Z0-9_]+")


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_REGEX.findall(text)}


@dataclass(frozen=True)
class SkillRecord:
    skill_id: str
    title: str
    description: str
    workflow: dict
    keywords: tuple[str, ...]
    source_path: str

    def searchable_text(self) -> str:
        return f"{self.title}\n{self.description}\n{' '.join(self.keywords)}"


class DynamicSkillLibrary:
    def __init__(self, skill_dir: str | Path):
        self.skill_dir = Path(skill_dir)
        self.records: list[SkillRecord] = []
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self.skill_dir.exists():
            return

        for skill_path in sorted(self.skill_dir.glob("*.json")):
            try:
                with open(skill_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if not isinstance(payload, dict):
                    continue
                workflow = payload.get("workflow", {})
                if not isinstance(workflow, dict):
                    workflow = {}
                keywords = payload.get("keywords", [])
                if not isinstance(keywords, list):
                    keywords = []
                self.records.append(
                    SkillRecord(
                        skill_id=str(payload.get("skill_id", skill_path.stem)),
                        title=str(payload.get("title", skill_path.stem)),
                        description=str(payload.get("description", "")),
                        workflow=workflow,
                        keywords=tuple(str(keyword) for keyword in keywords),
                        source_path=str(skill_path),
                    )
                )
            except Exception:
                continue

    def retrieve(
        self, query: str, top_k: int = 3, min_score: float = 0.12
    ) -> list[tuple[SkillRecord, float]]:
        self.load()
        query_tokens = _tokenize(query)
        if not query_tokens or top_k <= 0 or not self.records:
            return []

        scored: list[tuple[SkillRecord, float]] = []
        for record in self.records:
            record_tokens = _tokenize(record.searchable_text())
            overlap = query_tokens.intersection(record_tokens)
            if not overlap:
                continue
            score = len(overlap) / max(1, len(query_tokens))
            if score < min_score:
                continue
            scored.append((record, score))
        scored.sort(key=lambda row: row[1], reverse=True)
        return scored[:top_k]
