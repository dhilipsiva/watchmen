#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 dhilipsiva <dhilipsiva@gmail.com>
#
# Distributed under terms of the MIT license.

"""

"""

import posixpath
from pipes import quote
from os.path import join, expanduser
from contextlib import contextmanager

import requests

from fabric.state import env
from fabric.contrib import files
from fabric.operations import get
from fabric.decorators import roles
from fabric.api import run, task, sudo, prefix

from fabtools import user, require
from fabtools.files import is_file
from fabtools.utils import abspath
from fabtools.vagrant import vagrant
from fabtools.require.git import working_copy

from config import roledefs, SHERLOG, SHERLOG_TITLE, SHERLOG_USER, \
    SHERLOG_PASS, SHERLOG_SERVER_URL, SHERLOG_MONGO_HOST, SHERLOG_MONGO_USER, \
    SHERLOG_MONGO_PASS

vagrant = vagrant  # Silence flake8

# GitHub users who have/will have ssh access (deploy access) to the server
SSH_USERS = ['dhilipsiva']

env.project = 'watchmen'
env.repository = 'git@github.com:dhilipsiva/watchmen.git'
env.deploy_user = env.project
env.deploy_user_home = join("/home", env.deploy_user)
env.apps_path = join(env.deploy_user_home, 'apps')
env.code_root = join(env.apps_path, env.project)
env.local_conf_folder = "confs"

# Sherlog Configuration
env.sherlog_env = join(env.deploy_user_home, "envs", SHERLOG)
env.sherlog_path = join(env.deploy_user_home, "apps", SHERLOG)
env.sherlog_remote = "https://github.com/burakson/sherlogjs.git"
env.sherlog_node_host = "localhost"
env.sherlog_node_port = "3000"
env.sherlog_bind = "%s:%s" % (env.sherlog_node_host, env.sherlog_node_port)
env.sherlog_title = SHERLOG_TITLE
env.sherlog_user = SHERLOG_USER
env.sherlog_pass = SHERLOG_PASS
env.sherlog_server_url = SHERLOG_SERVER_URL
env.sherlog_mongo_host = SHERLOG_MONGO_HOST
env.sherlog_mongo_user = SHERLOG_MONGO_USER
env.sherlog_mongo_pass = SHERLOG_MONGO_PASS
env.sherlog_mongo_db = "sherlog"
env.sherlog_conf_template = '%s/%s.json' % (env.local_conf_folder, SHERLOG)
env.sherlog_conf = "%s/config/config.json" % env.sherlog_path


# Just default Vagrant configuration
env.roledefs = {
    SHERLOG: ['192.168.50.5', ],
}

env.roledefs['all'] = [h for r in env.roledefs.values() for h in r]


@task
def vag():
    """
    Just Vagrant configs
    """
    env.user = env.deploy_user


@task
def cloud():
    """
    Cloud Host config
    """
    env.user = env.deploy_user
    env.roledefs = roledefs
    env.roledefs['all'] = [h for r in env.roledefs.values() for h in r]


@task
@roles("all")
def ping():
    """
    This is just a test function.
    """
    run("echo pong")


@task
def add_my_key():
    """
    Add your public key to authorized_keys
    """
    user.add_ssh_public_key(env.deploy_user, expanduser("~/.ssh/id_rsa.pub"))


@task
def create_deploy_user():
    """
    Create the deploy user
    Usage: fab -i path/to/private.pem -H existing_user@host create_deploy_user
    """
    require.users.user(env.deploy_user, shell='/bin/bash')
    require.users.sudoer(env.deploy_user)
    add_my_key()


@task
@roles("all")
def sync_auth_keys():
    """
    Add multiple public keys to the user's authorized SSH keys from GitHub.
    """

    ssh_dir = posixpath.join(user.home_directory(env.user), '.ssh')
    require.files.directory(ssh_dir, mode='700', owner=env.user, use_sudo=True)
    authorized_keys_filename = posixpath.join(ssh_dir, 'authorized_keys')
    require.files.file(
        authorized_keys_filename, mode='600', owner=env.user, use_sudo=True)

    sudo('cat /dev/null > %s' % quote(authorized_keys_filename))

    for gh_user in SSH_USERS:
        r = requests.get("https://api.github.com/users/%s/keys" % gh_user)
        for key in r.json():
            sudo(
                "echo %s >> %s"
                % (quote(key["key"]), quote(authorized_keys_filename)))


def create_nodeenv(directory):
    directory = quote(directory)
    command = 'nodeenv %s' % directory
    run(command)


def nodeenv_exists(directory):
    """
    Check if a Python `virtual environment`_ exists.
    .. _virtual environment: http://www.virtualenv.org/
    """
    return is_file(posixpath.join(directory, 'bin', 'node'))


@task
def ensure_nodeenv(nodeenv):
    sudo("pip install nodeenv")
    """
    Require a Node `virtual environment`.
    """

    if not nodeenv_exists(nodeenv):
        create_nodeenv(nodeenv)


@contextmanager
def nodeenv(directory, local=False):
    """
    Context manager to activate an existing Node `virtual environment`.
    """

    # Build absolute path to the nodeenv activation script
    nodeenv_path = abspath(directory, local)
    activate_path = join(nodeenv_path, 'bin', 'activate')

    # Source the activation script
    with prefix('. %s' % quote(activate_path)):
        yield


def ensure_sherlog_node_deps():
    """
    ensure Sherlog's node deps
    """
    with nodeenv(env.sherlog_env):
        run("cd %s && npm install && bower install --config.interactive=false"
            % env.sherlog_path)
        run("npm install -g gulp")


@task
@roles('all')
def ensure_common_deps():
    require.deb.uptodate_index()
    require.deb.packages([
        "git",
        "wget",
        "curl",
        "python-software-properties",
        "python-dev",
        "build-essential",
        "supervisor",
        "vim",
        "python-pip",
    ])


def uptodate_index():
    """
    apt-get update
    """
    require.deb.uptodate_index()


def mongo_apt_config():
    """
    docstring for mongo_apt_config
    """
    sudo(
        "apt-key adv --keyserver hkp://keyserver.ubuntu.com:80"
        " --recv 7F0CEB10")
    run('echo "deb http://repo.mongodb.org/apt/ubuntu'
        ' "$(lsb_release -sc)"/mongodb-org/3.0 multiverse" |'
        ' sudo tee /etc/apt/sources.list.d/mongodb-org-3.0.list')


@task
@roles(SHERLOG)
def ensure_sherlog_deps():
    # mongo_apt_config()
    uptodate_index()
    require.deb.packages([
        # "mongodb-org",
        "mongodb",
    ])


@task
@roles(SHERLOG)
def upload_sherlog_conf():
    files.upload_template(
        env.sherlog_conf_template, env.sherlog_conf,
        context=env, backup=False, use_sudo=True)
    # sudo('chmod +x %s' % env.sherlog_conf)
    with nodeenv(env.sherlog_env):
        run("cd %s && gulp" % env.sherlog_path)
    get("%s/public/js/sherlog.min.js" % env.sherlog_path, "generated")


@task
@roles(SHERLOG)
def setup_sherlog():
    """
    Function to setup sherlog
    """
    uptodate_index()
    ensure_sherlog_deps()
    working_copy(env.sherlog_remote, env.sherlog_path)
    ensure_nodeenv(env.sherlog_env)
    with nodeenv(env.sherlog_env):
        run("npm install -g bower")
    ensure_sherlog_node_deps()
