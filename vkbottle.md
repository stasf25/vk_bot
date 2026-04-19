# VKBottle Documentation - Работа с вложениями (attachments)

## Официальная документация

**Основная документация:** https://vkbottle.rtfd.io/  
**GitHub репозиторий:** https://github.com/vkbottle/vkbottle  
**PyPI страница:** https://pypi.org/project/vkbottle/

---

## Версия библиотеки

- Текущая версия в проекте: `vkbottle==4.8.1`
- Последняя версия на PyPI: `4.8.2`

---

## Извлечение вложений из сообщений

### Структура объекта Message

В vkbottle 4.x объект `Message` содержит поле `attachments`, которое представляет собой список объектов типа `MessageAttachment`.

```python
from vkbottle.bot import Bot, Message

@bot.on.message()
async def handle_message(message: Message):
    # Проверка наличия вложений
    if message.attachments:
        for attachment in message.attachments:
            print(f"Тип вложения: {attachment.type}")
```

### Helper-методы для извлечения вложений

VKBottle предоставляет удобные методы для извлечения вложений определенного типа:

#### 1. Фотографии

```python
def get_photo_attachments(self) -> list[PhotosPhoto] | None:
    """Возвращает список фотографий из вложений сообщения"""
    if self.attachments is None:
        return None
    return [attachment.photo for attachment in self.attachments if attachment.photo]
```

**Пример использования:**

```python
from vkbottle.bot import Message

@bot.on.message()
async def handle_photos(message: Message):
    photos = message.get_photo_attachments()
    if photos:
        for photo in photos:
            # Получаем ID и owner_id для формирования строки вложения
            photo_id = photo.id
            owner_id = photo.owner_id
            access_key = photo.access_key  # Может быть None
            
            # Формируем строку вложения для отправки в другие сообщения
            # Формат: "photo{owner_id}_{id}_{access_key}"
            attachment_string = f"photo{owner_id}_{photo_id}"
            if access_key:
                attachment_string += f"_{access_key}"
            
            # Получаем URL фотографии
            # images - это список доступных размеров
            if photo.images:
                for image in photo.images:
                    print(f"Размер: {image.type}, URL: {image.url}")
                # image.url - прямая ссылка на фото
                # image.width, image.height - размеры
            # Или используем готовые поля для популярных размеров:
            # photo.photo_256, photo.photo_1280 и т.д.
```

#### 2. Документы

```python
def get_doc_attachments(self) -> list[DocsDoc] | None:
    """Возвращает список документов из вложений сообщения"""
    if self.attachments is None:
        return None
    return [attachment.doc for attachment in self.attachments if attachment.doc]
```

**Пример использования:**

```python
from vkbottle.bot import Message

@bot.on.message()
async def handle_docs(message: Message):
    docs = message.get_doc_attachments()
    if docs:
        for doc in docs:
            # Основная информация о документе
            doc_id = doc.id
            owner_id = doc.owner_id
            title = doc.title  # Название документа
            size = doc.size  # Размер в байтах
            ext = doc.ext  # Расширение файла
            
            # URL для скачивания документа
            download_url = doc.url
            
            # Предпросмотр документа (если доступен)
            preview = doc.preview  # type: ignore
            
            # Формируем строку вложения
            attachment_string = f"doc{owner_id}_{doc_id}"
            if doc.access_key:
                attachment_string += f"_{doc.access_key}"
```

#### 3. Другие типы вложений

```python
# Видео
def get_video_attachments(self) -> list[VideoVideoFull] | None:
    if self.attachments is None:
        return None
    return [attachment.video for attachment in self.attachments if attachment.video]

# Аудио
def get_audio_attachments(self) -> list[AudioAudio] | None:
    if self.attachments is None:
        return None
    return [attachment.audio for attachment in self.attachments if attachment.audio]

# Аудиосообщения (голосовые)
def get_audio_message_attachments(self) -> list[MessagesAudioMessage] | None:
    if self.attachments is None:
        return None
    return [
        attachment.audio_message for attachment in self.attachments if attachment.audio_message
    ]
```

---

## Поля объектов вложений

### PhotosPhoto (фотография)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | int | ID фотографии |
| `owner_id` | int | ID владельца |
| `access_key` | str \| None | Ключ доступа |
| `album_id` | int | ID альбома |
| `date` | int | Дата загрузки (timestamp) |
| `images` | list[PhotosImage] \| None | Список доступных размеров |
| `photo_256` | str \| None | URL фото 256px |
| `photo_1280` | str \| None | URL фото 1280px |
| `height` | int | Высота (для основного размера) |
| `width` | int | Ширина (для основного размера) |

