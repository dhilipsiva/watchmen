from constants import SHERLOG

roledefs = {
    SHERLOG: [
        '1.2.3.4',  # List of IP that will run sherlog (Tyically, just one IP)
    ],
}


SHERLOG_TITLE = "MyApp | Sherlog"  # Just some title
SHERLOG_USER = "admin"  # Sherlog has only one admin accound. This is username
SHERLOG_PASS = "password"  # Admin password.
SHERLOG_SERVER_URL = "sherlog.example.com"  # Public address of sherlog server
SHERLOG_MONGO_HOST = "localhost"  # Privite / Public address
SHERLOG_MONGO_USER = "user"  # Mongo user
SHERLOG_MONGO_PASS = "pass"  # Mongo password
