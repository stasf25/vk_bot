"""
Конфигурация для Telegram-бота с RAG на основе ProxyAPI.

Этот модуль содержит настройки для работы бота через кастомный API endpoint,
совместимый с OpenAI API. Это позволяет использовать собственные или
альтернативные провайдеры LLM.
"""

import os
from pathlib import Path
from dotenv import dotenv_values, find_dotenv

# Загружаем переменные окружения из файла .env
CONFIG = dotenv_values()

# ========== VK НАСТРОЙКИ ==========
# Токен сообщества получаем в настройках сообщества VK
API_TOKEN = CONFIG.get("VK_TEST_TOKEN", "")
if not API_TOKEN:
    raise ValueError("VK_TEST_TOKEN не установлен в переменных окружения!")

# ========== AITUNNEL НАСТРОЙКИ ==========
# URL aitunnel API endpoint (совместимый с OpenAI API)
# Примеры:
# - https://api.aitunnel.ru/openai/v1
# - https://your-aitunnel.com/v1
# - http://localhost:8000/v1
API_URL = CONFIG.get("AITUNNEL_API_URL", "https://api.aitunnel.ru/openai/v1")

# API ключ для доступа к aitunnel
API_KEY = CONFIG.get("AITUNNEL_API_KEY", "")
if not API_KEY:
    raise ValueError("AITUNNEL_API_KEY не установлен в переменных окружения!")

# Endpoints для aitunnel API
CHAT_ENDPOINT = CONFIG.get("AITUNNEL_CHAT_ENDPOINT", "/chat/completions")
EMBEDDINGS_ENDPOINT = CONFIG.get("AITUNNEL_EMBEDDINGS_ENDPOINT", "/embeddings")

# Модель для создания эмбеддингов (векторных представлений текста)
EMBED_MODEL = CONFIG.get("EMBED_MODEL", "text-embedding-3-small")
if not EMBED_MODEL:
    raise ValueError("EMBED_MODEL не установлен в переменных окружения!")

# Модель для генерации ответов (чат)
CHAT_MODEL = CONFIG.get("CHAT_MODEL", "gpt-4o-mini")
if not CHAT_MODEL:
    raise ValueError("CHAT_MODEL не установлен в переменных окружения!")

# Модель для обработки изображений (vision)
VISION_MODEL = CONFIG.get("VISION_MODEL", "gpt-4o-mini")
if not VISION_MODEL:
    raise ValueError("VISION_MODEL не установлен в переменных окружения!")

# Таймаут для HTTP запросов (в секундах)
REQUEST_TIMEOUT = 60

# ========== FAISS НАСТРОЙКИ ==========
# Путь к индексному файлу FAISS (векторная база данных)
PROJECT_ROOT     = f"{find_dotenv('.env')[0:-5]}"
DATA_DIR         = f"{PROJECT_ROOT}/data"
FAISS_INDEX_PATH = Path(DATA_DIR) / "index.faiss"
FAISS_METADATA_PATH = Path(DATA_DIR) / "metadata.json"
DOCS_PATH        = Path(DATA_DIR) / "docs"

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

