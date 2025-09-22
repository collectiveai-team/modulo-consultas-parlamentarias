import os
from functools import lru_cache
from typing import Literal
from uuid import uuid4

from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain.vectorstores.base import VectorStoreRetriever
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from pydantic import BaseModel, NonNegativeFloat, NonNegativeInt, StrictStr
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, SparseVectorParams, VectorParams

from modulo_consultas_parlamentarias.logger import get_logger

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_GRPC_PORT = int(os.getenv("QDRANT_GRPC_PORT", "6334"))

DENSE_EMBED_DOC_CACHE_PATH = os.getenv("DENSE_EMBED_DOC_CACHE_PATH")
DENSE_EMBED_QUERY_CACHE_PATH = os.getenv("DENSE_EMBED_QUERY_CACHE_PATH")
FAST_EMBED_SPARSE_CACHE = os.getenv("FAST_EMBED_SPARSE_CACHE")


logger = get_logger(__name__)


class TextChunk(BaseModel):
    text: StrictStr
    metadata: dict
    # num_tokens: NonNegativeInt


class RetrieverItem(BaseModel):
    text: StrictStr
    metadata: dict
    score: NonNegativeFloat | None = None


class Retriever:
    def __init__(
        self,
        dense_embeddings: Embeddings,
        dense_embed_doc_cache_path: str | None = DENSE_EMBED_DOC_CACHE_PATH,
        dense_embed_query_cache_path: str | None = DENSE_EMBED_QUERY_CACHE_PATH,
        sparse_embed_model_name: str = "Qdrant/bm25",
    ):
        assert dense_embeddings.dimensions is not None, (  # type: ignore
            "Expected 'dense_embeddings.dimensions' to be set."
        )

        assert dense_embeddings.model is not None, (  # type: ignore
            "Expected 'dense_embeddings.model' to be set."
        )

        self.dense_embed_dimensions = dense_embeddings.dimensions
        self.dense_embeddings = self._get_dense_embeddings(
            dense_embeddings=dense_embeddings,
            dense_embed_doc_cache_path=dense_embed_doc_cache_path,
            dense_embed_query_cache_path=dense_embed_query_cache_path,
        )

        self.sparse_embeddings = FastEmbedSparse(
            model_name=sparse_embed_model_name,
            cache_dir=FAST_EMBED_SPARSE_CACHE,
        )

        self.qadrant_client = QdrantClient(
            url=QDRANT_HOST,
            port=QDRANT_PORT,
            grpc_port=QDRANT_GRPC_PORT,
        )

        self.search_type_map = {
            "dense": self._get_dense_vector_store,
            "hybrid": self._get_hybrid_vector_store,
        }

    def _get_dense_embeddings(
        self,
        dense_embeddings: Embeddings,
        dense_embed_doc_cache_path: str | None,
        dense_embed_query_cache_path: str | None,
    ) -> Embeddings:
        if dense_embed_doc_cache_path is None:
            return dense_embeddings

        query_embedding_cache = (
            True
            if dense_embed_query_cache_path is None
            else LocalFileStore(root_path=dense_embed_query_cache_path)
        )

        return CacheBackedEmbeddings.from_bytes_store(
            underlying_embeddings=dense_embeddings,
            document_embedding_cache=LocalFileStore(
                root_path=dense_embed_doc_cache_path
            ),
            namespace=dense_embeddings.model,  # type: ignore
            query_embedding_cache=query_embedding_cache,
        )

    @lru_cache()
    def _get_dense_vector_store(
        self,
        collection_name: str,
    ) -> QdrantVectorStore:
        return QdrantVectorStore(
            client=self.qadrant_client,
            collection_name=collection_name,
            embedding=self.dense_embeddings,
            retrieval_mode=RetrievalMode.DENSE,
            vector_name="dense",
        )

    @lru_cache()
    def _get_hybrid_vector_store(
        self,
        collection_name: str,
    ) -> QdrantVectorStore:
        return QdrantVectorStore(
            client=self.qadrant_client,
            collection_name=collection_name,
            embedding=self.dense_embeddings,
            sparse_embedding=self.sparse_embeddings,
            retrieval_mode=RetrievalMode.HYBRID,
            vector_name="dense",
            sparse_vector_name="sparse",
        )

    def create_collection(self, collection_name: str) -> None:
        if self.qadrant_client.collection_exists(
            collection_name=collection_name
        ):
            logger.warning(f"collection {collection_name} already exists.")
            return

        self.qadrant_client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": VectorParams(
                    size=self.dense_embed_dimensions,  # type: ignore
                    distance=Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=False)
                )
            },
        )

    def insert_text_chunks(
        self,
        collection_name: str,
        text_chunks: list[TextChunk],
    ) -> None:
        if not self.qadrant_client.collection_exists(
            collection_name=collection_name
        ):
            logger.warning(f"collection {collection_name} doesn't exists.")
            return

        vector_store = self._get_hybrid_vector_store(
            collection_name=collection_name
        )

        documents = [
            Document(
                page_content=tc.text,
                metadata=tc.metadata,
            )
            for tc in text_chunks
        ]

        uuids = [str(uuid4()) for _ in range(len(documents))]
        vector_store.add_documents(documents=documents, ids=uuids)

    def _parse_results(
        self,
        results: list[tuple[Document, float]],
    ) -> list[RetrieverItem]:
        return [
            RetrieverItem(
                text=document.page_content,
                metadata=document.metadata,
                score=score,
            )
            for document, score in results
        ]

    async def dense_search(
        self,
        collection_name: str,
        query: str,
        k: int = 10,
        search_filter: models.Filter | None = None,
    ) -> list[RetrieverItem]:
        vector_store = self._get_dense_vector_store(
            collection_name=collection_name
        )

        results = await vector_store.asimilarity_search_with_score(
            query=query,
            k=k,
            filter=search_filter,
        )

        return self._parse_results(results=results)

    async def hybrid_search(
        self,
        collection_name: str,
        query: str,
        k: int = 10,
        search_filter: models.Filter | None = None,
    ) -> list[RetrieverItem]:
        vector_store = self._get_hybrid_vector_store(
            collection_name=collection_name
        )

        results = await vector_store.asimilarity_search_with_score(
            query=query,
            k=k,
            filter=search_filter,
        )

        return self._parse_results(results=results)

    @lru_cache()
    def _get_retriever(
        self,
        collection_name: str,
        search_type: str,
        k: int,
    ) -> VectorStoreRetriever:
        vector_store = self.search_type_map[search_type](
            collection_name=collection_name
        )

        return vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": k,
            },
        )

    async def retrieve(
        self,
        collection_name: str,
        query: str,
        k: int = 10,
        search_type: Literal["dense", "hybrid"] = "dense",
    ) -> list[RetrieverItem]:
        retriever = self._get_retriever(
            collection_name=collection_name,
            search_type=search_type,
            k=k,
        )

        results = await retriever.ainvoke(input=query)
        return [
            RetrieverItem(
                text=r.page_content,
                metadata=r.metadata,
            )
            for r in results
        ]

    def scroll(
        self,
        collection_name: str,
        limit: int = 10,
        scroll_filter: models.Filter | None = None,
    ):
        return self.qadrant_client.scroll(
            collection_name=collection_name,
            limit=limit,
            scroll_filter=scroll_filter,
        )