### PhotosImage (размер фотографии)

| Поле | Тип | Описание |
|------|-----|----------|
| `url` | str | Прямая ссылка на изображение |
| `width` | int | Ширина изображения |
| `height` | int | Высота изображения |
| `type` | str | Тип размера (m, x, y, z, w, q, t, s, m, o, p, r, c, e, k, l, a, h, i, j, n, b, d, f, g) |

### DocsDoc (документ)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | int | ID документа |
| `owner_id` | int | ID владельца |
| `access_key` | str \| None | Ключ доступа |
| `title` | str | Название документа |
| `size` | int | Размер файла в байтах |
| `ext` | str | Расширение файла |
| `date` | int | Дата загрузки (timestamp) |
| `type` | int | Тип документа |
| `url` | str | URL для скачивания |
| `preview` | DocsPreview \| None | Предпросмотр (для некоторых типов) |
| `is_licensed` | bool | Лицензионный ли документ |
| `tags` | list[str] | Теги документа |

---

## Скачивание вложений

### Скачивание фотографий

```python
import aiohttp
from pathlib import Path

async def download_photo(api, photo: PhotosPhoto, save_dir: Path):
    """Скачивает фотографию и сохраняет на диск"""
    
    # ==========  Устаревший вариант:  ДЛЯ vkbottle==4.8.1 НЕ АКТУАЛЬНО !!!  =============
    # Получаем URL максимального размера
    if photo.images:
        # Сортируем по размеру и берем самый большой
        largest_image = max(photo.images, key=lambda x: x.width * x.height)
        url = largest_image.url
    else:
        # Фоллбэк на photo_1280 или photo_256
        url = photo.photo_1280 or photo.photo_256

    # ===============  Вариант, АКТУАЛЬНЫЙ в vkbottle==4.8.1  ====================
    url = photo.orig_photo.to_dict().get('url', None)
    
    if not url:
        raise ValueError("No URL available for this photo")
    
    # Скачиваем файл
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                # Генерируем имя файла
                filename = f"photo_{photo.owner_id}_{photo.id}.jpg"
                save_path = save_dir / filename
                
                # Сохраняем
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(await response.read())
                return save_path
            else:
                raise Exception(f"Failed to download photo: {response.status}")
```

### Скачивание документов

```python
async def download_document(api, doc: DocsDoc, save_dir: Path):
    """Скачивает документ и сохраняет на диск"""
    url = doc.url
    
    if not url:
        raise ValueError("No URL available for this document")
    
    # Скачиваем файл
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                # Генерируем имя файла
                filename = f"{doc.title}.{doc.ext}" if doc.ext else doc.title
                save_path = save_dir / filename
                
                # Сохраняем
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(await response.read())
                return save_path
            else:
                raise Exception(f"Failed to download document: {response.status}")
```

---

## Полный пример обработчика сообщений с вложениями

