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
from fabric.state import connections
import sys
import time
from urlparse import urljoin


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
        self.key_filename = config.KEY_FILE
        self.identifier = identifier
        self.conn = EC2Connection(self.key_id, self.secret_key)
        self.instance = None
        self.root_account = config.USERNAME
        self.operating_system = config.OPERATING_SYSTEM
        if self.operating_system == 'Ubuntu':
            self.sudo_required = True
        else:
            self.sudo_required = False


    def run(self, command):
        if not self.instance:
            raise Exception('No machine attached to this server instance')
        env.host_string = self.root_account + '@' + self.instance.public_dns_name
        env.disable_known_hosts = True
        env.user = self.config.USERNAME
        env.connection_attempts = 6
        env.key_filename = self.key_filename
        if self.sudo_required:
            command = 'sudo ' + command
        run(command)


    def put(self, src, dest):
        env.host_string = self.root_account + '@' + self.instance.public_dns_name
        env.disable_known_hosts = True
        env.user = self.config.USERNAME
        env.connection_attempts = 6
        env.key_filename = '/home/hansel/.ssh/hanseldunlop.pem'
        if self.sudo_required:
            put(src, dest, use_sudo=True)
            return
        put(src, dest)


    def start_server(self):
        self.instance = start_server_from_ami(self)


    def destroy(self):
        print 'Destroying AWS server', self.aws_instance
        self.aws_instance.terminate()


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
    while instance.state != 'running':
        print '.',
        time.sleep(2)
        instance.update()
    print
    server.conn.create_tags([instance.id], {'Name': server.identifier})
    return instance

