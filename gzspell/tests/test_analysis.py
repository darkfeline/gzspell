import unittest
import logging

from gzspell import analysis

logger = logging.getLogger(__name__)


class TestSimpleDatabase(unittest.TestCase):

    def setUp(self):
        self.db = analysis.SimpleDatabase([
            ('apple', 0.25),
            ('banana', 0.25),
            ('bananas', 0.50),
        ])

    def test_wordfromid(self):
        db = self.db
        self.assertEquals(db.wordfromid(0), 'apple')
        self.assertEquals(db.wordfromid(1), 'banana')

    def test_freq(self):
        db = self.db
        self.assertEquals(db.freq(0), 0.25)
        self.assertEquals(db.freq(1), 0.25)

    def test_length_between(self):
        db = self.db
        x = db.length_between(5, 5)
        self.assertIn('apple', x)
        self.assertNotIn('banana', x)
        self.assertNotIn('bananas', x)
        x = db.length_between(4, 5)
        self.assertIn('apple', x)
        self.assertNotIn('banana', x)
        self.assertNotIn('bananas', x)
        x = db.length_between(4, 6)
        self.assertIn('apple', x)
        self.assertIn('banana', x)
        self.assertNotIn('bananas', x)
        x = db.length_between(4, 7)
        self.assertIn('apple', x)
        self.assertIn('banana', x)
        self.assertIn('bananas', x)
        x = db.length_between(5, 7)
        self.assertIn('apple', x)
        self.assertIn('banana', x)
        self.assertIn('bananas', x)
        x = db.length_between(6, 7)
        self.assertNotIn('apple', x)
        self.assertIn('banana', x)
        self.assertIn('bananas', x)
        x = db.length_between(7, 7)
        self.assertNotIn('apple', x)
        self.assertNotIn('banana', x)
        self.assertIn('bananas', x)

    def test_len_startswith(self):
        db = self.db
        x = db.len_startswith(5, 5, 'a')
        logger.debug(x)
        logger.debug(db.by_length)
        self.assertIn('apple', x)
        self.assertNotIn('banana', x)
        self.assertNotIn('bananas', x)
        x = db.len_startswith(5, 7, 'a')
        self.assertIn('apple', x)
        self.assertNotIn('banana', x)
        self.assertNotIn('bananas', x)
        x = db.len_startswith(5, 7, 'b')
        self.assertNotIn('apple', x)
        self.assertIn('banana', x)
        self.assertIn('bananas', x)
        x = db.len_startswith(5, 7, 'bana')
        self.assertNotIn('apple', x)
        self.assertIn('banana', x)
        self.assertIn('bananas', x)
        x = db.len_startswith(6, 7, 'bana')
        self.assertNotIn('apple', x)
        self.assertIn('banana', x)
        self.assertIn('bananas', x)
        x = db.len_startswith(7, 7, 'bana')
        self.assertNotIn('apple', x)
        self.assertNotIn('banana', x)
        self.assertIn('bananas', x)
        x = db.len_startswith(7, 7, 'ana')
        self.assertNotIn('apple', x)
        self.assertNotIn('banana', x)
        self.assertNotIn('bananas', x)

    def test_startswith(self):
        db = self.db
        x = db.startswith('a')
        self.assertIn('apple', x)
        self.assertNotIn('banana', x)
        self.assertNotIn('bananas', x)
        x = db.startswith('b')
        self.assertNotIn('apple', x)
        self.assertIn('banana', x)
        self.assertIn('bananas', x)
        x = db.startswith('banana')
        self.assertNotIn('apple', x)
        self.assertIn('banana', x)
        self.assertIn('bananas', x)
        x = db.startswith('app')
        self.assertIn('apple', x)
        self.assertNotIn('banana', x)
        self.assertNotIn('bananas', x)
        x = db.startswith('nanoha')
        self.assertNotIn('apple', x)
        self.assertNotIn('banana', x)
        self.assertNotIn('bananas', x)
