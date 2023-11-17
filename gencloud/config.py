import multiprocessing

# A day in seconds:
DAY_IN_SECONDS = 60*60*24

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

CLOUD_CFG = {
    "portage": None,  # use first portage-*.tar.bz2
    "stage3": None,  # use first stage3-.tar.xz file
    "disk": "/dev/vda",
    "partition": 1,
    "makeopts-j": THREADS,  # -jX during compile
    "jobcount": 4,
    "packages": []  # Additional packages
}

