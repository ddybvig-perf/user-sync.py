import os
import uuid

import keyring
import pytest
import yaml

from tests.util import update_dict
from user_sync import encryption
from user_sync.credentials import CredentialConfig, CredentialManager, Key, LdapCredentialConfig, UmapiCredentialConfig


@pytest.fixture
def root_config_file(fixture_dir):
    return os.path.join(fixture_dir, 'user-sync-config.yml')


@pytest.fixture
def ldap_config_file(fixture_dir):
    return os.path.join(fixture_dir, 'connector-ldap.yml')


@pytest.fixture
def modify_umapi_config(tmp_config_files):
    (_, _, umapi_config_file) = tmp_config_files

    def _modify_umapi_config(keys, val):
        conf = yaml.safe_load(open(umapi_config_file))
        conf = update_dict(conf, keys, val)
        yaml.dump(conf, open(umapi_config_file, 'w'))

        return umapi_config_file
    return _modify_umapi_config


def test_nested_set(ldap_config_file):
    c = CredentialConfig(ldap_config_file)
    c.set_nested_key(['password'], {'secure': 'somethingverysecure'})
    r = c.get_nested_key(['password', 'secure'])
    assert r == 'somethingverysecure'


def test_retrieve_ldap_creds_valid(tmp_config_files):
    (_, ldap_config_file, _) = tmp_config_files
    c = CredentialConfig(ldap_config_file)
    key = Key(['password'])
    plaintext_cred = c.get_nested_key(key.key_path)
    c.store_key(key)
    retrieved_plaintext_cred = c.retrieve_key(key)
    assert retrieved_plaintext_cred == plaintext_cred


def test_retrieve_ldap_creds_invalid(tmp_config_files):
    (_, ldap_config_file, _) = tmp_config_files
    c = CredentialConfig(ldap_config_file)
    key = Key(['password'])
    # if store_key has not been called previously, retrieve_key returns None
    assert c.retrieve_key(key) is None


def test_revert_valid(tmp_config_files):
    (_, ldap_config_file, _) = tmp_config_files
    c = CredentialConfig(ldap_config_file)
    key = Key(['password'])
    plaintext_cred = c.get_nested_key(key.key_path)
    c.store_key(key)
    reverted_plaintext_cred = c.revert_key(key)
    assert reverted_plaintext_cred == plaintext_cred


def test_revert_invalid(tmp_config_files):
    (_, ldap_config_file, _) = tmp_config_files
    c = CredentialConfig(ldap_config_file)
    key = Key(['password'])
    # assume store_key has not been called
    assert c.revert_key(key) is None


def test_retrieve_revert_ldap_valid(tmp_config_files):
    (_, ldap_config_file, _) = tmp_config_files
    ldap = LdapCredentialConfig(ldap_config_file)
    assert not ldap.parse_secure_key(ldap.get_nested_key(['password']))
    unsecured_key = ldap.get_nested_key(['password'])
    ldap.store()
    with open(ldap_config_file) as f:
        data = yaml.load(f)
        assert ldap.parse_secure_key(data['password'])
    retrieved_key_dict = ldap.retrieve()
    assert retrieved_key_dict['password'] == unsecured_key
    ldap.revert()
    with open(ldap_config_file) as f:
        data = yaml.load(f)
        assert data['password'] == unsecured_key


def test_retrieve_revert_ldap_invalid(tmp_config_files):
    (_, ldap_config_file, _) = tmp_config_files
    ldap = LdapCredentialConfig(ldap_config_file)
    assert not ldap.parse_secure_key(ldap.get_nested_key(['password']))
    # if store has not been previously called before retrieve and revert we can expect the following
    retrieved_key_dict = ldap.retrieve()
    assert retrieved_key_dict == {}
    creds = ldap.revert()
    assert creds == {}


def test_retrieve_revert_umapi_valid(private_key, modify_umapi_config):
    umapi_config_file = modify_umapi_config(['enterprise', 'priv_key_path'], private_key)
    umapi = UmapiCredentialConfig(umapi_config_file, auto=True)
    # Using the api_key for assertions. The rest can be added in later if deemed necessary
    assert not umapi.parse_secure_key(umapi.get_nested_key(['enterprise', 'api_key']))
    unsecured_api_key = umapi.get_nested_key(['enterprise', 'api_key'])
    umapi.store()
    with open(umapi_config_file, 'r') as f:
        data = yaml.load(f)
        assert umapi.parse_secure_key(data['enterprise']['api_key'])
    retrieved_key_dict = umapi.retrieve()
    assert retrieved_key_dict['enterprise:api_key'] == unsecured_api_key
    umapi.revert()
    with open(umapi_config_file) as f:
        data = yaml.load(f)
        assert data['enterprise']['api_key'] == unsecured_api_key