```python
import aiohttp
from pathlib import Path
from vkbottle.bot import Bot, Message
from vkbottle_types.objects import PhotosPhoto, DocsDoc

# Директория для скачивания вложений
DOWNLOAD_DIR = Path("./downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

@bot.on.message()
async def handle_attachments(message: Message):
    """Обработчик всех типов вложений"""
    response_parts = []
    
    # Обработка фотографий
    photos = message.get_photo_attachments()
    if photos:
        response_parts.append(f"📸 Найдено {len(photos)} фото(о):")
        for i, photo in enumerate(photos, 1):
            # Получаем самый большой размер
            if photo.images:
                largest = max(photo.images, key=lambda x: x.width * x.height)
                response_parts.append(f" {i}. Размер: {largest.width}x{largest.height}, URL: {largest.url}")
            else:
                response_parts.append(f" {i}. ID: {photo.id}, Owner: {photo.owner_id}")
    
    # Обработка документов
    docs = message.get_doc_attachments()
    if docs:
        response_parts.append(f"\n📄 Найдено {len(docs)} документ(а):")
        for i, doc in enumerate(docs, 1):
            response_parts.append(f" {i}. {doc.title} ({doc.size} байт, .{doc.ext})")
            if doc.url:
                response_parts.append(f" URL: {doc.url}")
    
    # Отправляем ответ
    if response_parts:
        await message.answer("\n".join(response_parts))
    else:
        await message.answer("❌ В этом сообщении нет поддерживаемых вложений")

@bot.on.message()
async def download_all_attachments(message: Message):
    """Пример скачивания всех вложений"""
    await message.answer("⬇️ Начинаю скачивание вложений...")
    
    downloaded = []
    errors = []
    
    # Скачиваем фотографии
    photos = message.get_photo_attachments()
    if photos:
        for photo in photos:
            try:
                path = await download_photo(message.ctx_api, photo, DOWNLOAD_DIR / "photos")
                downloaded.append(f"✅ Фото: {path.name}")
            except Exception as e:
                errors.append(f"❌ Фото {photo.id}: {str(e)}")
    
    # Скачиваем документы
    docs = message.get_doc_attachments()
    if docs:
        for doc in docs:
            try:
                path = await download_document(message.ctx_api, doc, DOWNLOAD_DIR / "docs")
                downloaded.append(f"✅ Документ: {path.name}")
            except Exception as e:
                errors.append(f"❌ Документ {doc.id}: {str(e)}")
    
    # Формируем итоговый ответ
    result = []
    if downloaded:
        result.append("✅ Скачано:")
        result.extend(downloaded)
    if errors:
        result.append("\n⚠️ Ошибки:")
        result.extend(errors)
    
    await message.answer("\n".join(result) if result else "❌ Нет вложений для скачивания")

async def download_photo(api, photo: PhotosPhoto, save_dir: Path) -> Path:
    """Скачивает фотографию"""
    if photo.images:
        largest_image = max(photo.images, key=lambda x: x.width * x.height)
        url = largest_image.url
    else:
        url = photo.photo_1280 or photo.photo_256
    
    if not url:
        raise ValueError("No URL available")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            
            filename = f"photo_{photo.owner_id}_{photo.id}.jpg"
            save_path = save_dir / filename
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = await response.read()
            with open(save_path, 'wb') as f:
                f.write(content)
            return save_path

async def download_document(api, doc: DocsDoc, save_dir: Path) -> Path:
    """Скачивает документ"""
    if not doc.url:
        raise ValueError("No URL available")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(doc.url) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            
            filename = f"{doc.title}.{doc.ext}" if doc.ext else doc.title
            save_path = save_dir / filename
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = await response.read()
            with open(save_path, 'wb') as f:
                f.write(content)
            return save_path
```

---

## Формирование строки вложения

Для отправки вложений в другие сообщения используется специальная строка формата:

```
{type}{owner_id}_{id}_{access_key}
```

Где:
- `type` - тип вложения: `photo`, `doc`, `video`, `audio` и т.д.
- `owner_id` - ID владельца (пользователь или сообщество, со знаком минус)
- `id` - ID вложения у владельца
- `access_key` - ключ доступа (опционально, только если есть)

### Пример формирования строки:

```python
def get_attachment_strings(self) -> list[str] | None:
    """Возвращает список строк вложений в формате VK API"""
    if self.attachments is None:
        return None
    
    attachments = []
    for attachment in self.attachments:
        attachment_type = attachment.type.value
        attachment_object = getattr(attachment, attachment_type)
        
        if not hasattr(attachment_object, "id") or not hasattr(attachment_object, "owner_id"):
            continue
        
        attachment_string = f"{attachment_type}{attachment_object.owner_id}_{attachment_object.id}"
        
        if hasattr(attachment_object, "access_key"):
            access_key = attachment_object.access_key
            if access_key:
                attachment_string += f"_{access_key}"
        
        attachments.append(attachment_string)
    
    return attachments

# Пример использования:
# attachments_str = message.get_attachment_strings()
# await message.answer("Ответ с вложением", attachment=attachments_str[0])
```

---

## Полезные ссылки

- [VKBottle Tutorial - Обработчики](https://vkbottle.rtfd.io/en/latest/high-level/bot/labeler/)
- [VKBottle Tutorial - Клавиатуры и вложения](https://vkbottle.rtfd.io/en/latest/tutorial/keyboards-attachments/)
- [VK API Documentation - Messages](https://dev.vk.com/en/reference/messages)
- [VK API Documentation - Photos](https://dev.vk.com/en/reference/photos)
- [VK API Documentation - Docs](https://dev.vk.com/en/reference/docs)
