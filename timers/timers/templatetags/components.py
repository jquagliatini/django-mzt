import enum
from typing import cast, Any
from django import template
from django.forms import ValidationError

class ComponentEnum(enum.StrEnum):
  button = 'button'
  input = 'input'

register = template.Library()

@register.simple_tag
def cx(name: ComponentEnum, **kwargs: Any) -> str:
  classes: str = ""
  if name == ComponentEnum.button:
    variant = kwargs.get('variant')

    classes = "cursor-pointer rounded px-3 py-2 text-xs uppercase duration-100 transition-colors"
    if variant is None or variant == 'primary':
      classes += " bg-red-400 hover:bg-red-300 text-white dark:bg-red-800 dark:hover:bg-red-700"
    elif variant == 'secondary':
      classes += " bg-white text-gray-900 border border-gray-400 dark:bg-neutral-900 dark:hover:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-200"
    elif variant == 'neutral':
      classes += " bg-gray-200 hover:bg-gray-100 text-gray-900"
    else:
      raise ValidationError(f"Unknown variant '{variant}'")

  elif name == ComponentEnum.input:
    is_disabled = cast(bool, kwargs.get('is_disabled') == 'True')

    classes = "py-1.5 sm:py-2 px-3 border-gray-200 rounded-md sm:text-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-neutral-900 dark:border-neutral-700 dark:text-neutral-200 dark:placeholder-neutral-500 dark:focus:ring-neutral-600"
    if is_disabled:
      classes += " disabled:opacity-50 disabled:pointer-events-none"

  else:
    raise ValidationError(f"Unknown component '{name}'")
    
  return classes




