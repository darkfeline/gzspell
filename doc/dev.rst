===========================
Developer Guide for gzspell
===========================

gzspell is a Python package/library for spell-checking and
auto-correction.

There is no user guide because this is the backend; the expected "end
user" is the developer.

.. note::

   Build this document with Sphinx if you want pretty formatting and
   links and such.  (This document is in reST format, in case you
   didn't know.)

Dependencies
============

- Python 3
- pymysql
- nose for unit tests

.. note::

   The public stable release of pymysql contains a fatal bug.  A
   patched version of the package is included in the ``files``
   directory.

Overview
========

gzspell implements spell-checking and auto-correction functions and
classes, as well as a server wrapping these functions with an API for
frontends.

Basic Setup
===========

* Load the database schema.
* Populate tables with data (a few helper scripts are included.)
* Start the server: ``gzserver --user user --passwd passwd``.

Example
-------

::

   # Install gzspell package
   $ python setup.py install

   # Load schema
   $ mysql -u group0 -p < files/lexicon.sql

   # Make lexicon (generate frequencies) from wordlist and corpora
   $ make_lexicon lexicon.dat wordlist corpus1 corpus2

   # Make graph (Warning: will take forever)
   $ make_graph lexicon.dat graph.dat

   # Import lexicon and graph into database
   $ import_lexicon --db-user group0 --db-passwd passwd lexicon.dat graph.dat

   # Start server
   $ gzserver --user group0 --passwd passwd

   # Start shell interface
   $ gzshell --user group0 --passwd passwd

   # Run one command
   $ gzcli --user group0 --passwd passwd process appler

Vocabulary Domain
=================

gzspell can handle all lowercase letters, single quotes and dashes.
There is no reason why it cannot be expanded to handle every
character, but it is currently not implemented to do so efficiently.

The relevant changes needed to widen the vocabulary mainly surrounds
expanding the Costs keyboard map for edit distance character
replacement costs and removing ``str.lower()`` calls scattered
throughout the code base.

Package Modules
===============

.. module:: trie

trie.py
-------

Contains an implementation of the trie data type.  This is no longer
used, a remnant of an earlier design.

.. class:: Trie

   Implementation of a trie with Nodes, Python dicts, and compression of
   single Node chains.  For example, if "app" and "apple" are added to a
   trie, instead of 5 nodes::

     Node a> Node p> Node p> Node l> Node e> Node
                             ^               ^

   there would only be 3 nodes::

     Node a> Relation pp> Node l> Relation e> Node
                          ^                   ^

   .. method:: add(word)

      Add the word to the trie.

Access and lookup for the trie is handled by a separate class.

.. class:: Traverser(trie)

   Traverser implements an incremental lookup on a trie.  The
   incremental lookup functionality is a remnant of the initial design.

   `trie` is the Trie instance to traverse.

   A basic lookup can be performed like so::

     >>> t = Traverser(trie)
     >>> t.traverse("apple")
     >>> t.complete
     True

   .. attribute:: complete

      Whether the current state of the traversal lies on a complete
      word.  This is implemented as a property (method call).

   .. attribute:: error

      Whether the current state of the traversal has run off the trie
      (the word is not in the trie).

   .. method:: traverse(chars)

      Traverse the trie with the given characters.

.. module:: analysis

analysis.py
-----------

The analysis module handles the actual spell-checking and correction.

.. class:: Costs

   Costs handles dynamic generation of key replacement costs for
   :meth:`editdist`.  The Costs class is hard-coded for a QWERTY
   keyboard, and the analysis module instantiates and binds a module
   instance of Costs that is referenced in the recursive part of
   :meth:`editdist`.

   .. method:: compute()

      Compute the costs.  This method should be called after
      instantiation.

   .. method:: repl_cost(a, b)

      Return the cost for replacing `a` with `b`.

.. function:: editdist(word, target, limit=None)

   Calculate the edit distance between `word` and `target`.  `limit`
   sets a limit on the cost after which computation terminates,
   returning infinity.

   This has an LRU cache of 2048, as does its recursive component, as
   an easier replacement for dynamic programming.

.. class:: Database

   A MySQL/RDB implementation of a theoretical Database interface.
   Used to use a trie for membership testing.

   The Database constructor takes the same arguments as pymysql's
   connect().

   Database is probably thread-safe.

   .. method:: hasword(word)

      Check if the word exists.

   .. method:: freq(id)

      Return the frequency of the word with the given id.

   .. method:: len_startswith(a, b, prefix)

      Return the words with the given id with length
      between `a` and `b` and beginning with the given prefix.

      Return a list of tuples: (id, word).

   .. method:: neighbors(word_id)

      Return the neighbors of the word with the given id.

      Return a list of tuples: (id, word).

   .. method:: add_word(word, freq)

      Add word with the given initial frequency proportion.  Doesn't check
      if the word already exists.

   .. method:: add_freq(word, freq)

      Add `freq` to the word's frequency count.  Doesn't check if the
      word already exists.

   .. method:: balance_freq()

      Balance frequencies in the database.

      .. note:: Not yet implemented.

.. class:: Spell(db)

   Class that implements the spell-checking and correction
   functionality.

   `db` is the database to use for this instance of Spell.

   .. method:: check(word)

      Check if the word is correct (in the dictionary).  Return 'OK' or
      'ERROR'.

   .. method:: correct(word)

      Return the correction for the word.

   .. method:: process(word)

      Check if the word is correct and return the correction if not.
      Return 'OK' or 'WRONG correction'.

   .. method:: add(word)

      Add the word to the database.

   .. method:: bump(word)

      Increase the frequency of an existing word in the database.

   .. method:: update(word)

      Add the word, and update if it already exists.

Scripts
=======

The gzspell package includes the following scripts:

gzserver

    The server script.  See the file or ``gzserver -h`` for usage instructions.

gzcli

   A CLI script.  See the file or ``gzserver -h`` for usage instructions.

   Run with ``--profile`` for profiling information.

gzshell

   A shell interface script.  See the file or ``gzserver -h`` for
   usage instructions.  Commands are the same as the server API.  An
   extra command ``profile`` is provided to turn profiling on or off.

   check <word>
   correct <word>
   process <word>
   add <word>
   bump <word>
   update <word>
   profile <on|off>
   profile
   quit

make_lexicon

   Given a word list and any number of corpora files, generate a
   lexicon file::

     $ make_lexicon lexicon.dat wordlist corpus1 corpus2 ...

make_graph

   Given a lexicon, generate a graph file.  See the docstrings in the
   script for data file formats (It's similar to JSON).

   .. warning::

      This will take forever.  O(n^2) edit distance calculations which
      are O(n^2).  Thus O(n^4).  Luckily, this is a one-time one-time
      cost to initialize the database.

import_lexicon

   Load lexicon and graph data files into a MySQL database.

Unit Tests
==========

Unit tests are in the ``test`` directory.  Run nosetests on the directory
to do all of them.

Server Protocol
===============

The server opens an INET socket locally at a given port (defaults to
9000).

Messages sent to and from the server are wrapped as follows:  First byte
indicates the number of following bytes (NOT characters), up to 255.
Messages are encoded in UTF-8.  See ``wrap()`` in server.py.

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

ADD word
    Add a new word to the dictionary.

BUMP word
    Bump the frequency of an existing word.

UPDATE word
    Add a new word to the dictionary, or bump if it exists.

PROCESS and UPDATE will probably be the easiest to use.

Database Schema
===============

An .sql file with the appropriate schema is included.  The following
describes the general structure of the database.

There are two tables: words and graph.

words has the following columns:

- id
- word
- length
- frequency

Most are self-explanatory.  ``frequency`` is a misnomer; it contains a
count and is averaged over the table sum for the actual frequency.
``frequency`` is balanced periodically, so it can be a float.

.. note:: Frequency balancing is not implemented yet.

graph contains two columns:

- word1
- word2

Self-explanatory, mapping word ids to word ids, for words with an edit
distance below a given threshold.
