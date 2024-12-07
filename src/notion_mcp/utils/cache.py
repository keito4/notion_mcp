from typing import Dict, Optional
import logging
import json
import os

logger = logging.getLogger('notion_mcp')


class RelationCache:
    CACHE_FILE = os.path.join(os.path.dirname(__file__), '.notion_mcp')

    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._load_cache_from_file()

    def _load_cache_from_file(self):
        try:
            with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                self._cache = json.load(f)
            logger.debug(f"Cache loaded from {self.CACHE_FILE}")
            return self._cache
        except OSError as e:
            logger.error(f"Failed to read cache from {self.CACHE_FILE}: {e}")
            return {}

    def _dump_cache_to_file(self):
        try:
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cache written to {self.CACHE_FILE}")
        except OSError as e:
            logger.error(f"Failed to write cache to {self.CACHE_FILE}: {e}")

    def get_name(self, database_id: str, relation_id: str) -> Optional[str]:
        cache = self._load_cache_from_file()
        logger.debug(
            f"Getting name for {database_id}:{relation_id} from cache({cache}, {self._cache})")
        return cache.get(f"{database_id}:{relation_id}")

    def set_name(self, database_id: str, relation_id: str, name: str):
        self._cache[f"{database_id}:{relation_id}"] = name
        self._dump_cache_to_file()

    def bulk_set(self, database_id: str, items: Dict[str, str]):
        for rid, rname in items.items():
            self.set_name(database_id, rid, rname)
        logger.info(
            f"Cached {len(items)} relations for database {database_id}")

    def exists(self, database_id: str, relation_id: str) -> bool:
        return (f"{database_id}:{relation_id}" in self._cache)
