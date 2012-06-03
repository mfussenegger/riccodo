# encoding: utf-8

import unittest
import riccodo.riccodo as riccodo


def get_pages():
    p1 = riccodo.Page('page1.md',
                'content',
                'page1',
                'red.html',
                None,
                1,
                1)
    p2 = riccodo.Page('page2.md',
                'content',
                'page2',
                'red.html',
                'page1',
                1,
                1)

    p3 = riccodo.Page('page3.md',
                'content',
                'page3',
                'red.html',
                'page2',
                1,
                1)

    p4 = riccodo.Page('page4.md',
                'content',
                'page4',
                'red.html',
                'page3',
                1,
                1)

    p1.children.append(p2)
    p2.children.append(p3)
    p3.children.append(p4)

    return p1


class PageTest(unittest.TestCase):
    def template_required_test(self):
        mdr = riccodo.MarkdownReader('./tests/')

        self.assertRaises(AssertionError,
                          mdr.read,
                          './tests/notemplate.md')

    def descendants_test(self):
        p1 = get_pages()
        self.assertEqual(len([p for p in p1.descendants()]), 3)
        self.assertNotEqual(len([p for p in p1.descendants()]), 4)


class GetUrlTest(unittest.TestCase):
    def get_url_test(self):
        url = riccodo.get_url('/en/foo.html', '/img/bar.png')
        self.assertEqual(url, '../img/bar.png')


class TestBuildTree(unittest.TestCase):
    def build_tree_test(self):
        p1 = riccodo.Page('page1.md',
                  'content',
                  'page1',
                  'red.html',
                  None,
                  1,
                  1)
        p2 = riccodo.Page('page2.md',
                  'content',
                  'page2',
                  'red.html',
                  'page1',
                  1,
                  1)

        self.assertEqual(p1.name, 'page1')
        self.assertEqual(p2.name, 'page2')
        pages = [p1, p2]
        page_tree, pages_flat = riccodo.build_page_tree(pages)
        self.assertTrue(page_tree[0].title == 'page1')
        self.assertTrue(page_tree[0].children)
