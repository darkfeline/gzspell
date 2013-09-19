"""
Start a backend server.

The server opens an INET socket locally at a given port (defaults to
9000).

Messages sent to and from the server are wrapped as follows:  First byte
indicates the number of following bytes (NOT characters), up to 255.
Messages are encoded in UTF-8.  See wrap().

Commands sent to the server have the format: "COMMAND arguments"

The server recognizes the following commands:

CHECK word
    Checks the given word and returns:

    - OK
    - ERROR
    - INCOMPLETE

CORRECT word
    Calculates the best correction for the given word and returns it.

PROCESS word
    Checks and corrects if not correct:

    - OK
    - WRONG suggestion

Socket is closed after each transaction.

"""

import logging
import argparse
import socket
import atexit
import shlex
from functools import partial

import pymysql

from gzspell import analysis
from gzspell import trie

logger = logging.getLogger(__name__)


def main(*args):

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9000)
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--db', default='lexicon')
    parser.add_argument('--user', default='lexicon')
    parser.add_argument('--pw', default='')
    args = parser.parse_args(args)

    # build trie
    t_words = _build_trie(args.host, args.db, args.user, "")
    t_words = trie.Trie()
    with open(args.wordlist) as f:
        for line in f:
            t_words.add(line.rstrip())

    # commands
    cmd_dict = {
        "CHECK": partial(check, t_words),
        "CORRECT": partial(
            correct, host=args.host, db=args.db, user=args.user),
        "PROCESS": process,
    }

    # open socket
    sock = socket.socket(socket.AF_INET)
    addr = ('', args.port)
    sock.bind(addr)
    atexit.register(_close, sock)
    sock.listen(5)
    logger.debug("Socket bound and listening to %r", addr)

    while True:
        try:
            remote_sock, addr = sock.accept()
        except OSError as e:
            logger.debug(
                'Got exception listening for socket connection %r', e)
            continue
        msg = _get(remote_sock)
        cmd, *args = shlex.split(msg)
        # calculate
        result = cmd_dict[cmd](*args)
        # send data
        if result is not None:
            remote_sock.send(wrap(result))
        else:
            remote_sock.send(bytes([0]))

        remote_sock.shutdown(socket.SHUT_RDWR)
        remote_sock.close()


def process(word, *, host, user, db, trie, length_err=2, num_cand=5):
    if check(trie, word) == 'OK':
        return 'OK'
    else:
        return ' '.join('WRONG', correct(
            word, host=host, db=db, length_err=length_err, num_cand=num_cand))


def correct(word, *, host, user, db, length_err=2, num_cand=5):
    with pymysql.connect(host=host, user=user, db=db) as cur:
        length = len(word)
        id_cand = []  # candidate IDs
        # filter by length
        # TODO the filtering can be put into new functions...
        results = cur.execute(
            ' '.join(
                'SELECT id FROM words WHERE length BETWEEN %d AND %d',
                'ORDER BY frequency DESC',
            ),
            (length - length_err, length + length_err))
        if not results:
            return None
        id_cand.extend(results)
        # filter by first letter
        results = cur.execute(
            'SELECT id FROM words WHERE word LIKE %s',
            word[0] + '%')
        if not results:
            return None
        new = []
        results = set(results)
        for x in id_cand:
            if x in results:
                new.append(x)
        id_cand = new
        # get from graph
        # TODO type, return value checks
        id_cand = id_cand[:num_cand]
        results = cur.executemany(' '.join(
            'SELECT word FROM graph WHERE word1=%s',
            'LEFT JOIN word ON graph.word2=word.id',
        ), id_cand)
        if not results:
            return None
        id_cand = set()
        for x in results:
            id_cand.update(x)
        # calculate edit distance
        id_cand = list(id_cand)
        id_cand.sort(key=partial(analysis.editdist, word))
        return id_cand[0]


def check(trie_, word):
    trav = trie.Traverser(trie_)
    # TODO do this incrementally?
    trav.traverse(word)
    if trav.error:
        assert not trav.complete
        return "ERROR"
    elif not trav.complete:
        return "INCOMPLETE"
    else:
        return "OK"


def wrap(chars):
    x = chars.encode('utf8')
    assert len(x) < 256
    return bytes([len(x)]) + chars.encode('utf8')


def _build_trie(host, db, user, passwd):
    t_words = trie.Trie()
    with pymysql.connect(host=host, user=user, db=db) as cur:
        words = cur.execute('SELECT word FROM words ORDER BY word')
        for word in words:
            t_words.add(word)
    return t_words


def _get(sock):
    size = sock.recv(1)
    if not size:
        return None
    return sock.recv(size).decode('utf8')


def _close(sock):
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
