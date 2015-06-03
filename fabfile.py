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
from contextlib import contextmanager
from os.path import join, expanduser, basename

import requests

from fabric.state import env
from fabric.contrib import files
from fabric.decorators import roles
from fabric.operations import get, settings
from fabric.colors import _wrap_with as wrap_with
from fabric.api import run, task, sudo, prefix, hide, abort

from fabtools import user, require
from fabtools.files import is_file
from fabtools.utils import abspath
from fabtools.vagrant import vagrant
from fabtools.require.git import working_copy

from config import roledefs, SHERLOG, SHERLOG_TITLE, SHERLOG_USER, \
    SHERLOG_PASS, SHERLOG_SERVER_URL, SHERLOG_MONGO_HOST, SHERLOG_MONGO_USER, \
    SHERLOG_MONGO_PASS

vagrant = vagrant  # Silence flake8
red_bg = wrap_with('41')

# GitHub users who have/will have ssh access (deploy access) to the server
SSH_USERS = ['dhilipsiva']

env.project = 'watchmen'
env.repository = 'git@github.com:dhilipsiva/watchmen.git'
env.deploy_user = env.project
env.deploy_user_home = join("/home", env.deploy_user)
env.apps_path = join(env.deploy_user_home, 'apps')
env.envs_path = join(env.deploy_user_home, 'envs')
env.code_root = join(env.apps_path, env.project)
env.logs_folder = "%(deploy_user_home)s/logs" % env
env.confs_folder_local = "confs"
env.confs_folder = "%(deploy_user_home)s/confs" % env
env.scripts_folder_local = "scripts"
env.scripts_folder = "%(deploy_user_home)s/scripts" % env

# Nginx configs
env.nginx_conf_temaplte = "%s/nginx.conf" % env.confs_folder_local
env.nginx_conf = '%s/nginx.conf' % env.confs_folder
env.ssl_folder = "%(deploy_user_home)s/ssl" % env
env.ssl_crt = "%(ssl_folder)s/%(project)s.crt" % env
env.ssl_key = "%(ssl_folder)s/%(project)s.key" % env
env.ssl_crt_local = "%(confs_folder_local)s/%(project)s.crt" % env
env.ssl_key_local = "%(confs_folder_local)s/%(project)s.key" % env
env.nginx_enable_path = "/etc/nginx/sites-enabled/"

# Sherlog Configuration
env.sherlog = SHERLOG
env.sherlog_env = join(env.envs_path, SHERLOG)
env.sherlog_path = join(env.apps_path, SHERLOG)
env.sherlog_log = "%(logs_folder)s/%(sherlog)s.log" % env
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
env.sherlog_conf_template = '%s/%s.json' % (env.confs_folder_local, SHERLOG)
env.sherlog_conf = "%s/config/config.json" % env.sherlog_path
env.sherlog_script = "%(scripts_folder)s/%(sherlog)s.sh" % env
env.sherlog_script_template = '%(scripts_folder_local)s/%(sherlog)s.sh' % env


# Supervisor Configuration
env.supervisor_ctl = '/usr/bin/supervisorctl'  # supervisorctl script
env.supervisor_autostart = 'true'  # true or false
env.supervisor_autorestart = 'true'  # true or false
env.supervisor_redirect_stderr = 'true'  # true or false
env.supervisor_stdout_logfile = \
    '%(logs_folder)s/supervisord_%(project)s.log' % env
env.supervisord_conf_template = \
    '%(confs_folder_local)s/supervisord.conf' % env
env.supervisord_conf = \
    '%(confs_folder)s/supervisord_%(project)s.conf' % env


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


def ensure_dirs():
    require.files.directories([
        env.envs_path,
        env.apps_path,
        env.logs_folder,
        env.confs_folder,
        env.scripts_folder,
        env.ssl_folder,
        ], owner=env.deploy_user)


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
        run("npm install -g bower")
        run("cd %s && npm install && bower install --config.interactive=false"
            % env.sherlog_path)
        run("npm install -g gulp")


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


def ensure_sherlog_deps():
    # mongo_apt_config()
    require.deb.ppa('ppa:nginx/stable')
    uptodate_index()
    require.deb.packages([
        # "mongodb-org",
        "mongodb",
        "nginx"
    ])


def upload_sherlog_conf():
    files.upload_template(
        env.sherlog_conf_template, env.sherlog_conf,
        context=env, backup=False, use_sudo=True)
    # sudo('chmod +x %s' % env.sherlog_conf)
    with nodeenv(env.sherlog_env):
        run("cd %s && gulp" % env.sherlog_path)
    get("%s/public/js/sherlog.min.js" % env.sherlog_path, "generated")


def upload_ssl_files():
    files.upload_template(env.ssl_crt_local, env.ssl_crt)
    files.upload_template(env.ssl_key_local, env.ssl_key)


def test_nginx_conf():
    with settings(
            hide('running', 'stdout', 'stderr', 'warnings'), warn_only=True):
        res = sudo('nginx -t -c /etc/nginx/nginx.conf')
    if 'test failed' in res:
        abort(red_bg(
            'NGINX configuration test failed!'
            ' Please review your parameters.'))


def upload_nginx_conf():
    files.upload_template(
        env.nginx_conf_temaplte, env.nginx_conf, context=env, use_sudo=True)
    sudo(
        'ln -sf %s %s/%s'
        % (env.nginx_conf, env.nginx_enable_path, basename(env.nginx_conf)))
    # sudo('rm -f %s%s' % (env.nginx_enable_path, 'default'))
    test_nginx_conf()
    sudo('nginx -s reload')


def upload_sherlog_script():
    files.upload_template(
        env.sherlog_script_template, env.sherlog_script, context=env)
    sudo('chmod +x %s' % env.sherlog_script)


def supervisor_restart():
    with settings(
            hide('running', 'stdout', 'stderr', 'warnings'), warn_only=True):
        res = sudo('%(supervisor_ctl)s restart all' % env)
    if 'ERROR' in res:
        print red_bg("NOT STARTED!:\n%s" % res)


def reload_supervisorctl():
    sudo('%(supervisor_ctl)s reread' % env)
    sudo('%(supervisor_ctl)s reload' % env)


@task
@roles(SHERLOG)
def upload_supervisord_conf():
    files.upload_template(
        env.supervisord_conf_template, env.supervisord_conf,
        context=env, use_sudo=True)
    sudo(
        'ln -sf %s /etc/supervisor/conf.d/%s'
        % (env.supervisord_conf, basename(env.supervisord_conf)))
    reload_supervisorctl()
    supervisor_restart()


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
    ensure_sherlog_node_deps()
    upload_sherlog_conf()
