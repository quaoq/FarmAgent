from pathlib import Path
import json

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class RAG_PDF:
    """
    Simple PDF RAG Toolset to:
    * Build/load FAISS vectorstore from all PDFs under `rag_dir`
    * Expose `rag_search(query: str, k: int = 4)` as an agent tool
    """
    def __init__(self, rag_dir: Path):
        self.rag_dir = Path(rag_dir)
        self.vs = None
        self.index_dir = self.rag_dir / ".faiss_index"
        self._init_index()
        self.mode = "text-only"

    def _embedding_model(self):
        # NOTE: could expose as cfg value
        model = "text-embedding-3-small"
        return OpenAIEmbeddings(model=model)

    def _init_index(self):
        if not self.rag_dir.exists():
            raise RuntimeError(f"[RAG] Invalid PDF path: {self.rag_dir}")

        # Load if already built
        if self.index_dir.exists():
            try:
                self.vs = FAISS.load_local(
                    str(self.index_dir),
                    self._embedding_model(),
                    allow_dangerous_deserialization=True,
                )
                print(f"[RAG] Loaded FAISS index from {self.index_dir}.")
                return
            except Exception as e:
                print(f"[RAG] Failed to load existing index, rebuilding. Reason: {e}")

        pdf_files = sorted([p for p in self.rag_dir.glob("**/*.pdf") if p.is_file()])
        if not pdf_files:
            # Question: Should I error this out?
            print(f"[RAG] No PDFs in: {self.rag_dir}. Skipping...")
            return

        print(f"[RAG] Building Vectorstore with {len(pdf_files)} PDFs from {self.rag_dir}")
        all_docs = []
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

        for pdf in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf))
                docs = loader.load()
                docs = splitter.split_documents(docs)

                # Normalize source to be relative for cleaner traces
                for d in docs:
                    src = d.metadata.get("source", str(pdf))
                    try:
                        d.metadata["source"] = str(Path(src).resolve().relative_to(self.rag_dir.resolve()))
                    except Exception:
                        d.metadata["source"] = src

                all_docs.extend(docs)
            except Exception as e:
                print(f"[RAG] Failed to load {pdf}: {e}")

        if not all_docs:
            # Question: Should I error this out?
            print("[RAG] No chunks produced. Skipping...")
            return

        self.vs = FAISS.from_documents(all_docs, self._embedding_model())
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.vs.save_local(str(self.index_dir))
        print(f"[RAG] FAISS vectorstore saved to {self.index_dir}.")

    def rag_search(self, query: str, k: int = 10) -> str:
        """
        Retrieve top-k RAG matches.
        """
        if self.vs is None:
            raise RuntimeError(f"No vectorstore found! Set PDF directory properly and retry!")

        matches = self.vs.similarity_search_with_score(query, k=k)
        out = []
        for match, score in matches:
            if self.mode == "text-only":
                out.append(match.page_content.strip())
            else:
                out.append({
                    "source": match.metadata.get("source", "unknown.pdf"),
                    "page": match.metadata.get("page", "unknown"),
                    "score": float(score),
                    "text": match.page_content.strip(),
                })

        if self.mode == "text-only":
            return '\n'.join(out)
        else:
            return json.dumps({"ok": True, "query": query, "k": k, "hits": out}, indent=2)

