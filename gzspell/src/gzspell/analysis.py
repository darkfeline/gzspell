from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

cost = {'insert': 1, 'delete': 1, 'replace': 1}


@lru_cache(1024)
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
            (
                _editdist(word, target, i_word, i_target - 1, table) +
                cost['insert']
            ),
            # delete in word
            (
                _editdist(word, target, i_word - 1, i_target, table) +
                cost['delete']
            ),
            # replace, same
            (
                _editdist(word, target, i_word - 1, i_target - 1, table) +
                (
                    cost['replace'] if
                    word[i_word - 1] != target[i_target - 1] else
                    0
                )
            ),
        )
    logger.debug('Got %r', table[i_target][i_word])
    return table[i_target][i_word]
