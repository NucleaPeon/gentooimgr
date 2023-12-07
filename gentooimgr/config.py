import os
import json
import gentooimgr.configs
import multiprocessing

# A day in seconds:
DAY_IN_SECONDS = 60*60*24
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
GENTOO_IMG_NAME = "gentoo.qcow2"

GENTOO_FILE_HASH_RE = r"^Hash\: ([\w]*)$"
GENTOO_FILE_ISO_RE = r"^(install-[\w\-_\.]*.iso) ([\d]*)"
GENTOO_FILE_ISO_HASH_RE = r"^([\w]*)  (install-[\w\-_\.]*.iso)$"
GENTOO_FILE_STAGE3_RE = r"^(stage3-[\w\-_\.]*.tar.*) ([\d]*)"
GENTOO_FILE_STAGE3_HASH_RE = r"^([\w]*)  (stage3-[\w\-_\.]*.tar.*)$"
# TODO: Repo regex to replace attributes, use function to do so as find key will change.

def replace_repos_conf(key, value):
    pass

# CLOUD_MODULES = [
#     "iscsi_tcp"
# ]

def load_config(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.loads(f.read())
    return {}

def load_default_config(config_name):
    """This is called when a --config option is set. --kernel options update the resulting config, whether
    it be 'base' or other.
    If user is supplying their own configuration, this is not called.
    """
    name, ext = os.path.splitext(config_name)
    if not name in gentooimgr.configs.KNOWN_CONFIGS:
        return {}

    with open(os.path.join(gentooimgr.configs.CONFIG_DIR, config_name), 'r') as f:
        return json.loads(f.read())

