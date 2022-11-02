from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dateutil.parser import parse as parse_date
from rest_framework.request import HttpRequest

if TYPE_CHECKING:
    from .views import MapApiBaseView


class Base:
    type = "generic"

    def __init__(self, label, many=False, frontend_only=False, default=None) -> None:
        self.name = None
        self.label = label
        self.many = many
        self.frontend_only = frontend_only
        self.default = default

    def render_meta(
        self, view: MapApiBaseView, request: HttpRequest
    ):  # pylint: disable=unused-argument
        return {
            "label": self.label,
            "type": self.type,
            "many": self.many,
            "frontend_only": self.frontend_only,
            "default": self.default,
        }

    def parse_request(self, request: HttpRequest) -> Any:
        if self.many:
            return [
                self.unserialize(value) for value in request.GET.getlist(self.name, [])
            ]
        return self.unserialize(request.GET.get(self.name, None))

    def unserialize(self, value):
        return value


class Text(Base):
    type = "text"


class DateRange(Base):
    type = "date_range"

    def unserialize(self, value):
        if not value:
            return None
        dates = value.split(" ")
        return parse_date(dates[0]), parse_date(dates[1])


class Date(Base):
    type = "date"

    def unserialize(self, value):
        if not value:
            return None
        return parse_date(value)


class Select(Base):
    type = "select"

    def __init__(  # pylint: disable=too-many-arguments
        self, label, many=False, frontend_only=False, default=None, choices=None
    ) -> None:
        super().__init__(label, many, frontend_only, default)
        self.choices = choices or {}

    def render_meta(self, view: MapApiBaseView, request: HttpRequest):
        meta = super().render_meta(view, request)
        meta = {**meta, "choices": self.render_choices(view, request)}
        return meta

    def render_choices(self, view: MapApiBaseView, request: HttpRequest) -> list:
        if callable(self.choices):
            return self.choices(view, request)
        return self.choices
