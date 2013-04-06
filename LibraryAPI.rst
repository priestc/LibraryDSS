Non-Hierarchical File System Project
====================================
* Only for immutable data (media)
    * Video, Images, Music, Archives
* Once a file enters my library, it is banished from my "Hierarchical world" forever.
* Each media item has one cannonical living place. I can cache an item from another library into my own.
* All data in your library represents all the data you have access to.
* Your library "outlives" all devices.

Library Service
===============

The library is a service that acts as an intermediary between clients (devices)
and the storage engine. The Library should be hosted in an always on manner.
The Library will only serve JSON data, no media data will pass through the Library.

Library URL format:
    library://username@provider.com

Library Query:
    library://username@provider.com/query?type=video&genre=horror

Library Response:
    JSON response of all hits. Each item includes the url for the data,
    as well as all metadata for that item.
    [
        {
            "size": 354234324,
            "md5": "d21ac23d43e242e",
            "origin": "library://fred@somewhere.else.com"
            "url": "http://mybucket.s3.amazonaws.com/poltergeist.avi",
            "metadata": {
                "type": "video",
                "genre": "horror",
                "title": "Poltergeist",
                "release_date": "1982-6-4"
            }
        },
        {
            "size": 354234324,
            "md5": "d21ac23d43e242e",
            "origin": "library://fred@somewhere.else.com"
            "url": "http://mybucket.s3.amazonaws.com/dracula.avi",
            "metadata": {
                "type": "video",
                "genre": "horror",
                "title": "Dracula"
            }
        }
    ]

Storage Engine
==============
The storage engine is where the actual bulk of the media are stored.
Examples of storage engines can be Amazon Glacier, Amazon S3, Dropbox and Google Drive.
Storage Engines are configured on the Library server.
For instance, you can configure your storage engines to work such that all objects over 1GB in size get sent to Glacier,
all files under 10MB go to Dropbox, and all other objects go to Amazon S3.
Lets say sometime in the future you lose trust in Google, and want to move all your data off of Google Drive.
You can go into your library's settings and instruct the library to begin migrating all data from Google Drive
to Amazon S3.

Client (Command Line Application)
=================================
``to_library`` is a command line application used to add items to your library.
It is configured to use your library through it's settings::

    $ to_library set_library library://chris@mylibrary.com

To add media to your library, pass the file into the command line utility and include metadata.
Metadata items are key/value in nature and always completely optional::

    $ to_library nosferatu.avi --genre=horror --title="Nosferatu"

The ``to_library`` application uploads the movie directly to the storage engine.
Details of which engine we are uploading to are transparent to the end user.

you can also add by url::

    $ to_library http://link.to/nosferatu.avi --genre=horror --title="Nosferatu"


In this case, the library server will perform the download from the URL,
and also perform the upload to the storage engine.

Client (device)
===============
A device can be configured to directly use your library for management.
In your settings of you camera/microphone/webcam, enter your library uri.
Whenever a picture is taken, the file is sent to your library.
Your device will have a UI to assist in adding metadata.
Your device will also be configured to automatically add metadata to each item,
such as "date_taken" and "camera_model".
All devices will delete the created media locally after the file has been successfully saved on the storage engine.
Devices only send data to the library, manager applications do all the managing.
Devices can keep cached copies of created media for UX reasons
(such as a "recently takes photos" section of a camer app),
but devices should not attempt to let the user manage content.