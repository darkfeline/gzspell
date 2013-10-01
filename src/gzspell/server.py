import logging
import socket
import shlex
import threading

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
            "ADD": self.spell.add,
            "BUMP": self.spell.bump,
            "UPDATE": self.spell.update,
        }

        sock = socket.socket(socket.AF_INET)
        addr = ('', self.port)
        threads = []

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
                cmd, *args = shlex.split(msg)
                # calculate
                t = RequestHandler(remote_sock, cmd_dict[cmd], args)
                t.start()
                threads.append(t)
                i = 0
                while i < len(threads):
                    t = threads[i]
                    if not t.is_alive():
                        t.join()
                        threads.pop(i)
                    else:
                        i += 1
        finally:
            _close(sock)


class RequestHandler(threading.Thread):

    def __init__(self, sock, cmd, args):
        super().__init__()
        self.sock = sock
        self.cmd = cmd
        self.args = args

    def run(self):
        result = self.cmd(*self.args)
        if result is not None:
            self.sock.send(wrap(result))
        else:
            self.sock.send(bytes([0]))
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()


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
