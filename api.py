# copyright: (c) 2012 by Hansel Dunlop.
# license: ISC, see LICENSE for more details.
#
# kubrick.api
#
# This module implements the Kubrick api.
#


from boto.ec2.connection import EC2Connection
from boto.ec2 import get_region
from fabric.api import env, put, run
from fabric.context_managers import cd
import time
from urlparse import urljoin

import aws_config as config

class Server(object):

    def __init__(self, provider_config):
        self.conn = EC2Connection(
            provider_config.AWS_ACCESS_KEY_ID,
            provider_config.AWS_SECRET_ACCESS_KEY
        )

    def disconnect(self):
        self.conn.close()

    def connect(self, identifier):
        pass


    def create(self):
        pass


    def destroy(self):
        pass


class AWSServer(Server):

    def __init__(self, key_id, secret_key, identifier):
        self.conn = EC2Connection(key_id, secret_key)
        self.save_config(server_id=identifier)
        self.save_config(AWS_ACCESS_KEY_ID=key_id)
        self.save_config(AWS_SECRET_ACCESS_KEY=secret_key)


class AWSConfig(object):

    def __init__(self, key_id, secret_key, zone):
        self.AWS_ACCESS_KEY_ID = key_id
        self.AWS_SECRET_ACCESS_KEY = secret_key


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


def get_instance(instance_id):
    conn = create_aws_connection()
    reservations = conn.get_all_instances([instance_id])[0]
    return reservations.instances[0]


def django_admin_setup():
    #ln -s /usr/local/lib/python2.7/dist-packages/django/contrib/admin/static/admin thenpsx.com/static/admin
    pass

def postgresql_setup():
    # edit pga_gb.conf
    # edit pga_hba.conf
    # edit postgres.conf
    # create tables
    # create users
    # sudo -u postgres createuser -P npsx-dbadmin
    # sudo -u postgres createdb -O npsx-dbadmin npsx
    pass


def pip_install():
    # django
    # redis
    pass

def apt_get_install():
    #redis
    pass

def redis_setup():
    # edit redis.conf
    pass


class Server(object):
    ami = config.BASE_AMI
    size = config.DEFAULT_INSTANCE_TYPE
    install_command_map = {
        'apt': 'sudo apt-get install',
        'pip': 'pip install --upgrade',
        'easy_install': 'easy_install --upgrade',
    }

    def start(self):
        pass


    def configure(self):
        pass


    def install_packages(self):
        for package in self.package_list:
            run('%s %s' % (self.install_command_map[package[0]], package[1]))


    def terminate(self):
        pass


class ApplicationServer(Server):

    package_list = [
        ('apt', 'apache2'),
        ('apt', 'squid3'),
    ]

    def configure(self):
        run('sudo apt-get update; sudo apt-get upgrade')
        self.install_packages()
        # copy sites-available and symlink them
        with cd('/etc/apache2/sites-available'):
            put(
                'app-server/etc/apache2/sites-available/www.aychedee.com',
                'www.aychedee.com'
            )

        # setup squid
        # create users for squid


class DatabaseServer(Server):

    package_list = [
        ('apt', 'mysql-server'),
    ]



def start_server_from_ami(ami, machine_name):
    """Starts a VM on AWS using a given AMI and name"""
    conn = create_aws_connection()
    reservation = conn.run_instances(
        ami, security_groups=config.SECURITY_GROUPS,
        key_name=config.KEY_NAME,
        instance_type=config.DEFAULT_INSTANCE_TYPE,
        placement=config.DEFAULT_ZONE,
    )

    instance = reservation.instances[0]

    print 'Waiting for instance to come up...'
    while instance.state != 'running':
        print '.',
        time.sleep(2)
        instance.update()
    print
    conn.create_tags([instance.id], {'Name': machine_name})
    return instance



def configure_instance(script, instance):
    """Runs script on a given instance"""
    env.hosts = [config.USERNAME + '@' + instance.public_dns_name]
    env.key_filename = [urljoin(config.KEY_FILE_PATH, config.KEY_NAME)]
    put(script, '/root/')
    run('/root/%s' % (script,))
