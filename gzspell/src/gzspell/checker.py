"""
Start a checker server using the given word list file.

The server opens an INET socket locally at a given port (defaults to
9000).

Communication with the server follows the given protocol per connection:

Client
------
First byte indicates number of following bytes.  Following bytes are
the characters to check, encoded in UTF-8.  Use the wrap() function to
do this.

Server
------
Responds with a single byte and closes the connection.  From the least
significant bit, the bits indicate whether the word is incorrect and
whether the word is complete.

"""

import logging
import argparse
import socket
import atexit

from gzspell import trie

logger = logging.getLogger(__name__)


def main(*args):

    parser = argparse.ArgumentParser()
    parser.add_argument('wordlist')
    parser.add_argument('--port', type=int, default=9000)
    args = parser.parse_args(args)

    # build trie
    t_words = trie.Trie()
    with open(args.wordlist) as f:
        for line in f:
            t_words.add(line.rstrip())

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
        assert isinstance(size, bytes)
        size = size[0]
        assert isinstance(size, int)
        # TODO do this incrementally?
        chars = remote_sock.recv(size).decode('utf8')
        trav = trie.Traverser(t_words)
        trav.traverse(chars)
        result = 0
        if trav.error:
            result ^= 1
        if trav.complete:
            result ^= 2
        remote_sock.send(bytes([result]))
        remote_sock.shutdown(socket.SHUT_RDWR)
        remote_sock.close()


def wrap(chars):
    return bytes([len(chars)]) + chars.encode('utf8')


def _close(sock):
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
