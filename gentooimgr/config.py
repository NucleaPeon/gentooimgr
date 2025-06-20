import os
import json
import sys
import argparse
import multiprocessing
import gentooimgr.configs
from gentooimgr.logging import LOG

# A day in seconds:
DAY_IN_SECONDS = 60*60*24

DAYS = 7  # To check for new images

# Define threads to compile packages with
THREADS = multiprocessing.cpu_count()

def config(architecture="amd64"):
    ns = argparse.Namespace(**dict(
        ARCHITECTURE=architecture,
        GENTOO_BASE_ISO_URL = f"https://distfiles.gentoo.org/releases/{architecture}/autobuilds/current-install-{architecture}-minimal/",
        GENTOO_BASE_STAGE_OPENRC_URL = f"https://distfiles.gentoo.org/releases/{architecture}/autobuilds/current-stage3-{architecture}-openrc/",
        GENTOO_BASE_STAGE_SYSTEMD_URL = f"https://distfiles.gentoo.org/releases/{architecture}/autobuilds/current-stage3-{architecture}-systemd/",
        GENTOO_LATEST_ISO_FILE = f"latest-install-{architecture}-minimal.txt",
        GENTOO_LATEST_STAGE_OPENRC_FILE = f"latest-stage3-{architecture}-openrc.txt",
        GENTOO_LATEST_STAGE_SYSTEMD_FILE = f"latest-stage3-{architecture}-systemd.txt",
        GENTOO_PORTAGE_FILE = "http://distfiles.gentoo.org/snapshots/portage-latest.tar.xz",  # No architecture, no txt files to determine latest.
        GENTOO_CMD = "qemu-system-x86_64" if architecture == "amd64" else f"qemu-system-{architecture}",
        GENTOO_IMG_NAME = f"gentoo-{architecture}.qcow2"
    ))
    return ns

# URL to latest image text file, defaults to amd64. This is parsed to find latest iso to download
# GENTOO_BASE_ISO_URL = f"https://distfiles.gentoo.org/releases/{architecture}/autobuilds/current-install-{architecture}-minimal/"
# GENTOO_BASE_STAGE_OPENRC_URL = f"https://distfiles.gentoo.org/releases/{architecture}/autobuilds/current-stage3-{architecture}-openrc/"
# GENTOO_BASE_STAGE_SYSTEMD_URL = f"https://distfiles.gentoo.org/releases/{architecture}/autobuilds/current-stage3-{architecture}-systemd/"
# GENTOO_LATEST_ISO_FILE = f"latest-install-{architecture}-minimal.txt"
# GENTOO_LATEST_STAGE_OPENRC_FILE = f"latest-stage3-{architecture}-openrc.txt"
# GENTOO_LATEST_STAGE_SYSTEMD_FILE = f"latest-stage3-{architecture}-systemd.txt"
# GENTOO_PORTAGE_FILE = "http://distfiles.gentoo.org/snapshots/portage-latest.tar.xz"  # No architecture, no txt files to determine latest.

DEFAULT_QEMU_CMD = "qemu-system-x86_64"
DEFAULT_GENTOO_EFI_FIRMWARE_PATH = "/usr/share/edk2-ovmf/OVMF_CODE.fd"
GENTOO_MOUNT = "/mnt/gentoo"

GENTOO_FILE_HASH_RE = r"^Hash\: ([\w]*)$"
GENTOO_FILE_ISO_RE = r"^(install-[\w\-_\.]*.iso) ([\d]*)"
GENTOO_FILE_ISO_HASH_RE = r"^([\w]*)  (install-[\w\-_\.]*.iso)$"
GENTOO_FILE_STAGE3_RE = r"^(stage3-[\w\-_\.]*.tar.*) ([\d]*)"
GENTOO_FILE_STAGE3_HASH_RE = r"^([\w]*)  (stage3-[\w\-_\.]*.tar.*)$"
# TODO: Repo regex to replace attributes, use function to do so as find key will change.

