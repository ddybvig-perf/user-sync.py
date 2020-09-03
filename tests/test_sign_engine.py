import pytest
import six
# import keyring

from sign_client.client import SignClient
from user_sync.connector.directory import DirectoryConnector
from user_sync.engine.sign import SignSyncEngine


@pytest.fixture
def example_engine(modify_root_config, sign_config_file):
    modify_root_config(['post_sync', 'modules'], 'sign_sync')
    modify_root_config(['post_sync', 'connectors'], sign_config_file)
    args = {'config_filename': sign_config_file}
    args['entitlement_groups'] = 'signgroup'
    args['sign_orgs'] = []
    return SignSyncEngine(args)


def test_load_users_and_groups(example_engine, example_user):
    dc = DirectoryConnector

    user = {'user@example.com': example_user}

    def dir_user_replacement(groups, extended_attributes, all_users):
        return six.itervalues(user)

    # replace the call to load directory groups and users with the example user dict. this dict will then be modified
    # by other methods in the engine/sign.py which are almost identical to the same methods in engine/umapi.py right now
    # these methods should be altered for sign-specific usage - for example, there's no need to specify an identity
    # type for sign-syncing purposes, but it has been left in there so that the code can run
    dc.load_users_and_groups = dir_user_replacement
    directory_users = example_engine.read_desired_user_groups({'directory_group': 'adobe_group'}, dc)
    assert directory_users is not None


def test_sign_client(sign_config_file):
    client_config = {
        'console_org': None,
        'host': 'api.na2.echosignstage.com',
        'key': 'allsortsofgibberish1234567890',
        'admin_email': 'brian.nickila@gmail.com'
    }
    sign_client = SignClient(client_config)
    assert sign_client.key == client_config['key']
    # this next line works...but then causes the keyring import in config.get credential to fail and thus use
    # cryptfile instead, which in turn causes the test to fail. workaround is to run once, then comment out
    # keyring.set_password('sign_key', client_config['admin_email'], client_config['key'])
    secure_client_config = {
        'console_org': None,
        'host': 'api.na2.echosignstage.com',
        'secure_key_key': 'sign_key',
        'admin_email': 'brian.nickila@gmail.com'
    }
    sign_client = SignClient(secure_client_config)
    assert sign_client.key == client_config['key']
