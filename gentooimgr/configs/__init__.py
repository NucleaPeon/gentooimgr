import os

CONFIG_DIR = os.path.abspath(os.path.dirname(__file__))

__all__ = ["CONFIG_DIR", "CLOUD_YAML", "HOST_TMPL", "HOSTNAME", "KNOWN_CONFIGS"]

# List of configurations that end in '.json' within the configs/ directory
KNOWN_CONFIGS = [
    "base",
    "cloud",
    "qemu",
    "ppcbase",
    "powerpc32",
    "powerpc64",
    "arm"
]

# Currently we handle the writing of additional files by having data defined here and checking options.
# this isn't ideal. TODO: Make this better.
CLOUD_YAML = """
# The top level settings are used as module
# and system configuration.

# A set of users which may be applied and/or used by various modules
# when a 'default' entry is found it will reference the 'default_user'
# from the distro configuration specified below
users:
   - default

# If this is set, 'root' will not be able to ssh in and they
# will get a message to login instead as the above $user (ubuntu)
disable_root: true
ssh_pwauth:   false

# This will cause the set+update hostname module to not operate (if true)
preserve_hostname: false

# this may be helpful in certain scenarios
# resize_rootfs_tmp: /dev

syslog_fix_perms: root:root

ssh_deletekeys: false
ssh_genkeytypes: [rsa, dsa]

# This can be 'template'
# which would look for /etc/cloud/templates/hosts.gentoo.tmpl
# or 'localhost'
# or False / commented out to disable altogether
manage_etc_hosts: template

# Example datasource config
# datasource:
#    Ec2:
#      metadata_urls: [ 'blah.com' ]
#      timeout: 5 # (defaults to 50 seconds)
#      max_wait: 10 # (defaults to 120 seconds)

# The modules that run in the 'init' stage
cloud_init_modules:
 - seed_random
 - bootcmd
 - write-files
 - growpart
 - resizefs
 - set_hostname
 - update_hostname
 - update_etc_hosts
 - ca-certs
 - users-groups
 - ssh

# The modules that run in the 'config' stage
cloud_config_modules:
# Emit the cloud config ready event
# this can be used by upstart jobs for 'start on cloud-config'.
 - disk_setup
 - mounts
 - ssh-import-id
 - set-passwords
 - package-update-upgrade-install
 - timezone
 - puppet
 - chef
 - salt-minion
 - mcollective
 - disable-ec2-metadata
 - runcmd

# The modules that run in the 'final' stage
cloud_final_modules:
 - scripts-vendor
 - scripts-per-once
 - scripts-per-boot
 - scripts-per-instance
 - scripts-user
 - ssh-authkey-fingerprints
 - keys-to-console
 - phone-home
 - final-message
 - power-state-change

# System and/or distro specific settings
# (not accessible to handlers/transforms)
system_info:
   # This will affect which distro class gets used
   distro: gentoo
   # Default user name + that default users groups (if added/used)
   default_user:
     name: gentoo
     lock_passwd: True
     gecos: Gentoo
     groups: [users, wheel]
     primary_group: users
     no-user-group: true
     sudo: ["ALL=(ALL) NOPASSWD:ALL"]
     shell: /bin/bash
   # Other config here will be given to the distro class and/or path classes
   paths:
      cloud_dir: /var/lib/cloud/
      templates_dir: /etc/cloud/templates/
"""

HOST_TMPL = """
## template:jinja
{#
This file /etc/cloud/templates/hosts.gentoo.tmpl is only utilized
if enabled in cloud-config.  Specifically, in order to enable it
you need to add the following to config:
  manage_etc_hosts: template
-#}
# Your system has configured 'manage_etc_hosts' as 'template'.
# As a result, if you wish for changes to this file to persist
# then you will need to either
# a.) make changes to the master file in /etc/cloud/templates/hosts.gentoo.tmpl
# b.) change or remove the value of 'manage_etc_hosts' in
#     /etc/cloud/cloud.cfg or cloud-config from user-data
#
# The following lines are desirable for IPv4 capable hosts
127.0.0.1 {{fqdn}} {{hostname}}
127.0.0.1 localhost.localdomain localhost
127.0.0.1 localhost4.localdomain4 localhost4

# The following lines are desirable for IPv6 capable hosts
::1 {{fqdn}} {{hostname}}
::1 localhost.localdomain localhost
::1 localhost6.localdomain6 localhost6
"""

HOSTNAME = """
# Set to the hostname of this machine
if [ -f /etc/hostname ];then
    hostname=$(cat /etc/hostname 2> /dev/null | cut -d"." -f1 2> /dev/null)
else
    hostname="localhost"
fi
"""

