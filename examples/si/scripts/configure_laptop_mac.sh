#/bin/bash

# CONFIGURE ZEROTIER
curl --output ZeroTier.pkg https://download.zerotier.com/dist/ZeroTier%20One.pkg
installer -pkg ZeroTier.pkg -target /
zerotier-cli join c6714bd6db5847b2

# CREATE USER sistemasstratio
dscl . -create /Users/sistemas
dscl . -create /Users/sistemas UserShell /bin/bash
dscl . -create /Users/sistemas UniqueID 1005
dscl . -create /Users/sistemas PrimaryGroupID 20
dscl . -create /Users/sistemas NFSHomeDirectory /Users/sistemas
dscl . -append /Groups/admin GroupMembership sistemas
mkdir -p /Users/sistemas/.ssh
chmod u=rwx,g-rwx,o-rwx /Users/sistemas/.ssh
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCqWuXWArUbEkifG/ooe2YdkViea8Aa3cEHl1iWpsevo1Rqx8qr+2+AQoXT2pX/VrICSBgwvMT2HkZ+32pECcAkhJBZUmS458wN+griqi2TbTpxq1OqdXfRczEDM8d4YEHPDEg9mDcrRkRpFghY4HtE8tcnLQKlbyuHLco6UG7fJmp5iV+2KBwIyVkQHDRDojWTzTCbm/m8mN6qLLb2KQtq+kFaFZntWjKpDHYkK/CpU0zOj9vMg4wxmNvZIa3ubAYl8otxAiqi/0IGOTGk6bfkE0LD7Pw4zVpi11uz38zaf13+rN0xvTH4S7YLKD9XJ/VhqnYNmd5rxQFf+OXoNYfsFIwXuTAqY6/SNLXbjG3zQdrZbAhTNsEGOfsvCA7tIxZaUuSld5vkJgIonwOzV346CWF/K615aRLeZBPQ4MW36FLsgPQS7qFwSdZFME8A5wgxxf6UADoz6XgSEA/IiyAHgk7peZEc0Yn2Fdl7NOWUsiwAltWb+72cwyH8qkFy84Uj+eKK0Z6QvXvPBlY8feoD+17XGqHBL5/p+2JPRuSGT2p8ol66YopzwydQKtfcgtA+ZykKqriRsEevOuIkKEv58VhRK01O9/lnhVxzSGPP6Vuq4tLRRE/3gaPi8IfcJBmHCLN2glQ9Ousc0PCVxHPQ1/0rIYOYE50vB9Mp2vwLzQ== sistemas' > /Users/sistemas/.ssh/authorized_keys
chmod 700 /Users/sistemas/.ssh
chmod 600 /Users/sistemas/.ssh/authorized_keys
chown -R sistemas /Users/sistemas/.ssh

linevisudo="sistemas    ALL=NOPASSWD: ALL"
grep -q 'sistemas' /etc/sudoers || echo $linevisudo >> /etc/sudoers 

# CONFIGURE SSH
# Connect to mac using  parameter -o MACs=hmac-sha2-256
systemsetup -f -setremotelogin on

echo "#	: sshd_config,v 1.103 2018/04/09 20:41:22 tj Exp $

# This is the sshd server system-wide configuration file.  See
# sshd_config(5) for more information.

# This sshd was compiled with PATH=/usr/bin:/bin:/usr/sbin:/sbin

# The strategy used for options in the default sshd_config shipped with
# OpenSSH is to specify options with their default value where
# possible, but leave them commented.  Uncommented options override the
# default value.

# This Include directive is not part of the default sshd_config shipped with
# OpenSSH. Options set in the included configuration files generally override
# those that follow.  The defaults only apply to options that have not been
# explicitly set.  Options that appear multiple times keep the first value set,
# unless they are a multivalue option such as HostKey.
Include /etc/ssh/sshd_config.d/*

Port 2269
#AddressFamily any
#ListenAddress 0.0.0.0
#ListenAddress ::

#HostKey /etc/ssh/ssh_host_rsa_key
#HostKey /etc/ssh/ssh_host_ecdsa_key
#HostKey /etc/ssh/ssh_host_ed25519_key

# Ciphers and keying
#RekeyLimit default none

# Logging
SyslogFacility AUTH
LogLevel INFO

# Authentication:

#LoginGraceTime 2m
PermitRootLogin no
#StrictModes yes
#MaxAuthTries 6
#MaxSessions 10

PubkeyAuthentication yes

# The default is to check both .ssh/authorized_keys and .ssh/authorized_keys2
# but this is overridden so installations will only check .ssh/authorized_keys
AuthorizedKeysFile	.ssh/authorized_keys

#AuthorizedPrincipalsFile none

#AuthorizedKeysCommand none
#AuthorizedKeysCommandUser nobody

# For this to work you will also need host keys in /etc/ssh/ssh_known_hosts
#HostbasedAuthentication no
# Change to yes if you don't trust ~/.ssh/known_hosts for
# HostbasedAuthentication
#IgnoreUserKnownHosts no
# Don't read the user's ~/.rhosts and ~/.shosts files
#IgnoreRhosts yes

# To disable tunneled clear text passwords, change to no here!
PasswordAuthentication no
#PermitEmptyPasswords no

# Allow only user sistemas
AllowUsers sistemas

# Change to no to disable s/key passwords
ChallengeResponseAuthentication no

# Kerberos options
#KerberosAuthentication no
#KerberosOrLocalPasswd yes
#KerberosTicketCleanup yes
#KerberosGetAFSToken no

# GSSAPI options
#GSSAPIAuthentication no
#GSSAPICleanupCredentials yes

# Set this to 'yes' to enable PAM authentication, account processing,
# and session processing. If this is enabled, PAM authentication will
# be allowed through the ChallengeResponseAuthentication and
# PasswordAuthentication.  Depending on your PAM configuration,
# PAM authentication via ChallengeResponseAuthentication may bypass
# the setting of PermitRootLogin without-password.
# If you just want the PAM account and session checks to run without
# PAM authentication, then enable this but set PasswordAuthentication
# and ChallengeResponseAuthentication to 'no'.
UsePAM no

#AllowAgentForwarding yes
#AllowTcpForwarding yes
#GatewayPorts no
#X11Forwarding no
#X11DisplayOffset 10
#X11UseLocalhost yes
#PermitTTY yes
#PrintMotd yes
#PrintLastLog yes
#TCPKeepAlive yes
#PermitUserEnvironment no
#Compression delayed
#ClientAliveInterval 0
#ClientAliveCountMax 3
#UseDNS no
#PidFile /var/run/sshd.pid
#MaxStartups 10:30:100
#PermitTunnel no
#ChrootDirectory none
#VersionAddendum none

# no default banner path
#Banner none

# override default of no subsystems
#Subsystem	sftp	/usr/libexec/sftp-server

# Example of overriding settings on a per-user basis
#Match User anoncvs
#	X11Forwarding no
#	AllowTcpForwarding no
#	PermitTTY no
#	ForceCommand cvs server" > /etc/ssh/sshd_config

sed -i '' 's/ 22\// 2269\//g' /etc/services
launchctl unload /System/Library/LaunchDaemons/ssh.plist
launchctl load -w /System/Library/LaunchDaemons/ssh.plist
systemsetup -f -setremotelogin on

## INSTALL PYTHON3-DEV

NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
export PATH="/usr/local/opt/python/libexec/bin:$PATH"
brew install python3
