import multiprocessing

# A day in seconds:
DAY_IN_SECONDS = 60*60*24

QEMU_IMG_SIZE = "12G"
# Define memory (in Mb)
QEMU_MEMORY = 4096
# Define threads to compile packages with
THREADS = multiprocessing.cpu_count()
# URL to latest image text file, defaults to amd64. This is parsed to find latest iso to download
ARCHITECTURE = "amd64"
GENTOO_BASE_ISO_URL = f"https://distfiles.gentoo.org/releases/{ARCHITECTURE}/autobuilds/current-install-{ARCHITECTURE}-minimal/"
GENTOO_BASE_STAGE_OPENRC_URL = f"https://distfiles.gentoo.org/releases/{ARCHITECTURE}/autobuilds/current-stage3-{ARCHITECTURE}-openrc/"
GENTOO_BASE_STAGE_SYSTEMD_URL = f"https://distfiles.gentoo.org/releases/{ARCHITECTURE}/autobuilds/current-stage3-{ARCHITECTURE}-systemd/"
GENTOO_LATEST_ISO_FILE = f"latest-install-{ARCHITECTURE}-minimal.txt"
GENTOO_LATEST_STAGE_OPENRC_FILE = f"latest-stage3-{ARCHITECTURE}-openrc.txt"
GENTOO_LATEST_STAGE_SYSTEMD_FILE = f"latest-stage3-{ARCHITECTURE}-systemd.txt"
GENTOO_PORTAGE_FILE = "http://distfiles.gentoo.org/snapshots/portage-latest.tar.xz"  # No architecture, no txt files to determine latest.

GENTOO_MOUNT = "/mnt/gentoo"
GENTOO_IMG_NAME = "gentoo.img"

GENTOO_FILE_HASH_RE = r"^Hash\: ([\w]*)$"
GENTOO_FILE_ISO_RE = r"^(install-[\w\-_\.]*.iso) ([\d]*)"
GENTOO_FILE_ISO_HASH_RE = r"^([\w]*)  (install-[\w\-_\.]*.iso)$"
GENTOO_FILE_STAGE3_RE = r"^(stage3-[\w\-_\.]*.tar.*) ([\d]*)"
GENTOO_FILE_STAGE3_HASH_RE = r"^([\w]*)  (stage3-[\w\-_\.]*.tar.*)$"

# Dict of "filename": ["package-name license-accepted"]
GENTOO_ACCEPT_LICENSE = {
    'kernel': ["sys-kernel/linux-firmware linux-fw-redistributable"]
}

# Currently we only deal with rsync uri's. Will need new feature branch to merge other methods
GENTOO_SYNC_URI = "rsync://192.168.254.20/gentoo-portage"
# Allow overriding this file if need be
GENTOO_REPO_FILE = f"""[DEFAULT]
main-repo = gentoo

[gentoo]
location = /var/db/repos/gentoo
sync-type = rsync
sync-uri = {GENTOO_SYNC_URI}
auto-sync = yes
sync-rsync-verify-jobs = 1
sync-rsync-verify-metamanifest = yes
sync-rsync-verify-max-age = 24
sync-openpgp-key-path = /usr/share/openpgp-keys/gentoo-release.asc
sync-openpgp-keyserver = hkps://keys.gentoo.org
sync-openpgp-key-refresh-retry-count = 40
sync-openpgp-key-refresh-retry-overall-timeout = 1200
sync-openpgp-key-refresh-retry-delay-exp-base = 2
sync-openpgp-key-refresh-retry-delay-max = 60
sync-openpgp-key-refresh-retry-delay-mult = 4
sync-webrsync-verify-signature = yes
"""

# Default list of packages to install. Can be overridden, but probably shouldn't
BASE_PACKAGES = [
    "acpid",
    "dmidecode",
    "syslog-ng",
    "cronie",
    "dhcpcd",
    "mlocate",
    "xfsprogs",
    "dosfstools",
    "grub",
    "sudo",
    "postfix",
    "cloud-init",
    "app-editors/vim",
    "parted",
    "portage-utils",
    "bash-completion",
    "gentoo-bashcomp",
    "eix",
    "tmux",
    "app-misc/screen",
    "dev-vcs/git",
    "net-misc/curl",
    "usbutils",
    "pciutils",
    "logrotate",
    "gptfdisk",
    "sys-block/gpart",
    "net-misc/ntp",
    "net-fs/nfs-utils",
    "sys-block/open-iscsi"
]

ONESHOT_UPDATE_PKGS = [
    "portage"
]

EMERGE_SINGLE_PKGS = [
    "app-portage/eix",
    "dev-util/cmake"
]

EMERGE_KEEP_GOING_PKGS = [
    "openssh"
]

KERNEL_PACKAGES = [
    "sys-kernel/genkernel",
    "gentoo-sources",
    "gentoolkit",
    "linux-firmware"
]

BOOTLOADER_PACKAGES = [
    "grub:2"
]

# Services to add to the 'default' in rc-update or rely on default level using systemctl enable
DEFAULT_SERVICES = []

ADDITIONAL_PACKAGES = [
    # app-editors/vim
]

# TODO: Merge this into configuration
# [ ] Use this file as a template to generate a conf file, esp. when one is not specified.
# [ ] Use that configuration file to retrieve values or have user specify another modified one.
CLOUD_CFG = {
    "portage": None,  # use first portage-*.tar.bz2
    "stage3": None,  # use first stage3-.tar.xz file
    "disk": "/dev/vda",
    "partition": 1,
    "makeopts-j": THREADS,  # -jX during compile
    "jobcount": THREADS,
    "packages": []  # Additional packages
}

CLOUD_MODULES = [
    "iscsi_tcp"
]
