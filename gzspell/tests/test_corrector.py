import unittest
import os
import logging
import shutil
import tempfile
import multiprocessing
import socket
import time

from gzspell import corrector

logger = logging.getLogger(__name__)


class TestCorrector(unittest.TestCase):

    def setUp(self):
        self._olddir = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)
        # TODO
        self.proc = CorrectorProcess()
        self.proc.start()
        time.sleep(1)

    def tearDown(self):
        self.proc.terminate()
        shutil.rmtree(self.tmpdir)
        os.chdir(self._olddir)

    def check(self, word):
        logger.debug('checking word %r', word)
        sock = socket.socket(socket.AF_INET)
        sock.connect(('localhost', 9001))
        sock.send(corrector.wrap(word))
        bytes = sock.recv(1)
        response = sock.recv(bytes).decode('utf8')
        logger.debug('got %r', response)

    @unittest.skip("can't do without database")
    def test_one(self):

        logger.debug('test 1')
        self.check('apple')

        logger.debug('test 2')
        self.check('app')

        logger.debug('test 3')
        self.check('ap')

        logger.debug('test 4')
        self.check('nanoha')


class CorrectorProcess(multiprocessing.Process):

    def __init__(self, *args):
        super().__init__()
        self.args = args

    def run(self):
        corrector.main(*self.args)
