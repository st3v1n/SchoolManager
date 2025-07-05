from django import template

register = template.Library()

@register.filter
def getattr(obj, attr):
    """Custom filter to get attribute of an object."""
    try:
        return getattr(obj, attr)
    except AttributeError:
        return None

@register.filter
def getitem(dictionary, key):
    """Retrieve an item from a dictionary by key (for use in Django templates)."""
    return dictionary.get(str(key), None)  # Ensure key is a string and return None if not found
