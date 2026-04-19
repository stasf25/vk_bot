"""
VK-бот с RAG-функциональностью.
"""

import asyncio
import logging
from pathlib import Path
from typing import List
from vkbottle.bot import Bot, Message as VKMessage
from vkbottle.dispatch.rules.base import TextRule, FuncRule

from config import VK_API_TOKEN, CHAT_API_URL, CHAT_API_KEY, CHAT_MODEL, VISION_API_URL, VISION_API_KEY, VISION_ENDPOINT, VISION_MODEL, EMBED_MODEL, \
    CHAT_ENDPOINT, EMBED_ENDPOINT, REQUEST_TIMEOUT, DOCS_PATH, \
    FAISS_INDEX_PATH, FAISS_METADATA_PATH, TOP_K_RESULTS, MAX_CONTEXT_LENGTH, \
    SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE, LOG_LEVEL, LOG_FORMAT
from rag.pipeline import RAGPipeline

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler("vk_bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
bot = Bot(token=VK_API_TOKEN)

# ========== ПАМЯТЬ РАЗГОВОРОВ ==========
# Словарь для хранения истории сообщений каждого пользователя
# Структура: {user_id: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
conversation_history = {}
MAX_HISTORY_LENGTH = 10  # Максимум последних сообщений для контекста

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def chunk_text(text: str, max_chars: int = 6000) -> List[str]:
    """
    Разбивает текст на части заданного размера.

    Args:
        text: Текст для разбиения
        max_chars: Максимальный размер одной части в символах

    Returns:
        Список частей текста
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current_chunk = []
    current_length = 0

    # Разбиваем по параграфам (двойной перенос строки)
    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        paragraph_length = len(paragraph) + 2  # +2 для \n\n

        # Если параграф сам больше лимита, разбиваем его по предложениям
        if paragraph_length > max_chars:
            sentences = paragraph.split('. ')
            for sentence in sentences:
                sentence_length = len(sentence) + 2

                if current_length + sentence_length > max_chars and current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = [sentence]
                    current_length = sentence_length
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_length

        # Если добавление параграфа превысит лимит, сохраняем текущий chunk
        elif current_length + paragraph_length > max_chars and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [paragraph]
            current_length = paragraph_length
        else:
            current_chunk.append(paragraph)
            current_length += paragraph_length

    # Добавляем последний chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks


def load_documents_from_directory(directory: Path) -> tuple[List[str], List[str]]:
    """
    Загружает все текстовые документы из директории.
    Большие документы разбиваются на части (chunks).

    Args:
        directory: Путь к директории с документами

    Returns:
        Кортеж (тексты документов, имена файлов)
    """
    documents = []
    sources = []

    if not directory.exists():
        logger.warning(f"Директория {directory} не существует")
        return documents, sources

    # Ищем все .txt файлы
    for file_path in directory.glob("*.txt"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

                # Разбиваем большие документы на части
                chunks = chunk_text(text, max_chars=6000)

                if len(chunks) > 1:
                    logger.info(f"Загружен документ: {file_path.name} ({len(text)} символов) - разбит на {len(chunks)} частей")
                    for i, chunk in enumerate(chunks, 1):
                        documents.append(chunk)
                        sources.append(f"{file_path.name} (часть {i}/{len(chunks)})")
                else:
                    logger.info(f"Загружен документ: {file_path.name} ({len(text)} символов)")
                    documents.append(text)
                    sources.append(file_path.name)

        except Exception as e:
            logger.error(f"Ошибка при чтении файла {file_path}: {e}")

    logger.info(f"Всего загружено документов/частей: {len(documents)}")
    return documents, sources


async def send_long_message(message: VKMessage, text: str, max_length: int = 4000):
    """
    Отправляет длинное сообщение, разбивая его на части если нужно.

    Args:
        message: Исходное сообщение для ответа
        text: Текст для отправки
        max_length: Максимальная длина одного сообщения
    """
    if len(text) <= max_length:
        await message.answer(text)
        return

    # Разбиваем на части
    parts = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    for part in parts:
        await message.answer(part)
        await asyncio.sleep(0.5)


async def handle_photo(message: VKMessage, user_query: str):
    """
    Обработчик фотографий - извлекает текст с изображения.
    """
    photos = message.get_photo_attachments()
    if not photos: return 0
    logger.info(f"Получено изображений от пользователя {message.from_id}: {len(photos)}")

    for i,photo in enumerate(photos):
        processing_msg = await message.answer(f"🖼 Обрабатываю изображение {i+1}...")
        try:
            '''
            if photo.images:   # неправильно - должно быть photo.sizes !!!
                largest = max(photo.images, key=lambda x: x.width * x.height)
                image_url = largest.url
            else:
                logger.info (f"{photo.sizes}")
                logger.info (f"{photo.orig_photo.to_dict()}")
                for attr in dir(photo.orig_photo):
                    if  not attr.startswith('__') and attr != 'src'  and attr != 'type':
                        par = "()"  if  callable(getattr(photo, attr))  else ""
                        logger.info (f"{attr}{par}:\n{type(getattr(photo, attr))}\n{getattr(photo, attr).__doc__}")
            '''
            image_url = photo.orig_photo.to_dict().get('url', None)

            if not image_url: raise ValueError("No image URL available")
            else:             logger.info (f"URL: {image_url}")
            
            result = RAGPipeline().process_image(image_url, user_query)

            if result.get('error'):
                await message.answer(f"❌ Ошибка при обработке изображения: {result['error']}")
                break

            response_text = "<b>📄 Текст с изображения:</b>\n"
            response_text += result['extracted_text'] + "\n\n"
            if result.get('rag_answer'):
                response_text += f"<b>💡 Ответ на ваш вопрос:</b>\n{result['rag_answer']}"

            await send_long_message(message, response_text)
            logger.info(f"Изображение обработано для пользователя {message.from_id}")

        except Exception as e:
            logger.error(f"Ошибка при обработке изображения: {e}")
            await message.answer(f"❌ Произошла ошибка: {str(e)}")
            break

    return  i +1


# ========== ОБРАБОТЧИКИ КОМАНД ==========

@bot.on.message(TextRule(["/start", "привет", "здравствуй", "хай", "hi", "hello"], ignore_case=True))
async def cmd_start(message: VKMessage):
    """
    Обработчик команды /start - приветствие и информация о боте.
    """
    logger.info(f"Пользователь {message.from_id} запустил бота")

    welcome_text = """
🤖 <b>Добро пожаловать в RAG-бота !</b>

Я интеллектуальный ассистент с доступом к базе знаний.
Работаю через OpenAI-совместимый endpoint.

<b>Мои возможности:</b>
📚 Поиск информации в базе знаний (RAG)
🖼 Обработка изображений и извлечение текста
💬 Ответы на вопросы с использованием контекста

<b>Доступные команды:</b>
/start - Показать это сообщение
/help - Подробная справка
/ask <вопрос> - Задать вопрос с поиском в базе знаний
/ingest - Перезагрузить базу знаний (только для администраторов)
/stats - Показать статистику системы
/clear - Очистить историю разговора

<b>Как пользоваться:</b>
• Просто напишите вопрос, и я найду ответ в базе знаний
• Отправьте изображение с текстом, и я его обработаю
• Используйте /ask для явного RAG-запроса

Powered by RAG + FAISS
"""
    await message.answer(welcome_text, parse_mode="html")


@bot.on.message(TextRule(["что ты умеешь", "помощь", "/help"], ignore_case=True))
async def cmd_help(message: VKMessage):
    """
    Обработчик команды /help - подробная справка.
    """
    logger.info(f"Пользователь {message.from_id} запросил справку")

    help_text = """
📖 <b>Подробная справка по использованию бота</b>

<b>1️⃣ RAG-запросы (Retrieval-Augmented Generation)</b>
RAG - это технология, которая позволяет мне находить релевантную информацию в базе знаний и использовать её для формирования ответа.

Примеры запросов:
• "Что такое RAG и как он работает?"
• "Как применяется RAG в поддержке клиентов?"
• "Расскажи о преимуществах RAG в HR"

<b>2️⃣ Обработка изображений</b>
Отправьте мне изображение (фото, скриншот, скан документа), и я:
• Извлеку текст с изображения
• Могу ответить на вопросы по этому тексту
• Найду связанную информацию в базе знаний

Пример: отправьте фото документа с подписью "Что это значит?"

<b>3️⃣ Команды</b>
/ask <вопрос> - Явный RAG-запрос
Пример: /ask Как работает векторный поиск?

/ingest - Перезагрузка базы знаний
Эта команда переиндексирует все документы.

/stats - Статистика системы
Показывает информацию о системе и API endpoint.

/clear - Очистить историю разговора

<b>4️⃣ Технические детали</b>
🔸 API: OpenAI-совместимый
🔸 Модель чата: gpt-4o-mini
🔸 Модель vision: gpt-4o-mini
🔸 Эмбеддинги: text-embedding-3-small
🔸 Векторная БД: FAISS
🔸 HTTP клиент: requests

<b>Преимущества версии:</b>
✅ Работа с любыми OpenAI-совместимыми API
✅ Полный контроль над запросами
✅ Легкая отладка и мониторинг
✅ Возможность использования локальных моделей

<b>Примеры эффективного использования:</b>
✅ "Объясни как RAG помогает в HR-процессах"
✅ "Какие метрики эффективности RAG в поддержке?"
✅ "В чем преимущества использования RAG?"

Если у вас есть вопросы - просто задайте их! 😊
"""
    await message.answer(help_text, parse_mode="html")


@bot.on.message(text="/ingest")
async def cmd_ingest(message: VKMessage):
    """
    Обработчик команды /ingest - индексация документов.
    """
    logger.info(f"Запрос на индексацию от пользователя {message.from_id}")

    await message.answer("📥 Начинаю индексацию документов...")

    try:
        documents, sources = load_documents_from_directory(DOCS_PATH)

        if not documents:
            await message.answer(
                f"❌ Документы не найдены в директории {DOCS_PATH}\n"
                "Пожалуйста, добавьте .txt файлы с документами."
            )
            return

        await message.answer(f"📄 Найдено документов: {len(documents)}\nНачинаю обработку...")

        # Создаем RAG pipeline
        rag_pipeline = RAGPipeline()

        success = rag_pipeline.index_documents(documents, sources)

        if success:
            stats = rag_pipeline.get_stats()
            response = (
                "✅ <b>Индексация завершена успешно!</b>\n\n"
                f"📊 Статистика:\n"
                f"• Документов: {stats['total_documents']}\n"
                f"• Векторов: {stats['total_vectors']}\n"
                f"• Размерность: {stats['dimension']}\n"
                f"• API: {stats['api_url']}\n\n"
                f"Бот готов к работе! Задавайте вопросы. 💬"
            )
            await message.answer(response, parse_mode="html")
            logger.info("Индексация завершена успешно")
        else:
            await message.answer("❌ Ошибка при индексации документов. См. логи для деталей.")

    except Exception as e:
        logger.error(f"Ошибка при индексации: {e}")
        await message.answer(f"❌ Произошла ошибка при индексации: {str(e)}")


@bot.on.message(text="/stats")
async def cmd_stats(message: VKMessage):
    """
    Обработчик команды /stats - статистика системы.
    """
    logger.info(f"Запрос статистики от пользователя {message.from_id}")

    try:
        # Создаем RAG pipeline
        from rag.pipeline import RAGPipeline
        rag_pipeline = RAGPipeline()

        stats = rag_pipeline.get_stats()
        user_id = message.from_id

        status_emoji = "✅" if stats['is_loaded'] else "❌"
        status_text = "Загружена" if stats['is_loaded'] else "Не загружена"

        # Статистика истории для пользователя
        history_count = len(conversation_history.get(user_id, [])) // 2

        stats_text = f"""
📊 <b>Статистика RAG-системы </b>

<b>Состояние базы знаний:</b>
{status_emoji} {status_text}

<b>Данные:</b>
• Документов: {stats['total_documents']}
• Векторов: {stats['total_vectors']}
• Размерность: {stats['dimension']}
• API: {stats['api_url']}

<b>История разговоров:</b>
• Сообщений: {history_count}
• Пользователей: {len(conversation_history)}

<b>Конфигурация:</b>
• Модель чата: {CHAT_MODEL}
• Модель vision: {VISION_MODEL}
• Эмбеддинги: {EMBED_MODEL}
• Таймаут: {REQUEST_TIMEOUT} сек
• API endpoint: {CHAT_API_URL}
"""
        await message.answer(stats_text, parse_mode="html")

    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")


@bot.on.message(text="/clear")
async def cmd_clear(message: VKMessage):
    """
    Обработчик команды /clear - очистка истории разговора.
    """
    user_id = message.from_id
    if user_id in conversation_history:
        conversation_history[user_id] = []
        await message.answer("🗑️ История разговора очищена!")
        logger.info(f"История разговора пользователя {user_id} очищена")
    else:
        await message.answer("ℹ️ История разговора уже пуста.")


@bot.on.message(TextRule(["/test"], ignore_case=True))
async def cmd_test(message: VKMessage):
    """
    Обработчик команды /test - проверка подключения к API.
    """
    logger.info(f"Проверка подключения от пользователя {message.from_id}")
    await message.answer("🔄 Проверяю подключение к API...")
    try:
        success = RAGPipeline().test_connection()
        if success:
            await message.answer("✅ Подключение к API работает корректно!")
        else:
            await message.answer("❌ Проблемы с подключением к API. См. логи.")
    except Exception as e:
        logger.error(f"Ошибка при проверке подключения: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@bot.on.message()
async def handle_message(message: VKMessage):
    """
    Обработчик команды /ask - RAG-запрос.
    """
    query = message.text[5:].strip()  if message.text.lower().startswith("/ask ")  else message.text
    if not query:
        await message.answer(
            "❌ Пожалуйста, укажите вопрос после команды.\n"
            "Пример: /ask Что такое RAG?"
        )
        return

    if  await handle_photo(message, query):  return
    logger.info(f"RAG-запрос от пользователя {message.from_id}: >{query}<")
    processing_msg = await message.answer("🔍 Ищу информацию в базе знаний...")

    try:
        user_id = message.from_id
        if user_id not in conversation_history:
            conversation_history[user_id] = []

        result = RAGPipeline().query_with_history(query, conversation_history[user_id])

        conversation_history[user_id].append({"role": "user", "content": query})
        conversation_history[user_id].append({"role": "assistant", "content": result['answer']})

        if len(conversation_history[user_id]) > MAX_HISTORY_LENGTH * 2:
            conversation_history[user_id] = conversation_history[user_id][-(MAX_HISTORY_LENGTH * 2):]
            logger.info(f"История обрезана до {MAX_HISTORY_LENGTH} пар сообщений")

        response_text = result['answer']
        await send_long_message(message, response_text)
        logger.info(f"Ответ отправлен пользователю {user_id} (история: {len(conversation_history[user_id])//2} сообщений)")

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

    return



# ========== ОСНОВНОЙ ЗАПУСК БОТА ==========
if __name__ == "__main__":
    logger.info("Запуск VK-бота с RAG-функциональностью ")

    # Проверяем наличие токена
    if not VK_API_TOKEN:
        logger.error("VK_API_TOKEN не установлен в переменных окружения!")
        print("❌ VK_API_TOKEN не установлен в переменных окружения!")
        exit(1)

    # Проверяем наличие API ключа
    if not CHAT_API_KEY:
        logger.error("CHAT_API_KEY не установлен в переменных окружения!")
        print("❌ CHAT_API_KEY не установлен в переменных окружения!")
        exit(1)

    # Создаем директории если их нет
    Path(DOCS_PATH).mkdir(parents=True, exist_ok=True)

    # Запускаем бота
    try:
        logger.info("Запускаю VK-бота...")
        bot.run_forever()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        print(f"❌ Ошибка при запуске бота: {e}")
        exit(1)