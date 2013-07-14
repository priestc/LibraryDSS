Library Data Storage System
===========================

LibraryDSS is a software service that is a hybrid between a database and a filesystem.
Not quite a database, not quite a filesystem. It is a Data Storage System or DSS.
Google Drive, Dropbox, and Amazon S3 could also be described as a DSS.
These services utilize filesystems and databases in their own implementation,
but they themselves are something fundamentally different as a whole.

LibraryDSS is an open source service that sits between the user and his or her Dropbox,
Google Drive or Amazon S3 Account that allows for better interoperability.

How can I install and run LibraryDSS?
-----------------------------

Clone this repo, then navigate to the follder and run ``giotto http --run``. This will start the webserver.
Navigate to ``http://localhost:5000``. You'll then see the site. Sign up with a username and password.

You can also go to http://libraries.pw to sign up for an account.
A library server is very similar to an email server.
libraries.pw is to libraries as what gmail.com is to email.
A library is similar to an inbox, but a library can do more and works a little differently.

How far along is LibraryDSS?
----------------------------

Currently pre-beta. If you would like to contribute fell free to try it out at libraries.pw.

I am a Developer, how does LibraryDSS work?
-------------------------------------------

Instead of saving data to a remote database, you connect to the user's library, and store the data there.



https://docs.google.com/presentation/d/1OxoolWUo2iY_ohxG_HHxd1gQTm3JA52pvWRnefl9IlA/pub?start=false&loop=false&delayms=3000#slide=id.p