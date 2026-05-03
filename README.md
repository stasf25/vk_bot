# VK Bot - Multimodal chatbot with Retrieval-Augmented Generation (RAG)

## 📖 Overview

**vk_bot** is a Python‑based chatbot for the VK social network that integrates **RAG (Retrieval‑Augmented Generation)** capabilities. It can answer user questions using a knowledge base stored in a **FAISS** vector store, handle image‑to‑text extraction via a vision model, and generate responses using an OpenAI‑compatible chat model. The bot is built on top of **vkbottle**, a modern async framework for VK bots.

Key features:

* **Knowledge‑base search** – documents are indexed with embeddings (OpenRouter) and queried via FAISS.
* **Vision support** – extract text from images and optionally answer a follow‑up query.
* **Conversation history** – retains recent dialogue context for richer answers.
* **Admin commands** – re‑ingest documents, view stats, clear history, test API connections.
* **Configurable via `.env`** – all endpoints, models, and tokens are loaded from environment variables.

---

## 📂 Project Structure

```
vk_bot/
├── README.md                # This documentation (generated)
├── .gitignore
├── dot_env                  # Example .env file (not committed)
├── inst_venv                # Virtual‑env activation script
├── requirements_vk.txt      # Python dependencies
├── vkbottle.md              # Reference for vkbottle usage
├── example/
│   ├── scraper.py          # Simple HTML→Markdown scraper (example utility)
│   └── vkbot_example.py    # Example script showing bot usage (not shown)
├── scripts/
│   ├── config.py           # Central configuration loaded from .env
│   ├── vk_bot.py           # Main bot entry point (async, command handlers)
│   └── rag/
│       ├── __init__.py
│       ├── embedder.py      # Embedding generation via OpenRouter API
│       ├── pipeline.py     # Orchestrates RAG query, indexing, stats, health‑check
│       ├── retriever.py    # Retrieves relevant docs from FAISS
│       └── vectorstore.py  # FAISS wrapper (create, add, search, save/load)
└── tg/                     # (currently empty – placeholder for Telegram bot)
```

---

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/stasf25/vk_bot.git
   cd vk_bot
   ```
2. **Create a virtual environment** (optional but recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements_vk.txt
   ```
4. **Create a `.env` file** (see *Configuration* below) with the required API keys and tokens.
5. **Prepare a documents directory** – by default the bot expects a folder `data/docs` inside the project root. Put any `.txt` files you want the bot to search.

---

## 🔧 Configuration

All configurable values are loaded from a `.env` file via **python‑dotenv**. The file should define the following variables (example values omitted):

| Variable | Description |
|----------|-------------|
| `VK_TEST_TOKEN` | VK community token for the bot |
| `CHAT_API_URL` | Base URL of the chat LLM endpoint |
| `CHAT_API_KEY` | Authorization key for the chat API |
| `CHAT_MODEL` | Model name for chat completions |
| `VISION_API_URL` | Base URL for the vision model |
| `VISION_API_KEY` | Authorization key for vision |
| `VISION_MODEL` | Vision model name |
| `EMBED_API_URL` | Base URL for the embeddings endpoint |
| `EMBED_API_KEY` | Authorization key for embeddings |
| `EMBED_MODEL` | Embeddings model name |
| `REQUEST_TIMEOUT` | HTTP request timeout (seconds) |

Additional constants (FAISS paths, top‑k, max context length, prompts, logging) are defined in `scripts/config.py` and can be overridden by providing them in the `.env` file.

---

## 🚀 Running the Bot

```bash
python -m scripts.vk_bot
```

The script performs a few startup checks:

* Validates required environment variables.
* Ensures the `data/docs` directory exists.
* Loads an existing FAISS index if present.

The bot will then listen for VK messages. Use the following commands in a VK chat with the bot:

