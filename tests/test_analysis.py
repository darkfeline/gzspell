import unittest
import logging

from gzspell import analysis

logger = logging.getLogger(__name__)


class TestSpell(unittest.TestCase):

    def setUp(self):
        db = analysis.SimpleDatabase([
            ('apple', 0.25),
            ('banana', 0.25),
            ('bananas', 0.50),
        ])
        self.spell = analysis.Spell(db)

    def test_check(self):
        spell = self.spell
        self.assertEquals(spell.check('apple'), 'OK')
        self.assertEquals(spell.check('appl'), 'ERROR')
        self.assertEquals(spell.check('nanoha'), 'ERROR')
        self.assertEquals(spell.check('banana'), 'OK')
        self.assertEquals(spell.check('bananas'), 'OK')
        self.assertEquals(spell.check('banan'), 'ERROR')

    def test_correct(self):
        spell = self.spell
        self.assertEquals(spell.correct('appel'), 'apple')
        self.assertEquals(spell.correct('bananaa'), 'bananas')


class TestSimpleDatabase(unittest.TestCase):

    def setUp(self):
        self.db = analysis.SimpleDatabase([
            ('apple', 0.25),
            ('banana', 0.25),
            ('bananas', 0.50),
        ])

    def test_hasword(self):
        db = self.db
        self.assertTrue(db.hasword('apple'))
        self.assertTrue(db.hasword('banana'))
        self.assertTrue(db.hasword('bananas'))
        self.assertFalse(db.hasword('nanoha'))

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
        self.assertIn(0, x)
        self.assertNotIn(1, x)
        self.assertNotIn(2, x)
        x = db.length_between(4, 5)
        self.assertIn(0, x)
        self.assertNotIn(1, x)
        self.assertNotIn(2, x)
        x = db.length_between(4, 6)
        self.assertIn(0, x)
        self.assertIn(1, x)
        self.assertNotIn(2, x)
        x = db.length_between(4, 7)
        self.assertIn(0, x)
        self.assertIn(1, x)
        self.assertIn(2, x)
        x = db.length_between(5, 7)
        self.assertIn(0, x)
        self.assertIn(1, x)
        self.assertIn(2, x)
        x = db.length_between(6, 7)
        self.assertNotIn(0, x)
        self.assertIn(1, x)
        self.assertIn(2, x)
        x = db.length_between(7, 7)
        self.assertNotIn(0, x)
        self.assertNotIn(1, x)
        self.assertIn(2, x)

    def test_len_startswith(self):
        db = self.db
        x = db.len_startswith(5, 5, 'a')
        logger.debug(x)
        logger.debug(db.by_length)
        self.assertIn(0, x)
        self.assertNotIn(1, x)
        self.assertNotIn(2, x)
        x = db.len_startswith(5, 7, 'a')
        self.assertIn(0, x)
        self.assertNotIn(1, x)
        self.assertNotIn(2, x)
        x = db.len_startswith(5, 7, 'b')
        self.assertNotIn(0, x)
        self.assertIn(1, x)
        self.assertIn(2, x)
        x = db.len_startswith(5, 7, 'bana')
        self.assertNotIn(0, x)
        self.assertIn(1, x)
        self.assertIn(2, x)
        x = db.len_startswith(6, 7, 'bana')
        self.assertNotIn(0, x)
        self.assertIn(1, x)
        self.assertIn(2, x)
        x = db.len_startswith(7, 7, 'bana')
        self.assertNotIn(0, x)
        self.assertNotIn(1, x)
        self.assertIn(2, x)
        x = db.len_startswith(7, 7, 'ana')
        self.assertNotIn(0, x)
        self.assertNotIn(1, x)
        self.assertNotIn(2, x)

    def test_startswith(self):
        db = self.db
        x = db.startswith('a')
        self.assertIn(0, x)
        self.assertNotIn(1, x)
        self.assertNotIn(2, x)
        x = db.startswith('b')
        self.assertNotIn(0, x)
        self.assertIn(1, x)
        self.assertIn(2, x)
        x = db.startswith('banana')
        self.assertNotIn(0, x)
        self.assertIn(1, x)
        self.assertIn(2, x)
        x = db.startswith('app')
        self.assertIn(0, x)
        self.assertNotIn(1, x)
        self.assertNotIn(2, x)
        x = db.startswith('nanoha')
        self.assertNotIn(0, x)
        self.assertNotIn(1, x)
        self.assertNotIn(2, x)

    def test_neighbors(self):
        db = self.db
        logger.debug(db.graph)
        self.assertIn(2, db.neighbors(1))
        self.assertIn(1, db.neighbors(2))
