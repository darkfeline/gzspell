from functools import lru_cache
import logging
import abc
from functools import partial
import random
from operator import itemgetter
from collections import defaultdict

import pymysql

from gzspell import trie

logger = logging.getLogger(__name__)


class BaseDatabase(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def hasword(self, word):
        raise NotImplementedError

    @abc.abstractmethod
    def wordfromid(self, id):
        raise NotImplementedError

    @abc.abstractmethod
    def freq(self, id):
        raise NotImplementedError

    @abc.abstractmethod
    def length_between(self, a, b):
        raise NotImplementedError

    @abc.abstractmethod
    def len_startswith(self, a, b, prefix):
        raise NotImplementedError

    @abc.abstractmethod
    def startswith(self, a):
        raise NotImplementedError

    @abc.abstractmethod
    def neighbors(self, word_id):
        raise NotImplementedError


class Database(BaseDatabase):

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self.trie = self._build_trie()

    def _connect(self):
        return pymysql.connect(*self._args, **self._kwargs)

    def _build_trie(self):
        t_words = trie.Trie()
        with self._connect() as cur:
            cur.execute('SELECT word FROM words ORDER BY word')
            words = [x[0].decode('utf8') for x in cur.fetchall()]
            for word in words:
                t_words.add(word)
        return t_words

    def hasword(self, word):
        trav = trie.Traverser(self.trie)
        trav.traverse(word)
        if trav.error or not trav.complete:
            logger.debug('has word %r', word)
            return False
        else:
            logger.debug("doesn't have word %r", word)
            return True

    def wordfromid(self, id):
        with self._connect() as cur:
            cur.execute('SELECT word FROM words WHERE id=%s', id)
            return [x[0] for x in cur.fetchall()]

    def freq(self, id):
        with self._connect() as cur:
            cur.execute('SELECT frequency FROM words WHERE id=%s', id)
            return [x[0] for x in cur.fetchall()]

    def length_between(self, a, b):
        with self._connect() as cur:
            cur.execute(
                'SELECT id FROM words WHERE length BETWEEN %s AND %s',
                (a, b))
            return [x[0] for x in cur.fetchall()]

    def len_startswith(self, a, b, prefix):
        with self._connect() as cur:
            cur.execute(' '.join((
                'SELECT id FROM words WHERE length BETWEEN %s AND %s',
                'AND word LIKE %s')), (a, b, prefix + '%'))
            return [x[0] for x in cur.fetchall()]

    def startswith(self, a):
        with self._connect() as cur:
            cur.execute(
                'SELECT id FROM words WHERE word LIKE %s', a + '%')
            return [x[0] for x in cur.fetchall()]

    def neighbors(self, word_id):
        with self._connect() as cur:
            cur.execute(
                'SELECT word2 FROM graph WHERE word1=%s',
                word_id)
            return [x[0] for x in cur.fetchall()]


class SimpleDatabase(Database):

    """Simple database implementation for testing purposes

    Parameters
    ----------
    words : iterable
        Iterable of units like (word, frequency)

    """

    def __init__(self, words):
        self.words = [word for word, freq in words]
        self.freqs = [freq for word, freq in words]
        self.by_length = defaultdict(list)
        for id, word in enumerate(words):
            self.by_length[len(word[0])].append(id)
        self.graph = [
            (a, b) for a in range(len(self.words))
            for b in range(len(self.words)) if
            editdist(*(self.words[i][0] for i in (a, b))) < 5 and
            a != b
        ]

    def hasword(self, word):
        assert isinstance(word, str)
        return word in self.words

    def wordfromid(self, id):
        assert isinstance(id, int)
        return self.words[id]

    def freq(self, id):
        assert isinstance(id, int)
        return self.freqs[id]

    def length_between(self, a, b):
        """Return words with length between a and b inclusive"""
        return [id for length in range(a, b+1) for id in
                self.by_length[length]]

    def len_startswith(self, a, b, prefix):
        return [id for length in range(a, b+1) for id in self.by_length[length]
                if self.words[id].startswith(prefix)]

    def startswith(self, a):
        return [id for id, word in enumerate(self.words) if word.startswith(a)]

    def neighbors(self, word_id):
        return [y for x, y in self.graph if x == word_id]


class Spell:

    def __init__(self, db):
        self.db = db
        self._length_err = 2
        self._threshold = 10

    def check(self, word):
        if self.db.hasword(word):
            return 'OK'
        else:
            return 'ERROR'

    def correct(self, word):
        logger.debug('correct(%r)', word)
        assert isinstance(word, str)
        length = len(word)
        # get candidates
        id_candidates = self.db.len_startswith(
            length - self._length_err, length + self._length_err, word[0])
        if not id_candidates:
            logger.debug('no candidates')
            return None
        # get from graph
        id_cand = random.choice(id_candidates)
        dist = partial(self._id_dist, target=word)
        while True:
            id_neighbors = self.db.neighbors(id_cand)
            if not id_neighbors:
                logger.debug('no neighbors')
                break
            id_neighbors.sort(key=dist)
            if dist(id_cand) <= dist(id_neighbors[0]):
                break
            else:
                id_cand = id_neighbors[0]
        return self.db.wordfromid(id_cand)

    def process(self, word):
        if self.check(word) == 'OK':
            return 'OK'
        else:
            correct = self.correct(word)
            return ' '.join(('WRONG', correct if correct is not None else ''))

    def _id_dist(self, id_word, target):
        return self.dist(self.db.wordfromid(id_word), target)

    def add(self, word):
        raise NotImplementedError

    def dist(self, word, target):
        """
        Parameters
        ----------
        word : str
            Correct word.
        target : str
            Wrong word.

        """
        assert isinstance(word, str)
        assert isinstance(target, str)
        cost = editdist(word, target)
        cost += abs(len(target) - len(word))
        if target[0] != word[0]:
            cost += 1
        cost *= self.db.freq(self.db.words.index(word))
        return cost


class Costs:

    keys = 'qwertyuiopasdfghjklzxcvbnm-'

    _neighbors = {
        'q': ('w', 'a', 's'),
        'w': ('q', 'a', 's', 'd', 'e'),
        'e': ('w', 's', 'd', 'f', 'r'),
        'r': ('e', 'd', 'f', 'g', 't'),
        't': ('r', 'f', 'g', 'h', 'y'),
        'y': ('t', 'g', 'h', 'j', 'u'),
        'u': ('y', 'h', 'j', 'k', 'i'),
        'i': ('u', 'j', 'k', 'l', 'o'),
        'o': ('i', 'k', 'l', 'p'),
        'p': ('o', 'l', '-'),
        'a': ('q', 'w', 's', 'x', 'z'),
        's': ('q', 'a', 'z', 'x', 'c', 'd', 'e', 'w'),
        'd': ('w', 's', 'x', 'c', 'v', 'f', 'r', 'e'),
        'f': ('e', 'd', 'c', 'v', 'b', 'g', 't', 'r'),
        'g': ('r', 'f', 'v', 'b', 'h', 'y', 't'),
        'h': ('t', 'g', 'b', 'n', 'j', 'u', 'y'),
        'j': ('y', 'h', 'n', 'm', 'k', 'i', 'u'),
        'k': ('u', 'j', 'm', 'l', 'o', 'i'),
        'l': ('i', 'k', 'o', 'p'),
        'z': ('a', 's', 'x'),
        'x': ('z', 's', 'd', 'c'),
        'c': ('x', 'd', 'f', 'v'),
        'v': ('c', 'f', 'g', 'b'),
        'b': ('v', 'g', 'h', 'n'),
        'n': ('b', 'h', 'j', 'm'),
        'm': ('n', 'j', 'k', 'l'),
        '-': ('p'),
    }

    def __init__(self):
        self.costs = [
            [float('+inf') for i in range(len(self.keys))]
            for j in range(len(self.keys))]

    def get(self, a, b):
        return self.costs[self.keys.index(a)][self.keys.index(b)]

    def set(self, a, b, v):
        self.costs[self.keys.index(a)][self.keys.index(b)] = v

    def compute(self):
        for a in self._neighbors:
            logger.debug('Computing for a=%r', a)
            unvisited = set(self.keys)
            self.set(a, a, 0)
            while unvisited:
                current = min(unvisited, key=partial(self.get, a))
                logger.debug('Computing for current=%r', current)
                for k in self._neighbors[current]:
                    if k not in unvisited:
                        continue
                    else:
                        self.set(a, k, min(
                            self.get(a, k), self.get(a, current) + 0.5))
                unvisited.remove(current)

    def print(self):
        for i, x in enumerate(self.keys):
            print(x)
            print(', '.join(
                ': '.join((y, str(self.costs[i][j])))
                for j, y in enumerate(self.keys)))

    def repl_cost(self, a, b):
        logger.debug('repl_cost(%r, %r)', a, b)
        assert isinstance(a, str) and len(a) == 1
        assert isinstance(b, str) and len(b) == 1
        cost = self.get(a, b)
        assert cost is not None
        return cost

costs = Costs()
costs.compute()


@lru_cache(2048)
def editdist(word, target, limit=None):
    # table[target][word]
    table = [
        [None for x in range(len(word) + 1)] for y in range(len(target) + 1)
    ]
    table[0][0] = 0
    try:
        return _editdist(word, target, limit, len(word), len(target), table)
    except LimitException:
        return float('+inf')


def _editdist(word, target, limit, i_word, i_target, table):
    """
    Parameters
    ----------
    word : str
        Word to calculate edit distance for
    target : str
        Target word to compare to
    limit : Number or None
        Cost limit before returning
    i_word : int
        Index for word substring slice, e.g. 3 for "apple" is slice
        "app"
    i_target : int
        Index for target substring slice
    table : list
        Table for dynamic programming/cache

    """
    logger.debug(
        '_editdist(%r, %r, %r, %r, table)', word, target, i_word, i_target)
    assert isinstance(i_word, int)
    assert isinstance(i_target, int)
    if i_word < 0 or i_target < 0:
        logger.debug('Got inf')
        return float('+inf')
    if table[i_target][i_word] is None:
        cost = min(
            # insert in word
            _editdist(word, target, limit, i_word, i_target - 1, table) + 1,
            # delete in word
            _editdist(word, target, limit, i_word - 1, i_target, table) + 1,
            # replace, same
            _editdist(word, target, limit, i_word - 1, i_target - 1, table) +
            costs.repl_cost(word[i_word - 1], target[i_target - 1])
        )
        if limit is not None and cost >= limit:
            raise LimitException
        table[i_target][i_word] = cost
    logger.debug('Got %r', table[i_target][i_word])
    return table[i_target][i_word]


class LimitException(Exception):
    pass
