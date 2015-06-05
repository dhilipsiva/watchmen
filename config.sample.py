from constants import SHERLOG, SENTRY

roledefs = {
    SHERLOG: [
        '1.2.3.4',  # List of IP that will run sherlog (Tyically, just one IP)
    ],
    SENTRY: [
        '1.2.3.4',  # List of IP that will run sentry (Tyically, just one IP)
    ],
}


SHERLOG_TITLE = "MyApp | Sherlog"  # Just some title
SHERLOG_USER = "admin"  # Sherlog has only one admin accound. This is username
SHERLOG_PASS = "password"  # Admin password.
SHERLOG_SERVER_URL = "sherlog.example.com"  # Public address of sherlog server
SHERLOG_MONGO_HOST = "localhost"  # Privite / Public address
SHERLOG_MONGO_USER = "sherlog"  # Mongo user
SHERLOG_MONGO_PASS = "pass"  # Mongo password

SENTRY_DB_NAME = SENTRY
SENTRY_DB_USER = SENTRY
SENTRY_DB_PASS = "pass"
SENTRY_DB_HOST = ""
SENTRY_DB_PORT = ""
SENTRY_SERVER_URL = "sentry.example.com"
SENTRY_URL_PREFIX = "https://%s" % SENTRY_SERVER_URL
SENTRY_ADMIN_EMAIL = "sentry@example.com"
SENTRY_REDIS_INSTANCE = SENTRY
SENTRY_REDIS_HOST = '127.0.0.1'
SENTRY_REDIS_PORT = "6379"
SENTRY_BROKER_URL = "redis://%s:%s" % (SENTRY_REDIS_HOST, SENTRY_DB_PORT)
SENTRY_WEB_HOST = '0.0.0.0'
SENTRY_WEB_PORT = "9000"
SENTRY_EMAIL_HOST = 'smtp.gmail.com'
SENTRY_EMAIL_HOST_PASS = 'pass'
SENTRY_EMAIL_HOST_USER = 'sentry@example.com'
SENTRY_EMAIL_PORT = "465"
SENTRY_EMAIL_USE_TLS = "True"  # [IMPORTANT] Use only empty string for `False`
