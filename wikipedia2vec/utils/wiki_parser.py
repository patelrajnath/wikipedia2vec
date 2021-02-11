import functools

import mwparserfromhell.nodes as nodes

from datetime import date
from typing import Union
from mwparserfromhell.wikicode import Wikicode

WikiValue = Union[str, list, dict, None, date, tuple]


@functools.singledispatch
def parse_wikicode(obj):
    raise NotImplementedError(type(obj))


@parse_wikicode.register(Wikicode)
def _(obj: Wikicode) -> WikiValue:
    parsed_nodes = [parse_wikicode(node) for node in obj.nodes]
    parsed_nodes = [node for node in parsed_nodes if node is not None]
    parsed_nodes = list_clean(parsed_nodes)

    if isinstance(parsed_nodes, list) and all(isinstance(x, str) for x in parsed_nodes):
        parsed_nodes = ''.join(parsed_nodes).strip()

    return parsed_nodes


@parse_wikicode.register(nodes.Text)
def _(obj: nodes.Text) -> str:
    return str(obj.value)


def list_lstrip(l: list):
    if len(l) == 0:
        return []

    first = l[0]
    if isinstance(first, str):
        first = first.lstrip()
        if first == '':
            return list_lstrip(l[1:])
        else:
            return [first, *l[1:]]
    else:
        return l


def list_rstrip(l: list):
    if len(l) == 0:
        return []

    last = l[-1]
    if isinstance(last, str):
        last = last.rstrip()
        if last == '':
            return list_rstrip(l[:-1])
        else:
            return [*l[:-1], last]
    else:
        return l


def list_strip(l: list):
    return list_lstrip(list_rstrip(l))


def list_collapse(l: list, total_collapse=False):
    if len(l) == 0:
        return None
    elif len(l) == 1:
        return l[0]
    elif total_collapse and all(isinstance(x, str) for x in l):
        return ''.join(l)
    else:
        return l


def list_clean(l: list, total_collapse=False) -> Union[list, object, None]:
    l = [x for x in l if x is not None]
    return list_collapse(list_strip(l), total_collapse)


@parse_wikicode.register(nodes.Template)
def _(obj: nodes.Template) -> WikiValue:
    try:
        template_name = str(obj.name).strip().lower()
        if template_name == 'plainlist' or template_name == 'plain list':
            item = None
            items = []
            for node in obj.params[0].value.nodes:
                if isinstance(node, nodes.Tag) and node.tag == 'li':
                    if item is not None:
                        items.append(item)
                    item = []
                elif item is not None:
                    item.append(node)
            items.append(item)
            return [(list_clean([parse_wikicode(item_part) for item_part in item]),) for item in items]
        elif template_name == 'citation needed':
            return None
        elif template_name == 'unbulleted list':
            return [(parse_wikicode(param.value),) for param in obj.params]
        elif template_name == 'birth date and age':
            return date(*[int(str(param.value)) for param in obj.params if str(param.value).isdigit()])
        elif template_name == 'marriage':
            # Params 1-3 contain start/end and reasons therefore
            return parse_wikicode(obj.params[0].value)
        elif template_name == 'url':
            return parse_wikicode(obj.params[0].value)
        elif template_name == 'flag':
            return parse_wikicode(obj.params[0].value)
        elif template_name == 'convert':
            if str(obj.params[2]).isdigit():
                params = obj.params[0:4]
            else:
                params = obj.params[0:2]
            return tuple(parse_wikicode(param.value) for param in params)
        elif template_name == 'based on':
            return tuple(parse_wikicode(param.value) for param in obj.params)
        elif template_name == 'film date':
            return date(*[int(str(param.value)) for param in obj.params if str(param.value).isdigit()])
        elif template_name == 'nbay':
            return str(obj.params[0])
        else:
            return f'Template({template_name})'
    except:
        return None


@parse_wikicode.register(nodes.ExternalLink)
def _(obj: nodes.ExternalLink):
    if not obj.title:
        return None
    return obj.title.strip_code()


@parse_wikicode.register(nodes.Wikilink)
def _(obj: nodes.Wikilink) -> WikiValue:
    return parse_wikicode(obj.text) if obj.text else parse_wikicode(obj.title)


@parse_wikicode.register(nodes.Tag)
def _(obj: nodes.Tag) -> WikiValue:
    if obj.tag == 'ref':
        return None
    elif obj.tag in ['small', 'i', 'b']:
        return parse_wikicode(obj.contents)
    elif obj.tag == 'br':
        return ' '
    return f'Tag({obj.tag})'


@parse_wikicode.register(nodes.Comment)
def _(obj: nodes.Comment) -> WikiValue:
    return None


@parse_wikicode.register(nodes.HTMLEntity)
def _(obj: nodes.HTMLEntity) -> WikiValue:
    return None


@parse_wikicode.register(nodes.Argument)
def _(obj: nodes.Argument) -> WikiValue:
    return None


@parse_wikicode.register(nodes.Heading)
def _(obj: nodes.Heading) -> WikiValue:
    return None