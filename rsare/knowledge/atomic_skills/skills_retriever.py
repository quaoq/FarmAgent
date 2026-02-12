import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np

from sentence_transformers import SentenceTransformer
from openai import OpenAI


# -----------------------------
# Data model
# -----------------------------
@dataclass(frozen=True)
class SkillRecord:
    skill_id: str
    title: str
    description: str
    workflow: Dict[str, Any]
    source_path: str
    keywords: Tuple[str, ...] = ()

    def to_text_for_embedding(self) -> str:
        """
        What we embed for similarity search.
        Keep it short-ish but informative: title + keywords + description.
        """
        kw = ", ".join(self.keywords) if self.keywords else ""
        parts = [
            f"Skill: {self.title}".strip(),
            f"Keywords: {kw}".strip() if kw else "",
            self.description.strip(),
        ]
        return "\n".join([p for p in parts if p])


# -----------------------------
# Utilities
# -----------------------------
def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom else 0.0


def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v if n == 0 else (v / n)


def _is_e5_model(model_name: str) -> bool:
    # E5 models typically benefit from query/passsage prefixes.
    # Not strictly required, but improves retrieval quality.
    return "e5-" in model_name or model_name.startswith("intfloat/e5")


def _format_e5_query(text: str) -> str:
    return f"query: {text.strip()}"


def _format_e5_passage(text: str) -> str:
    return f"passage: {text.strip()}"


# -----------------------------
# Loading skills
# -----------------------------
def load_skill_records(skill_dir: str | Path) -> List[SkillRecord]:
    """
    Load skills from a directory of JSON files.

    Expected JSON shape per file (minimal):
    {
      "skill_id": "cfar_vessel_detection_v1",
      "title": "Vessel detection (CFAR) + tile extraction + presence/length estimation",
      "description": "...",
      "keywords": ["SAR", "Sentinel-1", "CFAR", "VH", "VV", "tile", "vessel length"],
      "workflow": { ... }   # your oracle step dict
    }
    """
    skill_dir = Path(skill_dir)
    if not skill_dir.exists():
        raise FileNotFoundError(f"Skill directory not found: {skill_dir}")
    if not skill_dir.is_dir():
        raise ValueError(f"skill_dir must be a directory: {skill_dir}")

    records: List[SkillRecord] = []
    for p in sorted(skill_dir.glob("*.json")):
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            continue

        skill_id = str(data.get("skill_id") or p.stem)
        title = str(data.get("title") or skill_id)
        description = str(data.get("description") or data.get("Task description") or "")
        workflow = data.get("workflow") or data.get("Example workflow") or {}

        if not isinstance(workflow, dict):
            # Keep the workflow intact, but require a dict for now.
            # If you prefer list workflows, we can support both.
            continue

        keywords = data.get("keywords") or ()
        if isinstance(keywords, list):
            keywords = tuple(str(x) for x in keywords)
        else:
            keywords = tuple()

        records.append(
            SkillRecord(
                skill_id=skill_id,
                title=title,
                description=description,
                workflow=workflow,
                source_path=str(p),
                keywords=keywords,
            )
        )

    if not records:
        raise ValueError(f"No valid skill JSON files found under: {skill_dir}")
    return records


# -----------------------------
# Embedding backends
# -----------------------------
class Embedder:
    def embed(self, texts: Sequence[str]) -> List[np.ndarray]:
        raise NotImplementedError


class SentenceTransformersEmbedder(Embedder):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: Sequence[str]) -> List[np.ndarray]:
        # We normalize ourselves to keep consistent with OpenAI embeddings.
        embs = self.model.encode(list(texts), normalize_embeddings=False)
        arr = np.asarray(embs, dtype=np.float32)
        return [_normalize(arr[i]) for i in range(arr.shape[0])]


class OpenAIEmbedder(Embedder):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "text-embedding-3-small"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI embeddings")
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def embed(self, texts: Sequence[str]) -> List[np.ndarray]:
        resp = self.client.embeddings.create(model=self.model_name, input=list(texts))
        out: List[np.ndarray] = []
        for d in resp.data:
            v = np.asarray(d.embedding, dtype=np.float32)
            out.append(_normalize(v))
        return out


