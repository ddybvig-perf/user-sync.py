---
layout: default
lang: en
nav_link: Additional Tools
nav_level: 2
nav_order: 80
---


# Additional Tools

---

[Previous Section](deployment_best_practices.md)

---

#### Documentation goes here

###Credential Manager

The user can manage credentials from the command line using the 
```credentials``` command with any of the
following subcommands.

| Subcommand | Description |
|------------------------------|------------------|
| `store` | Replaces the plaintext values of sensitive credentials in configuration files with secure keys. |
| `retrieve` | Retrieves all stored credentials for the User Sync Tool from your OS secure storage and prints them to the console. |
| `revert` | Retrieves all stored credentials for the User Sync Tool from OS Secure storage, then replaces secure keys in the configuration files with the retrieved plaintext values. |
| `get` | Takes one parameter `--identifier [identifier]` either as a command line option or from a user prompt. Keyring then retrieves the corresponding credential from the backend. |
| `set` | Takes two parameters, `--identifier [identifier]` and `--value [value]` either as command line options or from user prompts. Keyring then creates a new credential in the backend for the specified identifier. The username will be "user_sync." |

**Sample Output (Windows)**

Successful output from ```set``` subcommand:

```
(venv) C:\Program Files\Adobe\Adobe User Sync Tool>python user-sync.pex credentials set
Enter identifier: ldap_password
Enter value:
Using backend: Windows WinVaultKeyring
Setting 'ldap_password' in keyring
Using keyring 'Windows WinVaultKeyring' to set 'ldap_password'
Validating...
Using keyring 'Windows WinVaultKeyring' to retrieve 'ldap_password'
Credentials stored successfully for: ldap_password
```
The identifier and value (password) can also be set as parameters:

```
(venv) C:\Program Files\Adobe\Adobe User Sync Tool>python user-sync.pex credentials set --identifier ldap_password --value password
Using backend: Windows WinVaultKeyring
Setting 'ldap_password' in keyring
Using keyring 'Windows WinVaultKeyring' to set 'ldap_password'
Validating...
Using keyring 'Windows WinVaultKeyring' to retrieve 'ldap_password'
Credentials stored successfully for: ldap_password
```

Successful output from ```get``` subcommand. Note that the 
output echoes the requested identifier and password on the last line:

```
(venv) C:\Program Files\Adobe\Adobe User Sync Tool>python user-sync.pex credentials get
Enter identifier: ldap_password
Using backend: Windows WinVaultKeyring
Getting 'ldap_password' from keyring
Using keyring 'Windows WinVaultKeyring' to retrieve 'ldap_password'
ldap_password: password
```

Similar to ```set```, ```get``` can also be run without the prompt by
passing in the identifier as a parameter.

Successful output from ```store``` subcommand. 

```
(venv) C:\Program Files\Adobe\Adobe User Sync Tool>python user-sync.pex credentials store
             <output from store goes here>
```

Example of what the config files look like after running ```store```.

```config file snippet showing the secure key```

Retrieve stuff goes here:

```blah blah blah```

Revert stuff goes here:

```blah blah blah```



[Previous Section](deployment_best_practices.md)