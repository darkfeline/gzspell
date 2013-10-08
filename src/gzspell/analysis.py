from functools import lru_cache
import logging
import abc
from functools import partial
import random
from operator import itemgetter
from collections import defaultdict
from numbers import Number
from itertools import repeat

import pymysql

logger = logging.getLogger(__name__)

GRAPH_THRESHOLD = 4
INITIAL_FREQ = 0.01


class Database:

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def _connect(self):
        return pymysql.connect(*self._args, **self._kwargs)

    def hasword(self, word):
        with self._connect() as cur:
            cur.execute('SELECT id FROM words WHERE word=%s', word)
            x = cur.fetchone()
            if x:
                return True
            else:
                return False

    def freq(self, id):
        with self._connect() as cur:
            cur.execute('SELECT frequency FROM words WHERE id=%s', id)
            count = cur.fetchone()[0]
            assert isinstance(count, Number)
            cur.execute('SELECT sum(frequency) FROM words')
            total = cur.fetchone()[0]
            assert isinstance(total, Number)
            return count / total

    def len_startswith(self, a, b, prefix):
        with self._connect() as cur:
            cur.execute(' '.join((
                'SELECT id, word FROM words WHERE length BETWEEN %s AND %s',
                'AND word LIKE %s')), (a, b, prefix + '%'))
            return [(x[0], x[1].decode('utf8') for x in cur.fetchall()]

    def neighbors(self, word_id):
        with self._connect() as cur:
            cur.execute(' '.join((
                'SELECT word2, word FROM graph',
                'LEFT JOIN words ON graph.word2=words.id WHERE word1=%s',
            ), word_id)
            return [(x[0], x[1].decode('utf8') for x in cur.fetchall()]

    def add_word(self, word, freq):
        logger.debug('add_word(%r, %r)', word, freq)
        with self._connect() as cur:
            cur.execute('SELECT sum(frequency) FROM words')
            total_freq = cur.fetchone()[0]
            assert isinstance(total_freq, Number)
            cur.execute(' '.join((
                    'INSERT IGNORE INTO words SET',
                    'word=%s, length=%s, frequency=%s',)),
                (word, len(word), total_freq * freq))
            cur.execute('SELECT LAST_INSERT_ID()')
            id = cur.fetchone()[0]
            assert isinstance(id, int)
            cur.execute('SELECT id, word FROM words')
            wordlist = [(a, b.decode('utf8')) for a, b in cur.fetchall()]
            cur.executemany(' '.join((
                'INSERT IGNORE INTO graph (word1, word2) VALUES',
                '(%s, %s), (%s, %s)',)),
                ((x, y, y, x) for x, y in zip(
                    repeat(id), self._gen_graph(word, wordlist))))

    @staticmethod
    def _gen_graph(target, wordlist):
        logger.debug('_gen_graph(%r, wordlist)', target)
        threshold = GRAPH_THRESHOLD
        for id, word in wordlist:
            if editdist(word, target) < threshold:
                yield id

    def add_freq(self, word, freq):
        with self._connect() as cur:
            cur.execute(
                'UPDATE words SET frequency=frequency + %s WHERE word=%s',
                (word, freq))

    def balance_freq(self):
        raise NotImplementedError


class Spell:

    LOOKUP_THRESHOLD = 3
    LENGTH_ERR = 2
    INIT_LIMIT = 200
    MAX_TRIES = 10

    def __init__(self, db):
        self.db = db

    def check(self, word):
        if self.db.hasword(word):
            return 'OK'
        else:
            return 'ERROR'

    def correct(self, word):

        logger.debug('correct(%r)', word)
        assert isinstance(word, str)

        # get initial candidates
        length = len(word)
        init_cands = self.db.len_startswith(
            length - self.LENGTH_ERR, length + self.LENGTH_ERR, word[0])
        if not id_init_cands:
            logger.debug('no candidates')
            return None

        cands
        seen = set()
        tries = 0
        while tries < self.MAX_TRIES and len(id_cands) < 10:
            tries += 1
            self._try_candidate(word, init_cands, cands, seen)
        if not id_cands:
            return None
        candidates = [(id, cand_word, self._cost(dist, id, cand_word, word))
                      for id, word_cand, dist in cands]
        logger.debug('Candidates: %r', candidates)
        id, word, cost = min(candidates, key=itemgetter(2))
        return word

    def _try_candidate(self, word, init_cands, cands, seen):

        init_tries = 0
        # select inital candidate
        id_cand, word_cand = random.choice(init_cands)
        while editdist(word_cand, word) > self.LOOKUP_THRESHOLD:
            id_cand, word_cand = random.choice(init_cands)
            init_tries += 1
            if init_tries > self.INIT_LIMIT:
                logger.debug('Candidate search limit hit')
                return
        cands.append((id_cand, word_cand, editdist(word_cand, word)))
        seen.add(id_cand)

        # traverse graph
        self._explore(word, seen, cands, id_cand)

    def _explore(self, word, seen, cands, id_node):
        """
        Args:
            word: misspelled word
            seen: set of seen candidate ids
            cands: candidates
            id_node: current node

        """
        id_new = set()
        for id_neighbor, word_neighbor in self.db.neighbors(id_node):
            if id_neighbor not in seen:
                logger.debug("Visiting %r", id_neighbor)
                seen.add(id_neighbor)
                    dist = editdist(word, word_neighbor)
                if dist <= self.LOOKUP_THRESHOLD:
                    cands.append((id_neighbor, word_neighbor, dist))
                    id_new.add(id_neighbor)
        for id_node in id_new:
            self._explore(word, seen, cands, id_node)

    def process(self, word):
        if self.check(word) == 'OK':
            return 'OK'
        else:
            correct = self.correct(word)
            return ' '.join(('WRONG', correct if correct is not None else ''))

    def add(self, word):
        self.db.add_word(word, INITIAL_FREQ)

    def bump(self, word):
        self.db.add_freq(word, 1)

    def update(self, word):
        if not self.db.hasword(word):
            self.add(word)
        else:
            self.bump(word)

    def _cost(self, dist, id_word, word, target):
        """
        Args:
            dist: Distance between words
            id_word: ID of word in graph
            word: word in graph
            target: Misspelled word

        >>> spell.cost(editdist(word, misspelled), word, misspelled)

        """
        cost = dist
        cost += abs(len(target) - len(word)) / 2
        if target[0] != word[0]:
            cost += 1
        cost *= (1 - self.db.freq(id_word))
        return cost


class Costs:

    keys = 'qwertyuiopasdfghjklzxcvbnm-\''

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
        'p': ('o', 'l', '-', "'"),
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
        '-': ('p',),
        "'": ('p',),
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
        try:
            cost = self.get(a, b)
        except ValueError:  # not in costs table
            return 5
        assert cost is not None
        return cost

costs = Costs()
costs.compute()


@lru_cache(4096)
def editdist(a, b):
    try:
        x = _r_editdist(a, b)
        logger.debug('editdist(%r, %r) = %r', a, b, x)
        return x
    except LimitException:
        return float('+inf')


@lru_cache(4096)
def _r_editdist(a, b):
    """
    Parameters
    ----------
    a : str
        Word substring to calculate edit distance for
    b : str
        Word substring to calculate edit distance for

    """
    assert isinstance(a, str)
    assert isinstance(b, str)
    # base case
    if not a and not b:
        return 0
    possible = [float('+inf')]
    # insert in a
    if len(b) >= 1:
        possible.append(_r_editdist(a, b[:-1]) + 1)
    # delete in a
    if len(a) >= 1:
        possible.append(_r_editdist(a[:-1], b) + 1)
    # replace or same
    if len(a) >= 1 and len(b) >= 1:
        possible.append(
            _r_editdist(a[:-1], b[:-1]) +
            costs.repl_cost(a[-1], b[-1]))
    # transposition
    if len(a) >= 2 and len(b) >= 2 and a[-1] == b[-2] and a[-2] == b[-1]:
        possible.append(_r_editdist(a[:-2], b[:-2]) + 1)
    cost = min(possible)
    return cost
