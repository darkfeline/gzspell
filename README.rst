gz-spell
========

Group 0's autocorrect implementation.

Requirements
------------

- Python 3
- pymysql
- Web browser for frontend
- MySQL or compatible RDB (schema included)
- Java for scripts?

General Design
--------------

The software is split into two parts, the frontend UI and the backend.
The backend is split into two parts, a checker, which verifies whether a
word is spelled correctly, and a corrector, which returns the best
choice for the correctly spelled word.

Frontend
--------

The UI will keep track of word atoms as the user is typing.  It will
send the individual words to the backend for checking and correction.
If a word needs correction, it will be corrected and an indicator will
appear for that word.  The user may double-click on the word to undo the
auto-correction, or hit backspace (?) to undo the correction for the
previous word.

.. note::

   Valid word characters are all letters and '-'.  Everything else is
   not a word character.  Letters are forced to lowercase, since
   capitalization is often abandoned in chat/twitter.  (What about
   numbers?)

Backend
-------

The two parts of the backend are both server processes.  The frontend
communicates with them through INET sockets.  Thus, the backend can be
started separately or by the frontend, or hosted on a remote machine
entirely.

Checker
^^^^^^^

Simple comparison check for word correctness.  Communication protocol is
in source docstrings.  Uses trie or Python native sets in the future?

Corrector
^^^^^^^^^

Generate a list of candidate spelllings, calculates cost, and returns
best candidate.  Communication protocol is in source docstrings.

Lexicon and data are stored in database.  Candidates are refined
according to the following:

- Fuzzy word length
- First letter
- Precalculated edit distance threshold graph
