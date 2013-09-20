from functools import lru_cache
import logging
from functools import partial

logger = logging.getLogger(__name__)


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
            [None for i in range(len(self.keys))]
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
            self.set(a, a, float('+inf'))

    def print(self):
        for i, x in enumerate(self.keys):
            print(x)
            print(', '.join(
                ': '.join((y, str(self.costs[i][j])))
                for j, y in enumerate(self.keys)))

costs = Costs()
costs.compute()


def repl_cost(a, b):
    logger.debug('repl_cost(%r, %r)', a, b)
    assert isinstance(a, str) and len(a) == 1
    assert isinstance(b, str) and len(b) == 1
    cost = costs.get(a, b)
    assert cost is not None
    return cost


@lru_cache(2048)
def editdist(word, target):
    # table[target][word]
    table = [
        [None for x in range(len(word) + 1)] for y in range(len(target) + 1)
    ]
    table[0][0] = 0
    return _editdist(word, target, len(word), len(target), table)


def _editdist(word, target, i_word, i_target, table):
    """
    Parameters
    ----------
    word : str
        Word to calculate edit distance for
    target : str
        Target word to compare to
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
    if i_word < 0 or i_target < 0:
        logger.debug('Got inf')
        return float('+inf')
    if table[i_target][i_word] is None:
        table[i_target][i_word] = min(
            # insert in word
            _editdist(word, target, i_word, i_target - 1, table) + 1,
            # delete in word
            _editdist(word, target, i_word - 1, i_target, table) + 1,
            # replace, same
            _editdist(word, target, i_word - 1, i_target - 1, table) +
            repl_cost(word[i_word - 1], target[i_target - 1])
        )
    logger.debug('Got %r', table[i_target][i_word])
    return table[i_target][i_word]
