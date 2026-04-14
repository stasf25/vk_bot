"""
FAISS Vector Store для хранения и поиска векторов.
"""

import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import json

import faiss
import numpy as np
from faiss import IndexFlatL2, IndexIDMap, normalize_L2

from config import FAISS_INDEX_PATH, FAISS_METADATA_PATH, LOG_LEVEL, LOG_FORMAT

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logger = logging.getLogger(__name__)

@dataclass
class FAISSConfig:
    """Конфигурация FAISS"""
    index_path: str = FAISS_INDEX_PATH
    metadata_path: str = FAISS_METADATA_PATH

class FAISSVectorStore:
    """
    FAISS Vector Store для хранения и поиска векторов.
    """

    def __init__(self, config: FAISSConfig = None):
        self.config = config or FAISSConfig()
        self.index = None
        self.metadata = []  # Метаданные документов
        
        logger.info(f"Инициализация FAISSVectorStore")
        logger.info(f"Путь к индексу: {self.config.index_path}")
        logger.info(f"Путь к метаданным: {self.config.metadata_path}")
    
    def create_index(self, dimension: int):
        """
        Создает новый пустой FAISS индекс.
        
        Args:
            dimension: Размерность векторов эмбеддингов (например, 1536)
        """
        # IndexFlatL2 - простой индекс с L2 (евклидовой) метрикой расстояния
        # Для больших баз можно использовать IndexIVFFlat или другие типы
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []
        logger.info(f"Создан новый FAISS индекс с размерностью {dimension}")
    
    def add_documents(self, texts: List[str], embeddings: List[List[float]], 
                     sources: List[str] = None):
        """
        Добавляет документы в векторное хранилище.
        
        Args:
            texts: Список текстов документов
            embeddings: Список векторов эмбеддингов для этих текстов
            sources: Список источников (имена файлов) для каждого документа
        """
        if self.index is None:
            raise ValueError("Индекс не инициализирован. Сначала вызовите create_index().")
        
        if not texts or not embeddings:
            logger.warning("Попытка добавить пустой список документов")
            return
        
        if len(texts) != len(embeddings):
            raise ValueError("Количество текстов и эмбеддингов должно совпадать")
        
        # Преобразуем эмбеддинги в numpy массив (требуется для FAISS)
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Добавляем векторы в FAISS индекс
        self.index.add(embeddings_array)
        
        # Сохраняем метаданные для каждого документа
        for i, text in enumerate(texts):
            metadata_item = {
                "text": text,
                "source": sources[i] if sources else f"doc_{i}",
                "index": len(self.metadata)
            }
            self.metadata.append(metadata_item)
        
        logger.info(f"Добавлено {len(texts)} документов в векторное хранилище")
        logger.info(f"Всего документов в хранилище: {len(self.metadata)}")
    
    def search(self, query_embedding: List[float], k: int = 3) -> List[Tuple[str, str, float]]:
        """
        Ищет наиболее похожие документы по запросу.
        
        Args:
            query_embedding: Вектор эмбеддинга запроса пользователя
            k: Количество наиболее похожих документов для возврата
            
        Returns:
            Список кортежей (текст документа, источник, расстояние/релевантность)
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Индекс пуст, невозможно выполнить поиск")
            return []
        
        # Преобразуем запрос в numpy массив нужной формы
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Выполняем поиск k ближайших соседей
        distances, indices = self.index.search(query_array, min(k, self.index.ntotal))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                metadata = self.metadata[idx]
                distance = float(distances[0][i])
                results.append((metadata["text"], metadata["source"], distance))
        
        logger.info(f"Найдено {len(results)} релевантных документов")
        return results
    
    def save(self):
        """
        Сохраняет индекс и метаданные на диск.
        """
        if self.index is None:
            logger.warning("Нечего сохранять - индекс не инициализирован")
            return
        
        try:
            # Создаем директории если их нет
            self.config.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.config.metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Сохраняем FAISS индекс с использованием абсолютного пути
            index_path_str = str(self.config.index_path.absolute())
            faiss.write_index(self.index, index_path_str)
            logger.info(f"FAISS индекс сохранен в {self.config.index_path}")
            
            # Сохраняем метаданные в JSON
            with open(self.config.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"Метаданные сохранены в {self.config.metadata_path}")

        except Exception as e:
            logger.error(f"Ошибка при сохранении: {e}")
            # Пробуем альтернативный метод для Windows с кириллицей
            try:
                import tempfile
                import shutil
                
                logger.info("Пытаемся сохранить через временный файл...")
                
                # Сохраняем во временный файл
                with tempfile.NamedTemporaryFile(delete=False, suffix='.faiss') as tmp_file:
                    temp_path = tmp_file.name
                    faiss.write_index(self.index, temp_path)
                
                # Копируем из временного в целевой
                shutil.move(temp_path, str(self.config.index_path))
                logger.info(f"FAISS индекс сохранен через временный файл в {self.config.index_path}")
                
                # Сохраняем метаданные
                with open(self.config.metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata, f, ensure_ascii=False, indent=2)
                logger.info(f"Метаданные сохранены в {self.config.metadata_path}")
                
            except Exception as e2:
                logger.error(f"Не удалось сохранить даже через временный файл: {e2}")
                raise
    
    def load(self) -> bool:
        """
        Загружает индекс и метаданные с диска.
        
        Returns:
            True если загрузка успешна, False если файлы не найдены
        """
        if not self.config.index_path.exists() or not self.config.metadata_path.exists():
            logger.warning(f"Файлы индекса не найдены")
            return False
        
        try:
            # Загружаем FAISS индекс
            self.index = faiss.read_index(str(self.config.index_path))
            logger.info(f"FAISS индекс загружен из {self.config.index_path}")
            logger.info(f"Количество векторов в индексе: {self.index.ntotal}")
            
            # Загружаем метаданные
            with open(self.config.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            logger.info(f"Метаданные загружены из {self.config.metadata_path}")
            logger.info(f"Количество документов в метаданных: {len(self.metadata)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке индекса: {e}")
            return False
    
    def get_stats(self) -> dict:
        """
        Возвращает статистику индекса.

        Returns:
            Словарь со статистикой
        """
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "total_documents": len(self.metadata),
            "dimension": self.index.d if self.index else 0,
            "index_exists": self.config.index_path.exists(),
            "metadata_exists": self.config.metadata_path.exists()
        }