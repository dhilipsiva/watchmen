#! /bin/bash
#
# sentry_worker.sh
# Copyright (C) 2015 dhilipsiva <dhilipsiva@gmail.com>
#
# Distributed under terms of the MIT license.
#


set -e
# go in your project root
cd %(confs_folder)s
# activate the virtualenv
source %(sentry_env)s/bin/activate
exec sentry --config=sentry.py celery worker -B >> %(sentry_worker_log)s
