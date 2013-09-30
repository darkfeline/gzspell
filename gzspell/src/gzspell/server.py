"""
Server module

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

CORRECT word
    Calculates the best correction for the given word and returns it.

PROCESS word
    Checks and corrects if not correct:

    - OK
    - WRONG suggestion

Socket is closed after each transaction.

"""

import logging
import socket
import shlex

logger = logging.getLogger(__name__)


class Server:

    def __init__(self, spell, port):
        self.spell = spell
        self.port = port

    def run(self):

        cmd_dict = {
            "CHECK": self.spell.check,
            "CORRECT": self.spell.correct,
            "PROCESS": self.spell.process,
        }

        sock = socket.socket(socket.AF_INET)
        addr = ('', self.port)

        try:
            sock.bind(addr)
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
                try:
                    cmd, *args = shlex.split(msg)
                    # calculate
                    result = cmd_dict[cmd](*args)
                except Exception as e:
                    logger.warning('Caught Exception %r', e)
                    result = None
                # send data
                if result is not None:
                    remote_sock.send(wrap(result))
                else:
                    remote_sock.send(bytes([0]))

                remote_sock.shutdown(socket.SHUT_RDWR)
                remote_sock.close()
        finally:
            _close(sock)


def wrap(chars):
    x = chars.encode('utf8')
    assert len(x) < 256
    return bytes([len(x)]) + chars.encode('utf8')


def _get(sock):
    size = sock.recv(1)
    size = size[0]
    logger.debug("Got size %r", size)
    if not size:
        return None
    msg = sock.recv(size).decode('utf8')
    logger.debug("Got msg %r", msg)
    return msg


def _close(sock):
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
