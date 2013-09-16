"""
Start a corrector server using the given word list file.

The server opens an INET socket locally at a given port (defaults to
9001).

Communication with the server follows the given protocol per connection:

Client
------
First byte indicates number of following bytes.  Following bytes are
the characters to check, encoded in UTF-8.  Use the wrap() function to
do this.

Server
------
Responds with the correct word.  Same as client, first byte indicates
number of following bytes.  Following bytes are the correct word,
encoded in UTF-8.

"""

import logging
import argparse
import socket
import atexit
from functools import partial

import pymysql

from gzspell import analysis

logger = logging.getLogger(__name__)


def main(*args):

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9001)
    parser.add_argument('--db-server', default='localhost')
    parser.add_argument('--db-name', default='lexicon')
    parser.add_argument('--db-user', default='lexicon')
    parser.add_argument('--db-pw', default='')
    args = parser.parse_args(args)

    # open socket
    sock = socket.socket(socket.AF_INET)
    addr = ('', args.port)
    sock.bind(addr)
    atexit.register(_close, sock)
    sock.listen(5)
    logger.debug("Socket bound and listening to %r", addr)

    # listen and check
    while True:
        try:
            remote_sock, addr = sock.accept()
        except OSError as e:
            logger.debug(
                'Got exception listening for socket connection %r', e)
            continue
        size = remote_sock.recv(1)
        if not size:
            continue
        # recv data
        chars = remote_sock.recv(size).decode('utf8')
        # calculate
        # TODO
        result = process(
            chars, host=args.db_server, user=args.db_user, db=args.db_name)
        # send data
        remote_sock.send(wrap(result))
        remote_sock.shutdown(socket.SHUT_RDWR)
        remote_sock.close()


def process(word, *, host, user, db, length_err=2, num_cand=5):
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
        id_cand.extend(results)
        # filter by first letter
        results = cur.execute(
            'SELECT id FROM words WHERE word LIKE %s',
            word[0] + '%')
        new = []
        results = set(results)
        for x in id_cand:
            if x in results:
                new.append(x)
        id_cand = new
        # get from graph
        id_cand = id_cand[:num_cand]
        results = cur.executemany(' '.join(
            'SELECT word FROM graph WHERE word1=%s',
            'LEFT JOIN word ON graph.word2=word.id',
        ), id_cand)
        id_cand = set()
        for x in results:
            id_cand.update(x)
        # calculate edit distance
        id_cand = list(id_cand)
        id_cand.sort(key=partial(analysis.editdist, word))
        return id_cand[0]


def wrap(chars):
    x = chars.encode('utf8')
    assert len(x) < 256
    return bytes([len(x)]) + chars.encode('utf8')


def _close(sock):
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
