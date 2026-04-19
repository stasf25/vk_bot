"""
Embedder для создания векторных представлений через embeddings API.
"""

import json
import logging
from typing import List
from dataclasses import dataclass

import requests
from requests.exceptions import RequestException

from config import EMBED_API_URL, EMBED_API_KEY, EMBED_MODEL, EMBED_ENDPOINT, REQUEST_TIMEOUT

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logger = logging.getLogger(__name__)

@dataclass
class EmbedderConfig:
    """Конфигурация Embedder"""
    api_url: str = EMBED_API_URL
    api_key: str = EMBED_API_KEY
    model: str = EMBED_MODEL
    endpoint: str = EMBED_ENDPOINT
    timeout: int = REQUEST_TIMEOUT

class Embedder:
    """
    Embedder для создания векторных представлений через embeddings API.
    """

    def __init__(self, config: EmbedderConfig = None):
        self.config = config or EmbedderConfig()
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        self.embedding_dimension = 0
    
    @property
    def model(self):
        return self.config.model
    
    def embed_text(self, text: str) -> List[float]:
        """
        Создает эмбеддинг для одного текста через HTTP запрос.
        
        Args:
            text: Текст для преобразования в вектор
            
        Returns:
            Список чисел с плавающей точкой - вектор эмбеддинга
        """
        return self.embed_texts([text])[0]


    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Получает эмбеддинги для списка текстов через embeddings API.

        Args:
            texts: Список текстов для эмбеддингов

        Returns:
            Список эмбеддингов (каждый эмбеддинг - список float)
        """
        embeddings = []
        max_embeddings_per_request = 10  # Максимум эмбеддингов в одном запросе


        # Разбиваем на batches если нужно
        for i in range(0, len(texts), max_embeddings_per_request):
            batch = texts[i:i + max_embeddings_per_request]
            payload = {
                "model": self.config.model,
                "input": batch
            }

            try:
                response = requests.post(
                    f"{self.config.api_url}{self.config.endpoint}",
                    headers=self.headers,
                    json=payload,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                result = response.json()

                # Извлекаем эмбеддинги
                for item in result.get("data", []):
                    embedding = item.get("embedding", [])
                    if  not self.embedding_dimension  or  len(embedding) == self.embedding_dimension  >0:
                        embeddings.append(embedding)
                        self.embedding_dimension = len(embedding)
                    else:
                        logger.warning(f"Некорректный размер эмбеддинга: {len(embedding)}")

            except RequestException as e:
                logger.error(f"Ошибка при получении эмбеддингов: {e}")
                raise Exception(f"Ошибка при получении эмбеддингов: {str(e)}")
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка при парсинге ответа: {e}")
                raise Exception(f"Ошибка при парсинге ответа: {str(e)}")

        return embeddings


    def get_embedding_dimension(self) -> int:
        """
        Определяет размерность векторов эмбеддингов.
        
        Returns:
            Размерность вектора
        """
        try:
            # Создаем тестовый эмбеддинг
            test_embedding = self.embed_text("test")
            dimension = len(test_embedding)
            logger.debug(f"Размерность эмбеддингов: {dimension}")
            return dimension
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к embeddings API: {e}")
        return 0


    def test_connection(self) -> bool:
        """
        Проверяет доступность модели, заодно определяя размерность эьбеддинга.
        
        Returns:
            True/False
        """
        self.embedding_dimension = self.get_embedding_dimension()
        return  self.embedding_dimension > 0