def replace_repos_conf(key, value):
    pass

CLOUD_MODULES = [
    "iscsi_tcp"
]

def load_config(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            LOG.info(path)
            return json.loads(f.read())
    return {}

def paths_from_config_name(config_name):
    """Returns a tuple of the json file and the kernel config file paths
    """

    cpath = os.path.join(gentooimgr.configs.CONFIG_DIR, config_name)
    name, ext = os.path.splitext(config_name)
    if not name in gentooimgr.configs.KNOWN_CONFIGS and not os.path.exists(cpath):
        LOG.warn(f"Config json file {cpath} not found in known configurations")
        return {}

    kpath = os.path.join(gentooimgr.configs.CONFIG_DIR, name + ".config")
    if not os.path.exists(kpath):
        LOG.warn(f"Kernel config file {kpath} not found for {config_name}")


    return (cpath, kpath,)

def load_default_config(config_name):
    """This is called when a --config option is set. --kernel options update the resulting config, whether
    it be 'base' or other.
    If user is supplying their own configuration, this is not called.
    """
    name, ext = os.path.splitext(config_name)
    if not name in gentooimgr.configs.KNOWN_CONFIGS:
        LOG.warn(f"Name {name} not found in known configurations")
        return {}

    path = os.path.join(gentooimgr.configs.CONFIG_DIR, config_name)
    LOG.debug(f"Expects a config at {path}")
    with open(path, 'r') as f:
        return json.loads(f.read())


def inherit_config(config: dict) -> dict:
    """Returns the json file that the inherit key specifies; will recursively update if inherit values are set.
    """
    configuration = load_default_config(config.get("inherit"))
    if not configuration:
        configuration = load_config(config.get("inherit"))

    if not configuration:
        sys.stderr.write(f"\tWW: Warning: Inherited configuration {config.get('inherit')} is not found.\n")
        return {}

    if configuration.get("inherit"):
        configuration.update(inherit_config(configuration.get("inherit")))

    return configuration

def determine_config(args: argparse.Namespace) -> dict:
    """Check argparser options and return the most valid configuration

    The "package" key/value object overrides everything that is set, it does not update() them.
    If you override "base" package set, it's exactly what you set. It makes more sense to do it this way.
    For example, if you have a dist kernel config, you don't want the base.json to update and include all
    non-dist kernel options as it would add a lot of used space for unused functionality.

    The package set is only overridden in the top level json configuration file though;
    If you have multiple inherits, those package sets will be combined before the parent package set overrides
    with the keys that are set.

    If you have base.json and base2.json that contain multiple layers of "base" packages, ie: base: ['foo'] and base2: ['bar']
    then you will have in yours.json: packages { base: ['foo', 'bar'] } and unless you set "base", that is what you'll get.


    If you check `status` action, it will flatten all configurations into one, so the "inherit" key will always be null.

    :Returns:
        - configuration from json to dict
    """

    # Check custom configuration
    configuration = load_default_config(args.config or 'base.json')
    if not configuration:
        configuration = load_config(args.config)
    if not configuration:
        sys.stderr.write(f"\tWW: Warning: Configuration {args.config} is empty\n")
    else:
        if configuration.get("inherit"):
            inherited = inherit_config(configuration)
            new_packages = configuration.get("packages", {})
            old_packages = inherited.get("packages", {})
            inherited.update(configuration)
            # This will update your configuration with any keys in the inherited file that doesn't exist.
            # It will not override them as you will probably want the upper-most value.
            for ikey, ival in inherited.items():
                if ikey not in configuration:
                    configuration[ikey] = ival

            # Set back old package dict and then update only what is set in new:
            inherited['packages'] = old_packages
            for key, pkgs in new_packages.items():
                if pkgs:
                    inherited['packages'][key] = pkgs

            return inherited

    return configuration

