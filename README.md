libraries.pw
============

libraries.pw is a simple, reference implemetation of a Library server, and Library console, written in Python.

Use this software to run your own Library server provider, or use the one at http://libraries.pw.

To learn more about what a Library Server is, and what the system was designed for,
refer to the Library Transfer Protocol documentation (which does not yet exist).

Library Transfer Protocol is a hybrid between a database and a filesystem.
Its designed purpose is to store data is a long term manner, but it does so in a manner similar to a database.
Instead of referencing data by a path and a filename, you reference data via SQL-like queries.

A Library server differs from a traditional fileserver or SQL database server,
in that end users interact with the datastore directly.

Another way to think of a Library server is a Google Drive service, but with a SQL-like interface. In fact,
this reference implementation uses Google drive under the hood to handle the storage portion of it's process.

More Information
----------------
Watch this presentation describing the protocol in pictures.

https://docs.google.com/presentation/d/1OxoolWUo2iY_ohxG_HHxd1gQTm3JA52pvWRnefl9IlA/pub?start=false&loop=false&delayms=3000#slide=id.p