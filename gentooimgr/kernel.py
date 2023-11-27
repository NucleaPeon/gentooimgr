import os
import sys
import re
import shutil
import datetime
from subprocess import Popen, PIPE
import time

VIRTIO_CONF = """
CONFIG_BLOCK=y
CONFIG_BLK_DEV=y
CONFIG_DEVTMPFS=y
CONFIG_VIRTIO_MENU=y
CONFIG_VIRTIO_BLK=y
"""

SPEC = dict(
    virtio=VIRTIO_CONF
)

def kernel_confs(specs=[]):
    """Returns a list of config options (CONFIG_OPT=y/n/m) required for the spec(s) given

    If --virtio is given, the kernel is configured to boot in a qemu environment. You would
    see the following config options set for the hard drive:

        CONFIG_BLOCK=y
        CONFIG_BLK_DEV=y
        CONFIG_DEVTMPFS=y
        CONFIG_VIRTIO_MENU=y
        CONFIG_VIRTIO_BLK=y
    """

    retval = []
    for s in specs:
        retval.extend(SPEC.get(s, "").split("\n"))

    return [ rv for rv in retval if rv ]

def kernel_conf_apply(kernel_dir='/usr/src/linux',
                      spectypes=[]):
    """Applies the given spec list (one CONFIG_ per line)
        - Performs a check; if an exact match up to the = isn't found, add it.
        - If an exact key match is found, check if it's exact. If not, run sed to change the value.
        - Write out a temporary kernel config file before doing a backup and write (use unix timestamp for backups.)
    """
    if not spectypes:
        sys.stderr.write("")
        return

    configs = kernel_confs(specs=spectypes)

    written_specs = []
    tmpfile = "/tmp/.config.tmp"
    if os.path.exists(tmpfile):
        os.remove(tmpfile)
    kernelconfig = os.path.join(kernel_dir, '.config')
    timestamp = time.mktime(datetime.datetime.now().timetuple())
    shutil.copy(kernelconfig, kernelconfig+str(timestamp))

    with open(tmpfile, 'w') as newconf:
        with open(kernelconfig, 'r') as conf:
            configtext = conf.read()
            # One possible caveat is that all specified configs end up at the top of the file.
            for c in configs:
                spec, val = c.split("=")
                newconf.write(f"{spec}={val}\n")
                written_specs.append(f"{spec}=")  # without value, but include equals

            for c in configtext.split("\n"):
                # If the conf we are about to write matches the new one spec'd and written, skip it
                if list(filter(lambda x: c.startswith(x), written_specs)):
                    continue  # Already exists

                newconf.write(f"{c}\n")

    shutil.copy(tmpfile, kernelconfig)
    os.remove(tmpfile)

def kernel_save_config():
    """Saves the current .config file"""
    proc = Popen(["make", "savedefconfig"])
    proc.communicate()

GRUB_CFG = """
# Copyright 1999-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/sys-boot/grub/files/grub.default-3,v 1.5 2015/03/25 01:58:00 floppym Exp $
#
# To populate all changes in this file you need to regenerate your
# grub configuration file afterwards:
#     'grub2-mkconfig -o /boot/grub/grub.cfg'
#
# See the grub info page for documentation on possible variables and
# their associated values.

GRUB_DISTRIBUTOR="Gentoo"

# Default menu entry
#GRUB_DEFAULT=0

# Boot the default entry this many seconds after the menu is displayed
#GRUB_TIMEOUT=5
#GRUB_TIMEOUT_STYLE=menu

# Append parameters to the linux kernel command line
# openrc only spits to the last console=tty
GRUB_CMDLINE_LINUX="net.ifnames=0 vga=791 console=tty0 console=ttyS0,115200"
#
# Examples:
#
# Boot with network interface renaming disabled
# GRUB_CMDLINE_LINUX="net.ifnames=0"
#
# Boot with systemd instead of sysvinit (openrc)
# GRUB_CMDLINE_LINUX="init=/usr/lib/systemd/systemd"

# Append parameters to the linux kernel command line for non-recovery entries
#GRUB_CMDLINE_LINUX_DEFAULT=""

# Uncomment to disable graphical terminal (grub-pc only)
GRUB_TERMINAL="serial console"
GRUB_SERIAL_COMMAND="serial --speed=115200"
#GRUB_SERIAL_COMMAND="serial --speed=115200 --unit=0 --word=8 --parity=no --stop=1"

# The resolution used on graphical terminal.
# Note that you can use only modes which your graphic card supports via VBE.
# You can see them in real GRUB with the command `vbeinfo'.
#GRUB_GFXMODE=640x480

# Set to 'text' to force the Linux kernel to boot in normal text
# mode, 'keep' to preserve the graphics mode set using
# 'GRUB_GFXMODE', 'WIDTHxHEIGHT'['xDEPTH'] to set a particular
# graphics mode, or a sequence of these separated by commas or
# semicolons to try several modes in sequence.
#GRUB_GFXPAYLOAD_LINUX=

# Path to theme spec txt file.
# The starfield is by default provided with use truetype.
# NOTE: when enabling custom theme, ensure you have required font/etc.
#GRUB_THEME="/boot/grub/themes/starfield/theme.txt"

# Background image used on graphical terminal.
# Can be in various bitmap formats.
#GRUB_BACKGROUND="/boot/grub/mybackground.png"

# Uncomment if you don't want GRUB to pass "root=UUID=xxx" parameter to kernel
#GRUB_DISABLE_LINUX_UUID=true

# Uncomment to disable generation of recovery mode menu entries
#GRUB_DISABLE_RECOVERY=true

# Uncomment to disable generation of the submenu and put all choices on
# the top-level menu.
# Besides the visual affect of no sub menu, this makes navigation of the
# menu easier for a user who can't see the screen.
GRUB_DISABLE_SUBMENU=y

# Uncomment to play a tone when the main menu is displayed.
# This is useful, for example, to allow users who can't see the screen
# to know when they can make a choice on the menu.
#GRUB_INIT_TUNE="60 800 1"

"""
