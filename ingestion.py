from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from common import get_namespace_vector_count, get_vector_index_name, get_vector_store


def index_uploaded_pdfs(
    files: list[tuple[str, bytes]],
) -> tuple[str, int | None, int, str, bool]:
    """Index uploaded PDFs into a corpus-specific Pinecone namespace."""
    if not files:
        raise ValueError("PDF 파일을 하나 이상 업로드해 주세요.")

    digest = hashlib.sha256()
    for filename, content in sorted(files, key=lambda item: item[0].lower()):
        digest.update(filename.encode("utf-8"))
        digest.update(content)
    corpus_hash = digest.hexdigest()
    namespace = f"upload-{corpus_hash[:24]}"
    existing_count = get_namespace_vector_count(namespace)
    if existing_count:
        return namespace, None, existing_count, get_vector_index_name(), True

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150, add_start_index=True
    )
    chunks = []
    ids = []
    page_count = 0

    with TemporaryDirectory(prefix="telco-rag-") as temp_dir:
        for number, (filename, content) in enumerate(files):
            safe_name = Path(filename).name
            if not safe_name.lower().endswith(".pdf"):
                raise ValueError(f"PDF 파일만 업로드할 수 있습니다: {safe_name}")
            path = Path(temp_dir) / f"{number}-{safe_name}"
            path.write_bytes(content)
            file_hash = hashlib.sha256(content).hexdigest()
            pages = PyMuPDFLoader(str(path)).load()
            page_count += len(pages)
            for page in pages:
                page_number = int(page.metadata.get("page", 0)) + 1
                page.metadata = {
                    "source_file": safe_name,
                    "page": page_number,
                    "file_hash": file_hash,
                    "document_type": "pdf",
                }
            if not any(page.page_content.strip() for page in pages):
                raise ValueError(f"텍스트를 추출할 수 없습니다. 스캔 PDF인지 확인해 주세요: {safe_name}")
            file_chunks = splitter.split_documents(pages)
            per_page: dict[int, int] = {}
            for chunk in file_chunks:
                page_number = int(chunk.metadata["page"])
                chunk_number = per_page.get(page_number, 0)
                per_page[page_number] = chunk_number + 1
                chunk.metadata["chunk"] = chunk_number
                raw_id = f"{file_hash}:{page_number}:{chunk_number}".encode("utf-8")
                ids.append(hashlib.sha256(raw_id).hexdigest())
                chunks.append(chunk)

    if not chunks:
        raise ValueError("PDF에서 검색 가능한 텍스트를 찾지 못했습니다.")

    get_vector_store(namespace=namespace).add_documents(chunks, ids=ids)
    return namespace, page_count, len(chunks), get_vector_index_name(), False