def test_credman_retrieve_revert_valid(tmp_config_files, private_key, modify_umapi_config):
    (root_config_file, ldap_config_file, _) = tmp_config_files
    umapi_config_file = modify_umapi_config(['enterprise', 'priv_key_path'], private_key)
    credman = CredentialManager(root_config_file, auto=True)
    with open(ldap_config_file) as f:
        data = yaml.load(f)
        plaintext_ldap_password = data['password']
    with open(umapi_config_file) as f:
        data = yaml.load(f)
        plaintext_umapi_api_key = data['enterprise']['api_key']
    credman.store()
    retrieved_creds = credman.retrieve()
    assert retrieved_creds[ldap_config_file]['password'] == plaintext_ldap_password
    assert retrieved_creds[umapi_config_file]['enterprise:api_key'] == plaintext_umapi_api_key
    # make sure the config files are still in secure format
    with open(ldap_config_file) as f:
        data = yaml.load(f)
        assert data['password'] != plaintext_ldap_password
    with open(umapi_config_file) as f:
        data = yaml.load(f)
        assert data['enterprise']['api_key'] != plaintext_umapi_api_key
    credman.revert()
    with open(ldap_config_file) as f:
        data = yaml.load(f)
        assert data['password'] == plaintext_ldap_password
    with open(umapi_config_file) as f:
        data = yaml.load(f)
        assert data['enterprise']['api_key'] == plaintext_umapi_api_key


def test_credman_retrieve_revert_invalid(tmp_config_files, private_key, modify_umapi_config):
    (root_config_file, ldap_config_file, _) = tmp_config_files
    umapi_config_file = modify_umapi_config(['enterprise', 'priv_key_path'], private_key)
    credman = CredentialManager(root_config_file)
    # if credman.store() has not been called first then we can expect the following
    retrieved_creds = credman.retrieve()
    assert retrieved_creds == {}
    creds = credman.revert()
    assert creds == {}


def test_set():
    identifier = 'TestId'
    value = 'TestValue'
    cm = CredentialManager()
    cm.set(identifier, value)


def test_get():
    identifier = 'TestId2'
    value = 'TestValue2'
    cm = CredentialManager()
    # Assume set works
    cm.set(identifier, value)
    assert cm.get(identifier) == value


def test_set_long():
    identifier = 'TestId3'
    cm = CredentialManager()
    value = "".join([str(uuid.uuid4()) for x in range(500)])

    if isinstance(keyring.get_keyring(), keyring.backends.Windows.WinVaultKeyring):
        with pytest.raises(Exception):
            cm.set(identifier, value)
    else:
        cm.set(identifier, value)
        assert cm.get(identifier) == value


def test_get_not_valid():
    # This is an identifier which should not exist in your backed.
    identifier = 'DoesNotExist'
    # keyring.get_password returns None when it cannot find the identifier (such as the case of a typo). No exception
    # is thrown in this case. This case is handled in app.py, which will throw an AssertionException if
    # CredentialManager.get() returns None.
    assert CredentialManager().get(identifier) is None


def test_config_store(tmp_config_files):
    (_, ldap_config_file, _) = tmp_config_files
    ldap = LdapCredentialConfig(ldap_config_file)
    key = Key(['password'])
    assert not ldap.parse_secure_key(ldap.get_nested_key(key.key_path))
    ldap.store()
    with open(ldap_config_file) as f:
        data = yaml.load(f)
        assert ldap.parse_secure_key(data['password'])


def test_config_store_key(tmp_config_files):
    (_, ldap_config_file, _) = tmp_config_files
    ldap = LdapCredentialConfig(ldap_config_file)
    key = Key(['password'])
    assert not ldap.parse_secure_key(ldap.get_nested_key(key.key_path))
    ldap.store_key(key)
    assert ldap.parse_secure_key(ldap.get_nested_key(key.key_path))


def test_config_store_key_none(tmp_config_files):
    (_, ldap_config_file, _) = tmp_config_files
    ldap = LdapCredentialConfig(ldap_config_file)
    key = Key(['password'])
    ldap.set_nested_key(key.key_path, [])
    assert ldap.store_key(key) is None


def test_credman_encrypt_decrypt_key_path(tmp_config_files, private_key, modify_umapi_config):
    (root_config_file, ldap_config_file, _) = tmp_config_files
    umapi_config_file = modify_umapi_config(['enterprise', 'priv_key_path'], private_key)
    credman = CredentialManager(root_config_file, auto=True)
    with open(private_key) as f:
        key_data = f.read()
        assert encryption.is_encryptable(key_data)
    credman.store()
    with open(private_key) as f:
        key_data = f.read()
        assert not encryption.is_encryptable(key_data)
    credman.revert()
    with open(private_key) as f:
        key_data = f.read()
        assert encryption.is_encryptable(key_data)


def test_credman_encrypt_decrypt_key_data(tmp_config_files, private_key, modify_umapi_config):
    (root_config_file, ldap_config_file, _) = tmp_config_files
    umapi_config_file = modify_umapi_config(['enterprise', 'priv_key_path'], None)
    with open(private_key) as f:
        key_data = f.read()
        umapi_config_file = modify_umapi_config(['enterprise', 'priv_key_data'], key_data)
    credman = CredentialManager(root_config_file, auto=True)
    with open(umapi_config_file) as f:
        umapi_dict = yaml.load(f)
        assert encryption.is_encryptable(umapi_dict['enterprise']['priv_key_data'])
    credman.store()
    with open(umapi_config_file) as f:
        umapi_dict = yaml.load(f)
        assert not encryption.is_encryptable(umapi_dict['enterprise']['priv_key_data'])
    credman.revert()
    with open(umapi_config_file) as f:
        umapi_dict = yaml.load(f)
        assert encryption.is_encryptable(umapi_dict['enterprise']['priv_key_data'])
