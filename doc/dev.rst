===========================
Developer Guide for gzspell
===========================

gzspell is a Python package/library for spell-checking and
auto-correction.

.. note::

   Build this document with Sphinx if you want pretty formatting and
   links and such.  (This document is in reST format, in case you didn't know.)

Dependencies
============

- Python 3
- pymysql
- nose for unit tests

.. note::
   The public stable release of pymysql contains a fatal bug.  A patched
   version of the package is included in the ``dependencies`` directory.

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
   Used to use a trire for membership testing.

   The Database constructor takes the same arguments as pymysql's
   connect().

   Database is probably thread-safe.

   .. method:: hasword(word)

      Check if the word exists.

   .. method:: wordfromid(id)

      Return the word with the given id.

   .. method:: freq(id)

      Return the frequency of the word with the given id.

   .. method:: length_between(a, b)

      Return the ids of words with length between `a` and `b`.

   .. method:: len_startswith(a, b, prefix)

      Return the ids of the word with the given id with length
      between `a` and `b` and beginning with the given prefix.

   .. method:: startswith(prefix)

      Return the ids of the word with the given id beginning with the
      given prefix.

   .. method:: neighbors(word_id)

      Return the ids of all of the neighbors of the word with the
      given id.

   .. method:: add_word(word, freq)

      Add word with the given initial frequency proportion.  Doesn't check
      if the word already exists.

   .. method:: add_freq(word, freq)

      Add `freq` to the word's frequency count.  Doesn't check if the
      word already exists.

   .. method:: balance_freq()

      Balance frequencies in the database.

.. class:: Spell(db)

   Class that implements the spell-checking and correction
   functionalities.

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

gzshell

    A shell interface script.  See the file or ``gzserver -h`` for
    usage instructions.  Commands are the same as the server API.

make_graph

    Given a lexicon, generate a graph file.  See the docstrings in the
    script for data file formats (It's similar to JSON).

    .. warning::

       This will take forever.  O(n^2) edit distance calculations which
       are O(n^2).  Thus O(n^4).  Luckily, this is a one-time one-time
       cost to initialize the database.

import_database

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
Messages are encoded in UTF-8.  See wrap() in server.py.

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
