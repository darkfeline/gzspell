import unittest
import os
import logging
import shutil
import tempfile
import multiprocessing
import socket
import time

from gzspell import checker

logger = logging.getLogger(__name__)


class TestChecker(unittest.TestCase):

    def setUp(self):
        self._olddir = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)
        with open('list', 'w') as f:
            f.write('\n'.join((
                'app', 'apple'
            )))
        self.proc = CheckerProcess('list')
        self.proc.start()
        time.sleep(1)

    def tearDown(self):
        self.proc.terminate()
        shutil.rmtree(self.tmpdir)
        os.chdir(self._olddir)

    def check(self, word, err, comp):
        logger.debug(
            'checking word %r with status err %r and comp %r', word, err, comp)
        sock = socket.socket(socket.AF_INET)
        sock.connect(('localhost', 9000))
        sock.send(checker.wrap(word))
        b_response = sock.recv(1)
        i_response = b_response[0]
        error, complete = (bool(i_response & (2**x)) for x in range(2))
        self.assertIs(error, err)
        self.assertIs(complete, comp)

    def test_one(self):

        logger.debug('test 1')
        self.check('apple', False, True)

        logger.debug('test 2')
        self.check('app', False, True)

        logger.debug('test 3')
        self.check('ap', False, False)

        logger.debug('test 4')
        self.check('nanoha', True, False)


class CheckerProcess(multiprocessing.Process):

    def __init__(self, *args):
        super().__init__()
        self.args = args

    def run(self):
        checker.main(*self.args)
