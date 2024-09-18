# /bin/python3

from ldap3 import Server, Connection, ALL, SIMPLE, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, MODIFY_ADD
from ldap3.core.exceptions import LDAPCursorError

LDAP_ENDPOINT = 'vpre.labs.stratio.com:389'
LDAP_USERNAME = ''
LDAP_PASSWORD = ''


def refactor_ldap():
    server = Server(LDAP_ENDPOINT.split(':')[0],
                    port=int(LDAP_ENDPOINT.split(':')[1]),
                    get_info=ALL)
    conn = Connection(server,
                      user=LDAP_USERNAME,
                      password=LDAP_PASSWORD,
                      authentication=SIMPLE,
                      auto_bind="NO_TLS")

    conn.search('ou=External,ou=Users,dc=stratio,dc=com',
                '(objectclass=person)',
                attributes=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES])

    for entry in conn.entries:
        print(entry.entry_dn)

        print("Adding givenName to " + entry.entry_dn)
        conn.modify(entry.entry_dn,
                    {'givenName': [(MODIFY_ADD, [str(entry.cn).split('-')[0]])]})

        print("Adding shadowFlag to " + entry.entry_dn)
        conn.modify(entry.entry_dn,
                    {'shadowFlag': [(MODIFY_ADD, [str(entry.shadowExpire)])]})


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    refactor_ldap()