# -----------------------------
# Skill index with caching
# -----------------------------
class SkillIndex:
    """
    Similarity-search index over SkillRecord items.

    - Builds embeddings for each skill (title/keywords/description)
    - Caches embeddings on disk
    - Supports top-k retrieval with cosine similarity
    - Provides search_text() to directly append retrieved skills into prompts
    """

    def __init__(
        self,
        skill_dir: str | Path,
        mode: str = "openai",
        embed_model: str = "text-embedding-3-small",
        openai_api_key: Optional[str] = None,
        cache_dir: str | Path | None = None,
    ):
        self.skill_dir = Path(skill_dir)
        self.mode = mode.strip().lower()
        self.embed_model = embed_model
        self.openai_api_key = openai_api_key

        if self.mode not in {"local", "openai"}:
            raise ValueError("mode must be 'local' or 'openai'")

        self.cache_dir = Path(cache_dir) if cache_dir else (self.skill_dir / ".skill_index_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._records: List[SkillRecord] = []
        self._embeddings: Optional[np.ndarray] = None  # shape: (N, D)
        self._embedder: Optional[Embedder] = None


    def ensure_built(self) -> None:
        """Build index if not built yet (safe no-op if already built)."""
        if self._embeddings is None or not self._records:
            self.build(force_rebuild=False)


    def _get_embedder(self) -> Embedder:
        if self._embedder is not None:
            return self._embedder
        if self.mode == "local":
            self._embedder = SentenceTransformersEmbedder(self.embed_model)
        else:
            self._embedder = OpenAIEmbedder(api_key=self.openai_api_key, model_name=self.embed_model)
        return self._embedder

    def _cache_paths(self) -> Tuple[Path, Path]:
        meta_path = self.cache_dir / "meta.json"
        vecs_path = self.cache_dir / "embeddings.npy"
        return meta_path, vecs_path

    def _fingerprint(self, files: List[Path]) -> Dict[str, Any]:
        """
        Cache invalidation fingerprint: list file names + mtimes + embed settings.
        """
        return {
            "mode": self.mode,
            "embed_model": self.embed_model,
            "files": [
                {"name": f.name, "mtime": f.stat().st_mtime_ns, "size": f.stat().st_size}
                for f in files
            ],
        }

    def build(self, force_rebuild: bool = False) -> None:
        """
        Load skill JSONs and build (or load) embeddings.
        """
        json_files = sorted(self.skill_dir.glob("*.json"))
        if not json_files:
            raise ValueError(f"No *.json found in skill_dir: {self.skill_dir}")

        meta_path, vecs_path = self._cache_paths()
        fp = self._fingerprint(json_files)

        if not force_rebuild and meta_path.exists() and vecs_path.exists():
            try:
                cached_meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if cached_meta == fp:
                    self._records = load_skill_records(self.skill_dir)
                    self._embeddings = np.load(vecs_path).astype(np.float32)
                    if self._embeddings.shape[0] != len(self._records):
                        # fall back to rebuild if mismatch
                        self._records = []
                        self._embeddings = None
                    else:
                        return
            except Exception:
                # rebuild on any cache read error
                pass

        # Rebuild
        self._records = load_skill_records(self.skill_dir)

        embedder = self._get_embedder()
        texts: List[str] = []
        for rec in self._records:
            t = rec.to_text_for_embedding()
            # Apply E5 formatting if using E5 locally
            if self.mode == "local" and _is_e5_model(self.embed_model):
                t = _format_e5_passage(t)
            texts.append(t)

        vecs = embedder.embed(texts)
        mat = np.stack(vecs, axis=0).astype(np.float32)  # (N, D)

        np.save(vecs_path, mat)
        meta_path.write_text(json.dumps(fp, indent=2), encoding="utf-8")

        self._embeddings = mat

    @property
    def records(self) -> List[SkillRecord]:
        return list(self._records)

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        k: Optional[int] = None,
    ) -> List[Tuple[SkillRecord, float]]:
        """
        Return top_k (record, score) sorted by cosine similarity.

        Args:
            query: user query
            top_k: number of results (preferred name)
            k: alias for top_k
        """
        self.ensure_built()

        if top_k is None:
            top_k = k if k is not None else 5
        if top_k <= 0:
            return []

        embedder = self._get_embedder()
        q = query.strip()
        if self.mode == "local" and _is_e5_model(self.embed_model):
            q = _format_e5_query(q)

        q_vec = embedder.embed([q])[0]  # normalized
        scores = (self._embeddings @ q_vec).astype(float)  # cosine since normalized
        ranked = np.argsort(-scores)[:top_k]
        return [(self._records[i], float(scores[i])) for i in ranked]


    def search_text(
        self,
        query: str,
        top_k: Optional[int] = None,
        k: Optional[int] = None,
        include_workflow: bool = True,
        include_description: bool = True,
        include_keywords: bool = True,
        max_workflow_chars: int = 4000,
        max_total_chars: int = 20000,
        header: str = "RETRIEVED ATOMIC SKILLS (evidence to follow exactly):",
    ) -> str:
        """
        Return a single string containing the top-k matched skills,
        formatted for direct inclusion in an LLM prompt.

        This is what you append into SCENARIO_INPUT.

        Notes:
          - max_workflow_chars truncates per-skill workflow JSON.
          - max_total_chars truncates the overall blob to avoid context bloat.
        """
        matches = self.search(query=query, top_k=top_k, k=k)

        lines: List[str] = []
        lines.append(header)
        lines.append("")

        used = 0
        for rank, (rec, score) in enumerate(matches, start=1):
            kw = ", ".join(rec.keywords) if (include_keywords and rec.keywords) else ""
            block_lines: List[str] = []

            block_lines.append(f"[SKILL #{rank}] score={score:.4f}")
            block_lines.append(f"skill_id: {rec.skill_id}")
            block_lines.append(f"title: {rec.title}")
            if kw:
                block_lines.append(f"keywords: {kw}")

            if include_description and rec.description.strip():
                block_lines.append("")
                block_lines.append("description:")
                block_lines.append(rec.description.strip())

            if include_workflow and isinstance(rec.workflow, dict) and rec.workflow:
                wf_str = json.dumps(rec.workflow, indent=2, ensure_ascii=False)
                if max_workflow_chars > 0 and len(wf_str) > max_workflow_chars:
                    wf_str = wf_str[:max_workflow_chars].rstrip() + "\n... (truncated)"
                block_lines.append("")
                block_lines.append("workflow_json:")
                block_lines.append(wf_str)

            block_lines.append("")  # blank line between skills

            block = "\n".join(block_lines)

            # enforce global size cap
            if max_total_chars > 0:
                if used + len(block) > max_total_chars:
                    remaining = max_total_chars - used
                    if remaining > 0:
                        lines.append(block[:remaining].rstrip() + "\n... (truncated)")
                    break

            lines.append(block)
            used += len(block)

        return "\n".join(lines).strip() + "\n"