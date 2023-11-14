import os

# Define memory (in Mb)
QEMU_MEMORY = 512
# Define threads to compile packages with
THREADS = 4
# URL to latest image text file, defaults to amd64. This is parsed to find latest iso to download
ARCHITECTURE = "amd64"
GENTOO_BASE_URL = f"https://distfiles.gentoo.org/releases/{ARCHITECTURE}/autobuilds/current-install-{ARCHITECTURE}-minimal/"
GENTOO_LATEST_FILE = f"latest-install-{ARCHITECTURE}-minimal.txt"
GENTOO_FILE_HASH_RE = r"^Hash\: ([\w]*)$"
GENTOO_FILE_ISO_RE = r"^(install-[\w\-_\.]*.iso) ([\d]*)"

TEMPORARY_DIRECTORY = os.path.join(os.sep, "tmp")

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
    "gentoo-sources",
    "linux-firmware",
    "parted",
    "portage-utils",
    "gentoolkit",
    "bash-completion",
    "gentoo-bashcom",
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
    "sys-block/open-iscsi",
    "sys-kernel/genkernel"
]

ADDITIONAL_PACKAGES = [
    # app-editors/vim
]

