import enum
from typing import Any
from django import template
import timers.lib.classes as c

class UnknownComponentException(BaseException):
  pass

class ComponentEnum(enum.StrEnum):
  button = 'button'
  input = 'input'

register = template.Library()

@register.simple_tag
def cx(name: ComponentEnum, **kwargs: Any) -> str:
  if name == ComponentEnum.button:
    return c.button(**kwargs)
  elif name == ComponentEnum.input:
    return c.input(**kwargs)
  else:
    raise UnknownComponentException(name)
