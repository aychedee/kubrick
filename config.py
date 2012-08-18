# copyright: (c) 2012 by Hansel Dunlop.
# license: ISC, see LICENSE for more details.
#

# AWS config settings, secrets.py is never committed as it contains all
# the sensitive account information

from secrets import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, KEY_FILENAME

BASE_AMI = 'ami-013f9768' # us1-east, micro, Ubuntu 12.04, ebs backed
DEFAULT_INSTANCE_TYPE = 't1.micro'
DEFAULT_ZONE = 'us-east-1b'
SECURITY_GROUPS = ['default']
KEY_NAME = 'hanseldunlop'
KEY_FILE_PATH = '~/.ssh/'
OPERATING_SYSTEM = 'Ubuntu'
USERNAME = 'ubuntu'




# AWS constants
MICRO = 't1.micro'
SMALL = 'm1.small'
MEDIUM = 'm1.medium'
LARGE = 'm1.large'
X_LARGE = 'm1.xlarge'

HI_CPU_MEDIUM = 'c1.medium'
HI_CPU_X_LARGE = 'c1.xlarge'

HI_MEM_X_LARGE = 'm2.xlarge'
HI_MEM_2X_LARGE = 'm2.2xlarge'
HI_MEM_4X_LARGE = 'm2.4xlarge'

EU_WEST_1 = 'eu-west-1'
SA_EAST_1 = 'sa-east-1'
US_EAST_1 = 'us-east-1'
US_WEST_2 = 'us-west-2'
US_WEST_1 = 'us-west-1'
AP_NORTHEAST_1 = 'ap-northeast-1'
AP_SOUTHEAST_1 = 'ap-southeast-1'
