#!/bin/bash

# Add user sistemas and configure it
if id "sistemas" &>/dev/null; then
    echo 'User sistemas exists'
else
	if id "1000" &>/dev/null; then
		echo 'Id 1000 exists'
		useradd -m -d /home/sistemas -s /bin/bash -c "Sistemas" -u 1010 sistemas
	else
		useradd -m -d /home/sistemas -s /bin/bash -c "Sistemas" -u 1000 sistemas
	fi
fi

mkdir -p /home/sistemas/.ssh
chmod u=rwx,g-rwx,o-rwx /home/sistemas/.ssh
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCqWuXWArUbEkifG/ooe2YdkViea8Aa3cEHl1iWpsevo1Rqx8qr+2+AQoXT2pX/VrICSBgwvMT2HkZ+32pECcAkhJBZUmS458wN+griqi2TbTpxq1OqdXfRczEDM8d4YEHPDEg9mDcrRkRpFghY4HtE8tcnLQKlbyuHLco6UG7fJmp5iV+2KBwIyVkQHDRDojWTzTCbm/m8mN6qLLb2KQtq+kFaFZntWjKpDHYkK/CpU0zOj9vMg4wxmNvZIa3ubAYl8otxAiqi/0IGOTGk6bfkE0LD7Pw4zVpi11uz38zaf13+rN0xvTH4S7YLKD9XJ/VhqnYNmd5rxQFf+OXoNYfsFIwXuTAqY6/SNLXbjG3zQdrZbAhTNsEGOfsvCA7tIxZaUuSld5vkJgIonwOzV346CWF/K615aRLeZBPQ4MW36FLsgPQS7qFwSdZFME8A5wgxxf6UADoz6XgSEA/IiyAHgk7peZEc0Yn2Fdl7NOWUsiwAltWb+72cwyH8qkFy84Uj+eKK0Z6QvXvPBlY8feoD+17XGqHBL5/p+2JPRuSGT2p8ol66YopzwydQKtfcgtA+ZykKqriRsEevOuIkKEv58VhRK01O9/lnhVxzSGPP6Vuq4tLRRE/3gaPi8IfcJBmHCLN2glQ9Ousc0PCVxHPQ1/0rIYOYE50vB9Mp2vwLzQ== sistemas' > /home/sistemas/.ssh/authorized_keys
chmod 700 /home/sistemas/.ssh
chmod 600 /home/sistemas/.ssh/authorized_keys
chown -R sistemas:sistemas /home/sistemas/.ssh

# Disable password to root sistemas
sed -i '/^%sudo.*/a sistemas    ALL=NOPASSWD: ALL' /etc/sudoers

# SSH
apt-get -y install ssh
echo "#	: sshd_config,v 1.103 2018/04/09 20:41:22 tj Exp $

# This is the sshd server system-wide configuration file.  See
# sshd_config(5) for more information.

# This sshd was compiled with PATH=/usr/bin:/bin:/usr/sbin:/sbin

# The strategy used for options in the default sshd_config shipped with
# OpenSSH is to specify options with their default value where
# possible, but leave them commented.  Uncommented options override the
# default value.

# Se cambia el puerto
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
#SyslogFacility AUTH
#LogLevel INFO

# Authentication:

LoginGraceTime 60
# Se impide login como root
PermitRootLogin no
#StrictModes yes
MaxAuthTries 3
MaxSessions 4

# Se activa uso de llaves
PubkeyAuthentication yes

# Expect .ssh/authorized_keys2 to be disregarded by default in future.
#AuthorizedKeysFile	.ssh/authorized_keys .ssh/authorized_keys2

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
# Se deshabilita el uso de password
PasswordAuthentication no
#PermitEmptyPasswords no

# Solo se permite acceso al usuario sistemas
AllowUsers sistemas

# Change to yes to enable challenge-response passwords (beware issues with
# some PAM modules and threads)
ChallengeResponseAuthentication no

# Kerberos options
#KerberosAuthentication no
#KerberosOrLocalPasswd yes
#KerberosTicketCleanup yes
#KerberosGetAFSToken no

# GSSAPI options
#GSSAPIAuthentication no
#GSSAPICleanupCredentials yes
#GSSAPIStrictAcceptorCheck yes
#GSSAPIKeyExchange no


UsePAM yes

#AllowAgentForwarding yes
AllowTcpForwarding no
#GatewayPorts no
X11Forwarding yes
#X11DisplayOffset 10
#X11UseLocalhost yes
#PermitTTY yes
PrintMotd no
#PrintLastLog yes
#TCPKeepAlive yes
#PermitUserEnvironment no
#Compression delayed
ClientAliveInterval 60
ClientAliveCountMax 3
#UseDNS no
#PidFile /var/run/sshd.pid
MaxStartups 10:30:60
#PermitTunnel no
#ChrootDirectory none
#VersionAddendum none

# no default banner path
Banner /etc/issue.net

# Allow client to pass locale environment variables
AcceptEnv LANG LC_*

# override default of no subsystems
Subsystem	sftp	/usr/lib/openssh/sftp-server

# Example of overriding settings on a per-user basis
#Match User anoncvs
#	X11Forwarding no
#	AllowTcpForwarding no
#	PermitTTY no
#	ForceCommand cvs server" > /etc/ssh/sshd_config
systemctl enable ssh && systemctl restart ssh