Library Transfer Protocol
=========================

LTP is a protocol for publishing, archiving, and organizing media files.
The protocol is conceptually very similar to email, except backwards.
With SMTP, you send messages to other people's inboxes, and other people send messages to your inbox.

With LTP, you publish media items (photos, videos, blog entries, other personal data) to your a library,
other people publish data to their library, and these libraries can talk to each other to allow data to flow between them,
as configured by the user who created the library.

What is LTP similar to?
-----------------------

It is very similar to WinFS.

Whats in this repo?
-------------------
The software withuin this repo is the code for running an LTP server.
It is written in Python, and works in both Python 2 and Python 3.
This code is intended to be a reference implementation of the LTP protocol.
The LTP Protocol will be defined and finalized after this reference implementation has reaches 1.0 state.
This code has been written to be readable and to clearly communicate the concepts of the protocol, and is not in any way optimized.


More Information
----------------
Watch this presentation describing the protocol in pictures.

https://docs.google.com/presentation/d/1OxoolWUo2iY_ohxG_HHxd1gQTm3JA52pvWRnefl9IlA/pub?start=false&loop=false&delayms=3000#slide=id.p
