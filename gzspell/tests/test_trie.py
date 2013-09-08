import unittest
import logging

from gzspell import trie

logger = logging.getLogger(__name__)


class TestTrie(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_one(self):

        x = trie.Trie()
        x.add('apple')

        logger.debug('test 1')
        t = trie.Traverser(x)
        t.traverse('apple')
        self.assertFalse(t.error)
        self.assertTrue(t.complete)

        logger.debug('test 2')
        t = trie.Traverser(x)
        t.traverse('app')
        self.assertFalse(t.error)
        self.assertFalse(t.complete)
        t.traverse('le')
        self.assertFalse(t.error)
        self.assertTrue(t.complete)

        logger.debug('test 3')
        t = trie.Traverser(x)
        t.traverse('banana')
        self.assertTrue(t.error)
        self.assertFalse(t.complete)
        t.traverse('cherry')
        self.assertTrue(t.error)
        self.assertFalse(t.complete)
