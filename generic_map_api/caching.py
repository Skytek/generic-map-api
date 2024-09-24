from __future__ import annotations

import hashlib
import json
from base64 import b64encode
from typing import TYPE_CHECKING, Union

from django.core.cache import DEFAULT_CACHE_ALIAS, caches

from .values import BaseViewPort

if TYPE_CHECKING:
    from .views import MapApiBaseView, MapFeaturesBaseView, MapTilesBaseView


KEY_PREFIX = "MAP_API"

NO_VALUE = object()

NO_CACHE = object()
DEFAULT_TTL = 15  # seconds


class Cache:
    def __init__(
        self,
        view: Union[MapApiBaseView, MapFeaturesBaseView, MapTilesBaseView],
        request,
    ) -> None:
        self.view = view
        self.request = request

    def _make_caching_key(self, fn_name, request, **context):
        extra = self.view.get_caching_key_extra(fn_name, request, **context)
        if extra is not None:
            context["extra"] = extra

        view_name = self.view.cache_view_name
        if not view_name:
            view_name = (
                f"{self.view.__class__.__module__}.{self.view.__class__.__name__}"
            )

        context_str = json.dumps(context, default=str)
        hasher = hashlib.sha256(context_str.encode("utf-8"))
        context_hash = b64encode(hasher.digest()).decode("utf-8")

        key = f"{KEY_PREFIX}__{view_name}__{fn_name}__{context_hash}"
        return key

    def _read_cache(self, key):
        cache_name = self.view.cache_name or DEFAULT_CACHE_ALIAS
        cache = caches[cache_name]
        return cache.get(key, NO_VALUE)

    def _write_cache(self, key, value, timeout):
        cache_name = self.view.cache_name or DEFAULT_CACHE_ALIAS
        cache = caches[cache_name]
        return cache.set(key, value, timeout)

    def get_serialized_meta(self):
        timeout = self.view.cache_ttl_meta or self.view.cache_ttl

        if timeout is NO_CACHE:
            value = NO_VALUE
        else:
            key = self._make_caching_key(
                "META",
                self.request,
            )
            value = self._read_cache(key)

        if value is NO_VALUE:
            value = self.view.get_serialized_meta()
            if timeout is not NO_CACHE:
                self._write_cache(key, value, timeout)
        return value

    def get_serialized_bounds(self, params):
        timeout = self.view.cache_ttl_bounds or self.view.cache_ttl

        if timeout is NO_CACHE:
            value = NO_VALUE
        else:
            key = self._make_caching_key(
                "BOUNDS",
                self.request,
                params=params,
            )
            value = self._read_cache(key)

        if value is NO_VALUE:
            value = self.view.get_serialized_bounds(params)
            if timeout is not NO_CACHE:
                self._write_cache(key, value, timeout)
        return value

    def get_serialized_items(self, viewport: BaseViewPort, params: dict):
        timeout = self.view.cache_ttl_items or self.view.cache_ttl

        if timeout is NO_CACHE:
            value = NO_VALUE
        else:
            key = self._make_caching_key(
                "ITEMS",
                self.request,
                viewport=viewport.to_dict(),
                params=params,
            )
            value = self._read_cache(key)

        if value is NO_VALUE:
            value = self.view.get_serialized_items(viewport, params)
            if timeout is not NO_CACHE:
                value = list(value)
                self._write_cache(key, value, timeout)
        return value

    def get_serialized_item(self, item_id):
        timeout = self.view.cache_ttl_item or self.view.cache_ttl

        if timeout is NO_CACHE:
            value = NO_VALUE
        else:
            key = self._make_caching_key(
                "ITEM",
                self.request,
                item_id=item_id,
            )
            value = self._read_cache(key)

        if value is NO_VALUE:
            value = self.view.get_serialized_item(item_id)
            if timeout is not NO_CACHE:
                self._write_cache(key, value, timeout)
        return value

    def get_tile_bytes(self, z: int, x: int, y: int, params: dict):
        timeout = self.view.cache_ttl_tile or self.view.cache_ttl

        if timeout is NO_CACHE:
            value = NO_VALUE
        else:
            key = self._make_caching_key(
                "TILE",
                self.request,
                coords=(x, y, z),
                params=params,
            )
            value = self._read_cache(key)

        if value is NO_VALUE:
            value = self.view.get_tile_bytes(z, x, y, params)
            if timeout is not NO_CACHE:
                self._write_cache(key, value, timeout)
        return value
