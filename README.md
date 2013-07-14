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

I am a Developer, describe to me how an application written using LibraryDSS would work?
----------------------------------------------------------------------------------------

Lets say you wanted to write a foursquare clone using the LibraryDSS system.

You would build an HTML5 page that looks like of like this:

    <html>
    	<body>
    		<form>
    			<input type="text" name="place_name" placeholder="Place Name">
    			<input type="text" name="comment" placeholder="Comment">
    			<input type="submit">
    		</form>
    		<script>
    			$("form").submit(function() {
    				// this gets executed when the user clicks the submit button.
    				// instead of sending the data to foursquare.com to be stored,
    				// we send it to the user's library. They could have this library
    				// hosted anywhere by anyone.

    				// The user's `identity` is the address to their library. It looks 
    				// a lot like an email address. When a user signs up for an app
    				// that is built on top of LibraryDSS, they don't ever need to supply
    				// a password. Not when they sign up, not when they login. When a
    				// user signs up, they supply their identity, and it is stored in cookies.
    				// Authentication happens at "publish time"
    				var users_library_identity = $.cookie('library_identity');
    				var identity_token = $.cookie('library_token');

    				// the below example shows hardcoded urls and values to demonstrate
    				// the API. Notice the data goes to the user's library domain,
    				// not to the domain that served this page.
    				// All data sent data has to be flat, key+value.
    				// Unlike SOAP where you can have complex, nested XML structures.
    				$.ajax("http://chris@libraries.pw/api/publish" {
    					'app': "Foursquare Clone",
    					'date_created': '2013-7-14T03:23:54Z',
    					'place_name': "Ben & Jerrys",
    					'purpose': "Check In",
    					'location': navigator.geolocation.getCurrentPosition().toString(),
    				});
    			});
    		</script>
    	</body>
    </html>

And then a separate page, which could even be served from a different domain, that reads
those Check Ins and puts them on a page, would look like this:

    <html>
    	<body>
    		<form>
    			<input type="text" name="place_name" placeholder="Place Name">
    			<input type="text" name="comment" placeholder="Comment">
    		</form>
    		<script>
				var users_library_identity = $.cookie('library_identity');
				var identity_token = $.cookie('library_token');

				// notice the SQLesq query language. It is called LQL.
				// It is basically SQL WHERE clauses but without any joins
				// or group by or anything like that.
				// This query returns all checkins I made within the past 24 hours.
				// I could leave off the last bit of this query that limits it to my origin,
				// which would return checkins made by my friends as well as made by me.
				result = $.ajax("http://chris@libraries.pw/api/query",{
					"query": "including purpose == 'Check In', date_created matches today, origin == " + identity_token 
				}).complete(funtion(result){
					foreach(checkin in result) {
						add_to_html(checkin);
    				}
				});    				
    		</script>
    	</body>
    </html>

For more information, have a look through these presentation slides:
https://docs.google.com/presentation/d/1OxoolWUo2iY_ohxG_HHxd1gQTm3JA52pvWRnefl9IlA/pub?start=false&loop=false&delayms=3000#slide=id.p