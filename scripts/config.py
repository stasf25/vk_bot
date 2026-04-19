"""
Конфигурация для VK-бота с RAG на основе нескольких API провайдеров.

Этот модуль содержит настройки для работы бота через отдельные API endpoints:
- Chat API (NVIDIA) - для генерации текстовых ответов
- Vision API (NVIDIA) - для обработки изображений
- Embeddings API (OpenRouter) - для создания векторных представлений
"""

import os
from pathlib import Path
from dotenv import dotenv_values, find_dotenv

# Загружаем переменные окружения из файла .env
CONFIG = dotenv_values()

# ========== VK НАСТРОЙКИ ==========
# Токен сообщества получаем в настройках сообщества VK
VK_API_TOKEN = CONFIG.get("VK_TEST_TOKEN", "")
if not VK_API_TOKEN:
    raise ValueError("VK_TEST_TOKEN не установлен в переменных окружения!")

# ========== CHAT API НАСТРОЙКИ (NVIDIA) ==========
# URL для чат API
CHAT_API_URL = CONFIG.get("CHAT_API_URL", "")
if not CHAT_API_URL:
    raise ValueError("CHAT_API_URL не установлен в переменных окружения!")

# API ключ для доступа к чат API
CHAT_API_KEY = CONFIG.get("CHAT_API_KEY", "")
if not CHAT_API_KEY:
    raise ValueError("CHAT_API_KEY не установлен в переменных окружения!")

# Endpoint для чат запросов
CHAT_ENDPOINT = CONFIG.get("CHAT_ENDPOINT", "/chat/completions")

# Модель для генерации ответов (чат)
CHAT_MODEL = CONFIG.get("CHAT_MODEL", "qwen/qwen3.5-122b-a10b")
if not CHAT_MODEL:
    raise ValueError("CHAT_MODEL не установлен в переменных окружения!")

# ========== VISION API НАСТРОЙКИ (NVIDIA) ==========
# URL для vision API
VISION_API_URL = CONFIG.get("VISION_API_URL", "")
if not VISION_API_URL:
    raise ValueError("VISION_API_URL не установлен в переменных окружения!")

# API ключ для доступа к vision API
VISION_API_KEY = CONFIG.get("VISION_API_KEY", "")
if not VISION_API_KEY:
    raise ValueError("VISION_API_KEY не установлен в переменных окружения!")

# Endpoint для vision запросов
VISION_ENDPOINT = CONFIG.get("VISION_ENDPOINT", "/chat/completions")

# Модель для обработки изображений (vision)
VISION_MODEL = CONFIG.get("VISION_MODEL", "qwen/qwen3.5-122b-a10b")
if not VISION_MODEL:
    raise ValueError("VISION_MODEL не установлен в переменных окружения!")

# ========== EMBEDDINGS API НАСТРОЙКИ (OpenRouter) ==========
# URL для embeddings API
EMBED_API_URL = CONFIG.get("EMBED_API_URL", "")
if not EMBED_API_URL:
    raise ValueError("EMBED_API_URL не установлен в переменных окружения!")

# API ключ для доступа к embeddings API
EMBED_API_KEY = CONFIG.get("EMBED_API_KEY", "")
if not EMBED_API_KEY:
    raise ValueError("EMBED_API_KEY не установлен в переменных окружения!")

# Endpoint для embeddings запросов
EMBED_ENDPOINT = CONFIG.get("EMBED_ENDPOINT", "/embeddings")

# Модель для создания эмбеддингов (векторных представлений текста)
EMBED_MODEL = CONFIG.get("EMBED_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2:free")
if not EMBED_MODEL:
    raise ValueError("EMBED_MODEL не установлен в переменных окружения!")

# ========== ОБЩИЕ НАСТРОЙКИ ==========
# Таймаут для HTTP запросов (в секундах)
REQUEST_TIMEOUT = 60

# ========== FAISS НАСТРОЙКИ ==========
# Путь к индексному файлу FAISS (векторная база данных)
PROJECT_ROOT = f"{find_dotenv('.env')[0:-5]}"
DATA_DIR = f"{PROJECT_ROOT}/data"
FAISS_INDEX_PATH = Path(DATA_DIR) / "index.faiss"
FAISS_METADATA_PATH = Path(DATA_DIR) / "metadata.json"
DOCS_PATH = Path(DATA_DIR) / "docs"

# ========== RAG НАСТРОЙКИ ==========
# Количество документов для извлечения из базы знаний
TOP_K_RESULTS = 3

# Максимальная длина контекста (в символах)
MAX_CONTEXT_LENGTH = 3000

# ========== ПРОМПТЫ ==========
# Системный промпт для RAG-ассистента
SYSTEM_PROMPT = """Ты — интеллектуальный ассистент с доступом к базе знаний.
Твоя задача — отвечать на вопросы пользователей, опираясь на предоставленный контекст из базы знаний и историю разговора.

Правила работы:
1. Используй информацию из контекста базы знаний для формирования ответа
2. Учитывай историю предыдущих сообщений для понимания контекста разговора
3. Если пользователь спрашивает про "это", "то", "предыдущий вопрос" - смотри в историю сообщений выше
4. Если в контексте нет информации для ответа, честно скажи об этом
5. Отвечай на русском языке четко и структурированно
6. Если уместно, используй списки и пункты для лучшей читаемости
7. Будь вежливым и профессиональным
"""

# Шаблон для формирования промпта с контекстом
RAG_PROMPT_TEMPLATE = """Контекст из базы знаний:
{context}

Вопрос пользователя: {query}

Ответ:"""

# ========== ЛОГИРОВАНИЕ ==========
# Уровень логирования (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = "INFO"

# Формат сообщений в логах
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"