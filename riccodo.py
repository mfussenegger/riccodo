#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from markdown import Markdown

from jinja2 import Environment, FileSystemLoader

PATH_CONTENT = '../site/content/'
PATH_TEMPLATES = '../site/templates/'


class MarkdownReader(object):
    METADATA = {
        'template': lambda x: str(x).strip(),
        'sort:': lambda x: str(x).strip(),
        'title': lambda x: str(x).strip(),
        'parent:': lambda x: str(x).strip(),
        'in_nav': lambda x: True if x == '1' or x == 'true' else False
    }
    extensions = ['codehilite', 'extra']

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
        return Page(''.join(filename.split('.')[:-1]),
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
        self.path = path
        self.url = get_url(self.path) + '.html'
        self.name = os.path.basename(path)
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


def get_pages():
    mdr = MarkdownReader()
    pages = []

    for root, dirs, files in os.walk(PATH_CONTENT):
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


def get_url(path):
    return '..{0}'.format(path.replace(PATH_CONTENT, ''))


def in_path(page, children):
    if page in children:
        return True
    for child in children:
        if child.children:
            return in_path(page, child.children)
    return False


def write_html(page_tree, pages_flat):
    env = Environment(loader=FileSystemLoader(PATH_TEMPLATES))
    env.globals['get_url'] = get_url
    env.globals['in_path'] = in_path
    for page in pages_flat:
        template = env.get_template(page.template)
        content = template.render({'page': page, 'pages': page_tree})
        path = '.{0}.html'.format(page.path.replace(PATH_CONTENT, 'output'))
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)


def main():
    pages = get_pages()
    page_tree, pages_flat = build_page_tree(pages)
    write_html(page_tree, pages_flat)

if __name__ == '__main__':
    main()