| Command | Description |
|---------|-------------|
| `/start` or greeting words | Shows a welcome banner and basic capabilities |
| `/help` | Detailed usage guide |
| `/ask <question>` | Explicit RAG query (optional – any message is also treated as a query) |
| `/ingest` | Re‑index all `.txt` files in `data/docs` (admin only) |
| `/stats` | Shows system statistics (model names, index size, API status) |
| `/clear` | Clears conversation history for the user |
| `/test` | Checks connectivity to all configured APIs |

---

## 🛠️ Architecture Details

### 1. Configuration (`scripts/config.py`)
Centralises all settings, loads them from `.env`, and defines constants such as `TOP_K_RESULTS`, `MAX_CONTEXT_LENGTH`, and logging formats.

### 2. Bot Core (`scripts/vk_bot.py`)
* Initializes a `vkbottle.Bot` instance.
* Maintains an in‑memory `conversation_history` dict per user.
* Provides helper functions:
  * `chunk_text` – splits large documents into manageable chunks.
  * `load_documents_from_directory` – reads `.txt` files, chunking them as needed.
  * `send_long_message` – splits long replies to respect VK message limits.
  * `handle_photo` – extracts text from images via the Vision API and optionally runs a RAG query on the extracted text.
* Registers command handlers (`/start`, `/help`, `/ingest`, `/stats`, `/clear`, `/test`) and a generic message handler that performs a RAG query.

### 3. RAG Pipeline (`scripts/rag/pipeline.py`)
Coordinates the three RAG components:
* **Embedder** – creates embeddings for text (via OpenRouter).
* **VectorStore** – FAISS wrapper handling index creation, addition, search, persistence.
* **Retriever** – obtains the most relevant documents and builds a context string.

The pipeline also builds the final prompt (`RAG_PROMPT_TEMPLATE`) that combines the retrieved context with the user query and system prompt before sending it to the chat LLM.

### 4. Embedder (`scripts/rag/embedder.py`)
Simple wrapper around the embeddings HTTP API. Supports batch requests (max 10 texts per call) and caches the embedding dimension after the first successful call.

### 5. VectorStore (`scripts/rag/vectorstore.py`)
Uses **FAISS IndexFlatL2** for similarity search. Stores document metadata (text, source filename, index) in a JSON side‑car file. Provides `create_index`, `add_documents`, `search`, `save`, `load`, and `get_stats`.

### 6. Retriever (`scripts/rag/retriever.py`)
Converts a query to an embedding, searches the FAISS index, and formats results. Also provides a helper `retrieve_context` that concatenates top‑k documents into a single context string respecting `MAX_CONTEXT_LENGTH`.

---

## 📦 Example Utilities

The `example/` directory contains a tiny HTML‑to‑Markdown scraper (`scraper.py`). It is unrelated to the VK bot but demonstrates a reusable utility that could be used to preprocess web content before adding it to the knowledge base.

---

## 🧪 Testing & Health Checks

* **`/test` command** – runs `RAGPipeline().test_connection()` which:
  * Calls `Embedder.test_connection()` to verify the embeddings endpoint.
  * Sends a short chat completion request.
  * Sends a minimal vision request using a public image.
  * Returns a boolean status displayed to the user.

* Unit‑testing is not currently part of the repository, but the modular design (separate classes with clear interfaces) makes it straightforward to add `pytest` tests for each component.

---

## 📚 Logging & Debugging

Logging is configured in `config.py` and `vk_bot.py` using Python’s built‑in `logging` module. The default level is **INFO**, but can be changed via the `LOG_LEVEL` environment variable. Logs are written to `vk_bot.log` and also output to the console.

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/awesome‑feature`).
3. Follow the existing code style (PEP‑8, type hints, docstrings).
4. Submit a pull request with a clear description of changes.

---

## 📄 License

This project is licensed under the MIT License – see the LICENSE file for details.

---

## 📞 Contact

For issues or questions, open an issue on the GitHub repository or contact the maintainer.

