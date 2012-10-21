
import unittest
from mock import call, patch

import kubrick


class AWSServerTest(unittest.TestCase):

    def test_init_works(self):
        # No need to test all the constants, just checking that it works

        identifier = 'test_server'
        kubrick.config.OPERATING_SYSTEM = 'Ubuntu'

        server = kubrick.api.AWSServer(kubrick.config, identifier)

        self.assertEqual(server.identifier, identifier)
        self.assertTrue(server.sudo_required)

        kubrick.config.OPERATING_SYSTEM = 'Arch'

        server = kubrick.api.AWSServer(kubrick.config, identifier)
        self.assertFalse(server.sudo_required)


    @patch('kubrick.api.start_server_from_ami')
    def test_start_server_delegates_to_correct_function(self, mock_start_server):

        server = kubrick.api.AWSServer(kubrick.config, 'sst')

        server.start_server()

        self.assertEqual(
            mock_start_server.call_args_list,
            [call(server)]
        )
