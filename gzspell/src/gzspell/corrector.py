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

TODO

Responds with a single byte and closes the connection.  From the least
significant bit, the bits indicate whether the word is incorrect and
whether the word is complete.

"""

import logging
import argparse
import socket
import atexit

logger = logging.getLogger(__name__)


def main(*args):

    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir')
    parser.add_argument('--port', type=int, default=9001)
    args = parser.parse_args(args)

    # build data

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
        result = process(chars)
        # send data
        remote_sock.send(bytes([result]))
        remote_sock.shutdown(socket.SHUT_RDWR)
        remote_sock.close()


def process(word):
    return 'apple'


def wrap(chars):
    x = chars.encode('utf8')
    assert len(x) < 256
    return bytes([len(x)]) + chars.encode('utf8')


def _close(sock):
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
