from collections import namedtuple
import logging

logger = logging.getLogger(__name__)

Relation = namedtuple('Relation', ['node', 'chars'])


class Traverser:

    """
    Traverser is used to traverse a Trie.  Instantiate a Traverser with
    the target trie and feed it characters with traverse().

    Attributes
    ----------
    complete : bool
        Whether or not the traversal currently lies on a complete word.
    error : bool
        Whether or not the traversal has failed.  If this is True,
        complete is False.

    """

    def __init__(self, trie):
        self.node = trie.root
        self.partial = ''
        self.error = False

    @property
    def complete(self):
        if not self.error:
            return self.node.end
        else:
            return False

    def traverse(self, chars):
        logger.debug('traverse(%r)', chars)
        if self.error:
            return
        chars = self.partial + chars.lower()
        while chars:
            char, chars = chars[0], chars[1:]
            logger.debug('checking %r, remaining %r', char, chars)
            try:
                rel = self.node[char]
            except KeyError:
                logger.debug('%r is bad key', char)
                self.error = True
                return
            if not chars.startswith(rel.chars):
                if rel.chars.startswith(chars):
                    logger.debug(
                        'storing partial match %r with relation %r',
                        chars, rel.chars)
                    self.partial = char + chars
                    return
                else:
                    logger.debug(
                        "chars %r doesn't match relation %r", chars, rel.chars)
                    self.error = True
                    return
            chars = chars[len(rel.chars):]
            self.node = rel.node


class Trie:

    """Compressed char trie implementation"""

    def __init__(self):
        self.root = Node()

    def add(self, word):
        logger.debug('add(%r)', word)
        word = word.lower()
        node = self.root
        while word:
            char, word = word[0], word[1:]
            logger.debug('checking %r', char)
            if node.haskey(char):
                logger.debug('getting %r', char)
                rel = node[char]
                if word.startswith(rel.chars):
                    logger.debug('relation chars okay')
                    node = rel.node
                    word = word[len(rel.chars):]
                else:
                    logger.debug('splitting relation %r', rel.chars)
                    match = _gcp(word, rel.chars)
                    logger.debug('first half %r', match)
                    new_node = Node()
                    node[char] = Relation(new_node, word[:match])
                    new_node[word[match]] = Relation(
                        node, word[match+1:])
                    node = new_node
                    word = word[match+1:]
            else:
                logger.debug('mapping %r with rel chars %r', char, word)
                new_node = Node()
                node[char] = Relation(new_node, word)
                node = new_node
                break
        node.end = True


class Node:

    __slots__ = ['map', 'end']

    def __init__(self):
        self.map = {}
        self.end = False

    def __getitem__(self, key):
        return self.map[key]

    def __setitem__(self, key, item):
        self.map[key] = item

    def haskey(self, key):
        return key in self.map


def _gcp(a, b):
    """Greatest common prefix"""
    i = 0
    count = 0
    while True:
        try:
            if a[i] == b[i]:
                count += 1
            else:
                return count
        except IndexError:
            return count
        i += 1
    return count
