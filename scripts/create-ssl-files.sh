#! /bin/bash
#
# create-ssl-files.sh
# Copyright (C) 2015 dhilipsiva <dhilipsiva@gmail.com>
#
# Distributed under terms of the MIT license.
#


openssl req -nodes -new -x509 -keyout confs/watchmen.key -out confs/watchmen.crt
