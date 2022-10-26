from typing import Any

from rest_framework.request import HttpRequest


class Base:
    type = "generic"

    def __init__(self, label, many=False, frontend_only=False, default=None) -> None:
        self.name = None
        self.label = label
        self.many = many
        self.frontend_only = frontend_only
        self.default = default

    def render_meta(self):
        return {
            "label": self.label,
            "type": self.type,
            "many": self.many,
            "frontend_only": self.frontend_only,
            "default": self.default,
        }

    def parse_request(self, request: HttpRequest) -> Any:
        if self.many:
            return request.GET.getlist(self.name, [])
        return request.GET.get(self.name, None)


class Text(Base):
    type = "text"
