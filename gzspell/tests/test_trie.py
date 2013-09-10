import unittest
import logging

from gzspell import trie

logger = logging.getLogger(__name__)


class TestTrie(unittest.TestCase):

    def check(self, t, err, comp):
        self.assertIs(t.error, err)
        self.assertIs(t.complete, comp)

    def test_one(self):

        x = trie.Trie()
        x.add('apple')

        logger.debug('test 1')
        t = trie.Traverser(x)
        t.traverse('apple')
        self.check(t, False, True)

        logger.debug('test 2')
        t = trie.Traverser(x)
        t.traverse('app')
        self.check(t, False, False)
        t.traverse('le')
        self.check(t, False, True)

        logger.debug('test 3')
        t = trie.Traverser(x)
        t.traverse('banana')
        self.check(t, True, False)
        t.traverse('cherry')
        self.check(t, True, False)
