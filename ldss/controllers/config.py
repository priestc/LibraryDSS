import os
project_path = os.path.dirname(os.path.abspath(__file__))
auth_session_expire = 3600 * 24 * 7
error_template = "error.html"
debug=True

dropbox_app_type = 'dropbox'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'libraries',                      
        'USER': 'chris',
        'PASSWORD': 'spatula',
        'HOST': 'localhost',
        'PORT': '',
    }
}