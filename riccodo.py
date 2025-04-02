#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import posixpath
import argparse
from markdown import Markdown
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader


URL = ''


class MarkdownReader(object):
    METADATA = {
        'template': lambda x: str(x).strip(),
        'sort:': lambda x: str(x).strip(),
        'title': lambda x: str(x).strip(),
        'title_short': lambda x: str(x).strip(),
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
        try:
            text = open(filename, 'r', encoding='utf-8').read()
        except UnicodeDecodeError:
            print('wrong encoding: {0}'.format(filename))
            raise
        md = Markdown(extensions=set(self.extensions + ['meta']))
        content = md.convert(text)

        metadata = {}
        for name, value in md.Meta.items():
            name = name.lower()
            metadata[name] = self.process_metadata(name, value[0])
        return Page(filename.replace(self.path, ''),
                    content,
                    metadata.get('title'),
                    metadata.get('title_short'),
                    metadata.get('template'),
                    metadata.get('parent'),
                    metadata.get('sort'),
                    metadata.get('in_nav'))


class Page(object):
    def __init__(self,
                 path,
                 content,
                 title,
                 title_short,
                 template,
                 parent_name,
                 sort,
                 in_nav):
        self.path = path.replace('.md', '.html')
        self.url = '{0}/{1}'.format(URL, self.path)
        self.name = os.path.basename(path.replace('.md', ''))
        self.title = title or self.name
        self.title_short = title_short or title
        self.content = content
        assert template is not None, 'Template is required: {0}'.format(path)
        self.template = template
        self.parent_name = parent_name
        if sort:
            self.sort = int(sort)
        else:
            self.sort = 1
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
            try:
                pages.append(mdr.read(path))
            except AttributeError:
                print('could not parse {0}'.format(path))
                continue

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


def copy_static(source, target):
    source = os.path.join(source, 'static')
    target = os.path.join(target, 'static')

    try:
        shutil.rmtree(target)
    except OSError:
        pass

    if os.path.exists(source):
        shutil.copytree(source, target)


def gen(content, templates, output, nostatic=False):
    print('Generating content...')
    if not nostatic:
        copy_static(templates, output)
    pages = get_pages(content)
    page_tree, pages_flat = build_page_tree(pages)
    write_html(page_tree, pages_flat, templates, output)
    print('Done.')


def main():
    parser = argparse.ArgumentParser("riccodo")
    parser.add_argument("--content", type=str, required=True)
    parser.add_argument("--templates", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--no-static", action="store_true")
    args = parser.parse_args()
    gen(args.content, args.templates, args.output, args.no_static)


if __name__ == '__main__':
    main()
