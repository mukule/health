from django import template

register = template.Library()

@register.filter
def get_color(colors, index):
    if len(colors) == 0:
        return ''  # Return an empty string if colors list is empty
    return colors[index % len(colors)]
