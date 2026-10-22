# Telecom Support Agentic RAG

A document-grounded support copilot for telecom customer service teams. Upload telecom policy PDFs, index them in Pinecone, and ask questions in a Streamlit chat interface. The agent searches the uploaded documents and drafts Korean answers with page-level citations for a human support agent to review.

> **Prototype:** This project is for learning and portfolio demonstration. Its answers are drafts, not authoritative customer communications. Validate the source documents and test the system before using it in a real support operation.

## Features

- Upload one or more PDF files through the web interface.
- Extract PDF text, split it into overlapping chunks, and create OpenAI embeddings.
- Store and retrieve vectors in Pinecone. A compatible dense-vector index is created automatically when it does not exist.
- Reuse an existing corpus namespace when the exact same set of PDFs is uploaded again, avoiding duplicate embeddings for that corpus.
- Use a tool-calling agent to search the uploaded PDFs and answer in Korean with source file and page references.
- Ask the agent to state when the uploaded documents do not provide enough evidence instead of guessing.

## How it works

1. Upload PDFs in the Streamlit app.
2. The ingestion pipeline extracts pages, adds source metadata, splits the text into chunks, and embeds the chunks.
3. Pinecone stores the vectors in a namespace derived from the uploaded corpus.
4. For each question, the agent calls a retrieval tool to find relevant passages.
5. The agent drafts an answer based on those passages and includes citations such as `[guide.pdf p. 4]`.

## Tech stack

- Python 3.12+
- Streamlit
- LangChain and LangGraph
- OpenAI chat and embedding models
- Pinecone vector database
- PyMuPDF
- uv for Python dependency management

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key
- A Pinecone API key and an account that can create serverless indexes

## Run locally

1. Clone this repository and open its folder in a terminal.

   ```powershell
   git clone https://github.com/<your-github-username>/telecom-support-agentic-RAG.git
   cd telecom-support-agentic-RAG
   ```

2. Install the project dependencies:

   ```powershell
   uv sync
   ```

3. Create a `.env` file in the project root with the required credentials:

   ```dotenv
   OPENAI_API_KEY=your-openai-api-key
   PINECONE_API_KEY=your-pinecone-api-key
   PINECONE_INDEX=your-base-index-name
   ```

   Never commit `.env` or paste real credentials into source code. `.env` is excluded by `.gitignore`.

4. Start the app:

   ```powershell
   uv run streamlit run app.py
   ```

5. Open the local URL printed by Streamlit, upload PDF documents, and select **Start document analysis**. Ask questions in the chat after indexing completes.

## Configuration

The following optional environment variables can be added to `.env`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | OpenAI chat model used by the agent |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Model used to embed document chunks and queries |
| `PINECONE_VECTOR_INDEX` | `<PINECONE_INDEX>-vectors` | Explicit name for the dense-vector index; otherwise derived from `PINECONE_INDEX` |
| `PINECONE_DIMENSION` | `1536` | Vector dimension; must match the selected embedding model |
| `PINECONE_CLOUD` | `aws` | Pinecone serverless cloud provider |
| `PINECONE_REGION` | `us-east-1` | Pinecone serverless region |
| `PINECONE_NAMESPACE` | `skt-docs-v1` | Default namespace for vector-store operations |
| `RETRIEVAL_K` | `5` | Number of candidate passages retrieved per search |
| `MIN_RELEVANCE_SCORE` | `0.20` | Minimum relevance score used to keep a retrieved passage |

The project appends `-vectors` to `PINECONE_INDEX` by default because Pinecone indexes with a document schema require a different write API. You can set `PINECONE_VECTOR_INDEX` to choose the vector index name directly.

## Project structure

```text
.
├── agent.py       # Retrieval tool and answer-generating agent
├── app.py         # Streamlit interface for PDF upload and chat
├── common.py      # Environment settings, embeddings, and Pinecone setup
├── ingestion.py   # PDF extraction, chunking, deduplication, and indexing
├── pyproject.toml # Project metadata and dependencies
├── uv.lock        # Locked dependency versions
└── README.md
```

## Current limitations

- Retrieval and answer quality depend on the uploaded PDFs, their text quality, and the chosen models.
- Image-only or scanned PDFs may not contain extractable text and are not OCR-processed by the current ingestion pipeline.
- Corpus reuse is based on the uploaded file names and contents; uploading changed documents creates a new corpus namespace.
- Index creation and API usage may incur charges according to your OpenAI and Pinecone plans.
- The project does not yet include a formal evaluation dataset, automated regression tests, authentication, or production monitoring.

## Data and privacy

Use documents you are permitted to process and upload. Consider the privacy and retention terms of the services configured for this project before uploading customer or confidential information. Do not use real customer personal data in a public portfolio demo.

## License

No license has been added yet. Unless a license is added, others do not automatically have permission to reuse, modify, or distribute this project's code.
