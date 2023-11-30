from __future__ import annotations

from dataclasses import asdict, dataclass
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
            ] or None
        return self.unserialize(request.GET.get(self.name, None))

    def unserialize(self, value):
        return value


class Text(Base):
    type = "text"


class Color(Base):
    type = "color"


class DateRange(Base):
    type = "date_range"

    def unserialize(self, value):
        if not value:
            return None
        dates = value.split(" ")
        from_date = parse_date(dates[0])
        to_date = parse_date(dates[0])
        to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        return from_date, to_date


class Date(Base):
    type = "date"

    def unserialize(self, value):
        if not value:
            return None
        return parse_date(value)


class Select(Base):
    type = "select"

    @dataclass
    class Choice:
        value: str
        label: str

    def __init__(  # pylint: disable=too-many-arguments
        self, label, many=False, frontend_only=False, default=None, choices=None
    ) -> None:
        super().__init__(label, many, frontend_only, default)
        self.choices = choices or []

    def render_meta(self, view: MapApiBaseView, request: HttpRequest):
        meta = super().render_meta(view, request)
        meta = {
            **meta,
            "choices": [
                self._choice_to_dict(choice)
                for choice in self.render_choices(view, request)
            ],
        }
        return meta

    def _choice_to_dict(self, choice):
        if isinstance(choice, dict):
            return choice
        return asdict(choice)

    def render_choices(self, view: MapApiBaseView, request: HttpRequest) -> list:
        if callable(self.choices):
            return self.choices(view, request)
        return self.choices
