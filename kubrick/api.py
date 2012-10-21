# copyright: (c) 2012 by Hansel Dunlop.
# license: ISC, see LICENSE for more details.
#
# kubrick.api
#
# This module implements the Kubrick api.
#

import os

from boto.ec2.connection import EC2Connection
from boto.ec2 import get_region
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from fabric.api import env, put, run
from fabric.contrib.files import append
from fabric.state import connections
import sys
import time

import config

class Server(object):
    install_command_map = {
        'apt': 'sudo apt-get install',
        'pip': 'pip install --upgrade',
        'easy_install': 'easy_install --upgrade',
    }


class AWSServer(Server):

    def __init__(self, config, identifier):
        self.key_id = config.AWS_ACCESS_KEY_ID
        self.secret_key = config.AWS_SECRET_ACCESS_KEY
        self.ami_id = config.BASE_AMI
        self.config = config
        self.key_filename = config.KEY_FILENAME
        self.identifier = identifier
        self.conn = EC2Connection(self.key_id, self.secret_key)
        self.instance = None
        self.root_account = config.USERNAME
        self.operating_system = config.OPERATING_SYSTEM
        if self.operating_system == 'Ubuntu':
            self.sudo_required = True
        else:
            self.sudo_required = False


    def run(self, command, warn_only=False):
        if not self.instance:
            raise Exception('No machine attached to this server instance')
        env.host_string = self.root_account + '@' + self.instance.public_dns_name
        env.disable_known_hosts = True
        env.user = self.config.USERNAME
        env.connection_attempts = 6
        env.warn_only = warn_only
        env.key_filename = self.key_filename
        if self.sudo_required:
            command = 'sudo ' + command
        run(command)


    def append(self, filename, text):
        if not self.instance:
            raise Exception('No machine attached to this server instance')
        env.host_string = self.root_account + '@' + self.instance.public_dns_name
        env.disable_known_hosts = True
        env.user = self.config.USERNAME
        env.connection_attempts = 6
        env.key_filename = self.key_filename
        if self.sudo_required:
            append(filename, text, use_sudo=True)
        else:
            append(filename, text)


    def put(self, src, dest):
        env.host_string = self.root_account + '@' + self.instance.public_dns_name
        env.disable_known_hosts = True
        env.user = self.config.USERNAME
        env.connection_attempts = 6
        env.key_filename = self.key_filename
        if self.sudo_required:
            put(src, dest, use_sudo=True, mirror_local_mode=True)
            return
        put(src, dest, mirror_local_mode=True)


    def start_server(self):
        self.instance = start_server_from_ami(self)


    def destroy(self):
        if self.instance:
            print 'Destroying AWS server', self.instance
            self.instance.terminate()
        else:
            print 'No instance on this server object'


    def reboot(self):
        self.run('reboot')
        time.sleep(30)
        print "Reconnecting",
        sys.stdout.flush()
        for retry in range(12):
            try:
                print ".",
                sys.stdout.flush()
                env.host_string = self.root_account + '@' + self.instance.public_dns_name
                connections.connect(env.host_string)
                break
            except:
                print "-",
                sys.stdout.flush()
                time.sleep(10)
        print


class UbuntuMixin(object):
    '''A mixin for Ubuntu based servers'''

    apt_updated = False
    apt_command = 'apt-get -qq -y'

    def make_swap(self, size):
        swap_location = '/var/swap'
        self.run('dd if=/dev/zero of=%s bs=1M count=%d' % (swap_location, size,))
        self.run('mkswap ' + swap_location)
        self.run('swapon ' + swap_location)
        self.append(
            '/etc/fstab', '%s swap swap defaults 0 0' % (swap_location,)
        )


    def purge_apt_packages(self):
        self.update_apt_if_necessary()
        for package in self.APT_PURGES:
            self.run(self.apt_command + ' --purge remove ' + package)


    def update_apt_if_necessary(self):
        if not self.apt_updated:
            self.run(self.apt_command + ' update')
            self.apt_updated = True


    def upgrade_installed_packages(self):
        self.update_apt_if_necessary()
        self.run(self.apt_command + ' upgrade')
        self.apt_updated = False


    def install_apt_packages(self):
        self.update_apt_if_necessary()
        self.run(self.apt_command + ' install ' + ' '.join(self.APT_INSTALLS))


    def install_python_modules(self):
        self.run('easy_install -U distribute')
        for package in self.PIP_INSTALLS:
            self.run('pip install %s' % (package,))


    def configure_locales(self):
        # prevents certain warning messages
        self.run('locale-gen en_US en_US.UTF-8 en_GB.UTF-8')
        self.run('dpkg-reconfigure locales')
        self.run('mkdir -p /etc/ssl/intermediate_and_root_certs/')


    def add_non_root_user(self, user, uid, gid, groups, shell='/bin/bash'):
        groups_arg = ','.join(groups)

        self.run('groupadd --gid %d %s' % (gid, user))
        self.run(
            'useradd -m -s %s --uid %d --gid %d -G %s %s' % (
                shell, uid, gid, groups_arg, user
            )
        )


    def put_static_config_files(self):
        # recursively put all the files in the server_config dir
        config_files = []
        for dirname, dirs, files in os.walk(self.CONFIG_LOCATION):
            for path in files:
                full_path = os.path.join(dirname, path)
                config_files.append(
                    (full_path, full_path.replace(self.CONFIG_LOCATION, ''))
                )

        for src, dest in config_files:
            self.run('mkdir -p ' + os.path.dirname(dest))
            self.put(src, dest)


    def setup_cron(self):
        self.run('chmod 600 /etc/crontab')
        self.run('chgrp root /etc/crontab')
        self.run('chown root /etc/crontab')


    def set_hostname(self, hostname):
        self.run('hostname %s' % (hostname,))



def get_region_from_name(zone_name=config.DEFAULT_ZONE):
    return get_region(
        zone_name,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
    )


def create_aws_connection():
    return EC2Connection(
        config.AWS_ACCESS_KEY_ID,
        config.AWS_SECRET_ACCESS_KEY,
        region=get_region_from_name()
    )


def create_storage_connection():
    return S3Connection(
        config.AWS_ACCESS_KEY_ID,
        config.AWS_SECRET_ACCESS_KEY,
    )


def put_file_into_bucket_with_key(path, bucketname, key):
    conn = create_storage_connection()
    buckets = conn.get_all_buckets()
    bucket = None
    for b in buckets:
        if b.name == bucketname:
            bucket = b
    if not bucket:
        raise Exception('Bucket with name ' + bucketname + ' not found')
    k = Key(bucket)
    k.key = key
    k.set_contents_from_filename(path)
    print path, 'has been saved in', bucket.name, 'with key:', key


def get_instance(instance_id):
    conn = create_aws_connection()
    reservations = conn.get_all_instances([instance_id])[0]
    return reservations.instances[0]


def start_server_from_ami(server):
    """Starts a VM on AWS using a given AMI and name"""
    if not server.conn:
        server.conn = create_aws_connection()
    reservation = server.conn.run_instances(
        server.ami_id, security_groups=server.config.SECURITY_GROUPS,
        key_name=server.config.KEY_NAME,
        instance_type=server.config.DEFAULT_INSTANCE_TYPE,
        placement=server.config.DEFAULT_ZONE,
    )

    instance = reservation.instances[0]

    print 'Waiting for instance to come up...'
    # Give the instance a chance to exist
    time.sleep(1.5)
    while instance.state != 'running':
        print '.',
        sys.stdout.flush()
        time.sleep(2)
        instance.update()
    print
    server.conn.create_tags([instance.id], {'Name': server.identifier})
    return instance

