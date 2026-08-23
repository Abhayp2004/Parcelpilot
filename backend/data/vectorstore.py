from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHROMA_DIR = PROJECT_ROOT / "chroma_db"
DEFAULT_MODEL_CACHE_DIR = PROJECT_ROOT / ".model_cache"


class VectorStore:
    def __init__(self, persist_directory: str | Path = DEFAULT_CHROMA_DIR):
        self.persist_directory = Path(persist_directory)
        if not self.persist_directory.is_absolute():
            self.persist_directory = PROJECT_ROOT / self.persist_directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        DEFAULT_MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        self.embedding_model = self._load_embedding_model()
        self.collection = self.client.get_or_create_collection(
            name="parcelpilot_docs",
            metadata={"hnsw:space": "cosine"}
        )

    def _load_embedding_model(self) -> SentenceTransformer:
        model_name = "all-MiniLM-L6-v2"
        cache_folder = str(DEFAULT_MODEL_CACHE_DIR)
        try:
            return SentenceTransformer(
                model_name,
                cache_folder=cache_folder,
                local_files_only=True,
            )
        except OSError:
            return SentenceTransformer(model_name, cache_folder=cache_folder)

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self.embedding_model.encode(texts, show_progress_bar=False).tolist()

    def ingest(self, chunks: List[Dict[str, Any]]) -> None:
        if not chunks:
            return

        texts = [chunk["text"] for chunk in chunks]
        metadatas = [
            {key: ("" if value is None else value) for key, value in chunk["metadata"].items()}
            for chunk in chunks
        ]
        ids = [f"{meta['source_file']}_chunk_{meta['chunk_index']}" for meta in metadatas]

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=self._get_embeddings(texts),
            metadatas=metadatas,
        )

    def search(
        self,
        query: str,
        k: int = 6,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_embeddings=[self._get_embeddings([query])[0]],
            n_results=k,
            where=filters,
            include=["documents", "metadatas", "distances"]
        )

        formatted_results = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for index, document in enumerate(documents):
            formatted_results.append(
                {
                    "text": document,
                    "metadata": metadatas[index],
                    "score": 1 - distances[index],
                }
            )

        return sorted(formatted_results, key=lambda item: item["score"], reverse=True)

    def get_by_source(self, source_file: str) -> List[Dict[str, Any]]:
        results = self.collection.get(
            where={"source_file": source_file},
            include=["documents", "metadatas"]
        )

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        return [
            {"text": documents[index], "metadata": metadatas[index]}
            for index in range(len(documents))
        ]

    def clear(self) -> None:
        try:
            self.client.delete_collection("parcelpilot_docs")
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name="parcelpilot_docs",
            metadata={"hnsw:space": "cosine"}
        )
