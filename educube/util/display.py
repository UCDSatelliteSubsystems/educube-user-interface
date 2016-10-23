import json
import click
from pygments import highlight, lexers, formatters


def _pop_safe(dictobj, key):
    if key in dictobj.keys():
        dictobj.pop(key)


def json_requested():
    click_root_context = click.get_current_context()
    while click_root_context.parent:
        click_root_context = click_root_context.parent
    if click_root_context.params['json']:
        return True
    else:
        return False


def get_standalone_mode():
    click_root_context = click.get_current_context()
    while click_root_context.parent:
        click_root_context = click_root_context.parent
    if click_root_context.params['standalone_mode']:
        return True
    else:
        return False


def display_color_json(json_obj):
    formatted_json = json.dumps(json_obj, sort_keys=True, indent=4)
    colorful_json = highlight(unicode(formatted_json, 'UTF-8'), lexers.JsonLexer(), formatters.TerminalFormatter())
    return colorful_json


