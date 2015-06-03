#! /bin/bash
#
# sherlog.sh
# Copyright (C) 2015 dhilipsiva <dhilipsiva@gmail.com>
#
# Distributed under terms of the MIT license.


set -e
# go in your project root
cd %(sherlog_path)s
# activate the virtualenv
source %(sherlog_env)s/bin/activate
exec npm start >> %(sherlog_log)s
