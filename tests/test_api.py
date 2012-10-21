
import unittest
from mock import call, Mock, patch

import kubrick


@patch('kubrick.api.start_server_from_ami')
class AWSServerTest(unittest.TestCase):

    def test_init_works(self, _):
        # No need to test all the constants, just checking that it works

        identifier = 'test_server'
        kubrick.config.OPERATING_SYSTEM = 'Ubuntu'

        server = kubrick.api.AWSServer(kubrick.config, identifier)

        self.assertEqual(server.identifier, identifier)
        self.assertTrue(server.sudo_required)

        kubrick.config.OPERATING_SYSTEM = 'Arch'

        server = kubrick.api.AWSServer(kubrick.config, identifier)
        self.assertFalse(server.sudo_required)


    def test_start_server_delegates_to_correct_function(self, mock_start_server):

        server = kubrick.api.AWSServer(kubrick.config, 'sst')

        server.start_server()

        self.assertEqual(
            mock_start_server.call_args_list,
            [call(server)]
        )
        self.assertEqual(server.instance, mock_start_server.return_value)


    @patch('kubrick.api.time.sleep')
    def test_reboot_runs_reboot(self, mock_sleep, _):

        server = kubrick.api.AWSServer(kubrick.config, 'sst')
        server.run = Mock()

        server.reboot()

        self.assertEqual(
            server.run.call_args_list,
            [call('reboot')]
        )


    def test_host_string_property(self, _):

        server = kubrick.api.AWSServer(kubrick.config, 'sst')
        server.root_account = 'godzilla'
        server.instance = Mock()
        server.instance.public_dns_name = 'tokyo.com'

        self.assertEqual(
            server.host_string,
            server.root_account + '@' + server.instance.public_dns_name
        )

