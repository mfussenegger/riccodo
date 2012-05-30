#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import posixpath
from markdown import Markdown
from argh import command, ArghParser
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader


URL = ''


class MarkdownReader(object):
    METADATA = {
        'template': lambda x: str(x).strip(),
        'sort:': lambda x: str(x).strip(),
        'title': lambda x: str(x).strip(),
        'parent:': lambda x: str(x).strip(),
        'in_nav': lambda x: True if x == '1' or x == 'true' else False
    }
    extensions = ['codehilite', 'extra']

    def __init__(self, path):
        self.path = path
        if not self.path.endswith('/'):
            self.path = self.path + '/'

    def process_metadata(self, name, value):
        if name in self.METADATA:
            return self.METADATA[name](value)
        return value

    def read(self, filename):
        """Parses the given file and returns a :class:`Page` object

        :param filename: path to the file to read.
        :type filename: str.
        :returns: Page
        """
        text = open(filename, 'r', encoding='utf-8').read()
        md = Markdown(extensions=set(self.extensions + ['meta']))
        content = md.convert(text)

        metadata = {}
        for name, value in md.Meta.items():
            name = name.lower()
            metadata[name] = self.process_metadata(name, value[0])
        return Page(filename.replace(self.path, ''),
                    content,
                    metadata.get('title'),
                    metadata.get('template'),
                    metadata.get('parent'),
                    metadata.get('sort'),
                    metadata.get('in_nav'))


class Page(object):
    def __init__(self,
                 path,
                 content,
                 title,
                 template,
                 parent_name,
                 sort,
                 in_nav):
        self.path = path.replace('.md', '.html')
        self.url = '{0}/{1}'.format(URL, path.replace('.md', '.html'))
        self.name = os.path.basename(path.replace('.md', ''))
        self.title = title or self.name
        self.content = content
        self.template = template
        self.parent_name = parent_name
        self.sort = sort or 1
        self.children = []
        self.in_nav = 1 if in_nav == None else in_nav

    def __repr__(self):
        return repr(str(self))

    def __str__(self):
        return '<Page {0}>'.format(self.name)

    def descendants(self):
        for p in self.children:
            yield p
            for c in p.descendants():
                yield c


def get_pages(path):
    mdr = MarkdownReader(path)
    pages = []

    for root, _, files in os.walk(path):
        for fi in files:
            path = os.path.join(root, fi)
            pages.append(mdr.read(path))

    return pages


def build_page_tree(pages):
    parent_names = set([x.parent_name for x in pages
               if x.parent_name and x.parent_name.strip() != ''])
    pages_flat = pages[:]
    for page in pages_flat:
        if page.name in parent_names:
            page.children = [x for x in pages_flat if x.parent_name == page.name]
        if page.parent_name:
            pages.remove(page)

    return pages, pages_flat


def write_html(page_tree, pages_flat, templates, output):
    env = Environment(loader=FileSystemLoader(templates))
    for page in pages_flat:
        env.globals['get_url'] = lambda x: get_url(page.url, x)

        template = env.get_template(page.template)
        content = template.render({'page': page, 'pages': page_tree})

        path = os.path.join(output, page.path)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)


def get_url(current, target):
    current = urlparse(current).path
    target = urlparse(target).path

    result = posixpath.relpath(target, current).split('/')
    result = '/'.join(result[1:])
    return result


@command
def gen(content, templates, output):
    pages = get_pages(content)
    page_tree, pages_flat = build_page_tree(pages)
    write_html(page_tree, pages_flat, templates, output)


def main():
    p = ArghParser()
    p.add_commands([gen])
    p.dispatch()


if __name__ == '__main__':
    main()
