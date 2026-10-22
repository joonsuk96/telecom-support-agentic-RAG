from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec


def find_project_root() -> Path:
    """Find the project folder without assuming a particular package layout."""
    current = Path(__file__).resolve().parent
    for folder in (current, *current.parents):
        if (folder / "pyproject.toml").is_file() or (folder / ".env").is_file():
            return folder
    return current


PROJECT_ROOT = find_project_root()
RAW_DOCS_DIR = PROJECT_ROOT / "data" / "raw"


def load_settings() -> None:
    env_path = PROJECT_ROOT / ".env"
    load_dotenv(env_path)
    required = ("OPENAI_API_KEY", "PINECONE_API_KEY", "PINECONE_INDEX")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variables: {names}. "
            f"Expected a .env file at: {env_path}. "
            "Check that this exact file contains the variable names above with non-empty values."
        )


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    )


def get_vector_index_name() -> str:
    """Return the name of the vector index used by this app.

    PINECONE_INDEX remains the user's configured base name. We add a suffix
    because an index with that name may already be a document-schema index.
    """
    load_settings()
    configured_name = os.getenv("PINECONE_VECTOR_INDEX")
    if configured_name:
        return configured_name

    base_name = os.environ["PINECONE_INDEX"]
    return f"{base_name[:37]}-vectors"


def ensure_vector_index() -> str:
    """Create a compatible dense-vector index on first use if it is missing."""
    load_settings()
    index_name = get_vector_index_name()
    pinecone = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

    if index_name not in pinecone.list_indexes().names():
        dimension = int(os.getenv("PINECONE_DIMENSION", "1536"))
        cloud = os.getenv("PINECONE_CLOUD", "aws")
        region = os.getenv("PINECONE_REGION", "us-east-1")
        pinecone.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region),
            vector_type="dense",
        )

    return index_name


def get_namespace_vector_count(namespace: str) -> int:
    """Return the stored vector count for a namespace, or zero if it is empty."""
    load_settings()
    index_name = ensure_vector_index()
    pinecone = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    stats = pinecone.Index(index_name).describe_index_stats()
    namespaces = getattr(stats, "namespaces", None) or {}
    namespace_stats = namespaces.get(namespace)
    if namespace_stats is None:
        return 0
    return int(getattr(namespace_stats, "vector_count", 0) or 0)


def get_vector_store(namespace: str | None = None) -> PineconeVectorStore:
    load_settings()
    return PineconeVectorStore(
        index_name=ensure_vector_index(),
        embedding=get_embeddings(),
        namespace=namespace or os.getenv("PINECONE_NAMESPACE", "skt-docs-v1"),
    )
