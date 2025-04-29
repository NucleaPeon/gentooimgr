"""Module to handle downloading and verification of Gentoo images

To ensure accuracy, we re-download every .txt file if it's older than one day.
We assume that people building a cloud configured image want what is most up to date.
If you have a specific image you want built over and over regardless, create a config
file and load it in using -c/--config that points GENTOO_* values to the files you want.
"""

import os
import re
import sys
from datetime import date
import hashlib
import progressbar
from urllib.request import urlretrieve
import tempfile
import gentooimgr.config
from gentooimgr.logging import LOG
from gentooimgr.common import older_than_a_day

hashpattern =    re.compile(gentooimgr.config.GENTOO_FILE_HASH_RE, re.MULTILINE)
isopattern =     re.compile(gentooimgr.config.GENTOO_FILE_ISO_RE, re.MULTILINE)
isohashpattern = re.compile(gentooimgr.config.GENTOO_FILE_ISO_HASH_RE, re.MULTILINE)
stage3pattern  = re.compile(gentooimgr.config.GENTOO_FILE_STAGE3_RE, re.MULTILINE)
stage3hashpattern = re.compile(gentooimgr.config.GENTOO_FILE_STAGE3_HASH_RE, re.MULTILINE)

class DownloadProgressBar():
    def __init__(self):
        self.progress = None

    def __call__(self, block_num, block_size, total_size):
        if not self.progress:
            self.progress = progressbar.ProgressBar(maxval=total_size)
            self.progress.start()

        downloaded = block_num * block_size
        if downloaded < total_size:
            self.progress.update(downloaded)
        else:
            self.progress.finish()

def parse_latest_iso_text(fullpath) -> tuple:
    """Returns a tuple of (hash type, iso name, iso bytes)"""
    with open(fullpath) as f:
        content = f.read()
        m_hash = hashpattern.search(content)
        m_iso = isopattern.search(content)
        return (m_hash.group(1) if not m_hash is None else None,
                m_iso.group(1) if not m_iso is None else None,
                m_iso.group(2) if not m_iso is None else None,)

def parse_latest_stage3_text(fullpath) -> tuple:
    """Returns a tuple of (hash type, iso name, iso bytes)
    """
    with open(fullpath) as f:
        content = f.read()
        m_hash = hashpattern.search(content)
        m_stage3 = stage3pattern.search(content)
        return (m_hash.group(1) if not m_hash is None else None,
                m_stage3.group(1) if not m_stage3 is None else None,
                m_stage3.group(2) if not m_stage3 is None else None,)

def verify(args, _type: str, baseurl: str, hashpattern, filename: str) -> bool:
    """Downloads hash file and run a hash check on the file
    :Parameters:
        - args: Namespace of parsed arguments
        - _type: str hash type
        - baseurl: (remote) folder where hashsum file is contained
        - hashpattern:
        - filename: str name of file to check (used to download corresponding hash file)

            A install-amd64-minimal-2023111iso2T170154Z.iso file will have a
              install-amd64-minimal-20231112T170154Z.iso.sha256 for example.

    :Returns:
        Whether iso was verified using the specified hash

    """
    digest = hashlib.file_digest(open(os.path.join(args.download_dir, filename), 'rb'), _type.lower())
    filename = filename+f".{_type.lower()}"  # Update to hash file
    hashfile = os.path.join(baseurl, filename)
    fullpath = os.path.join(args.download_dir, os.path.basename(hashfile))
    if not os.path.exists(fullpath) or args.redownload or older_than_a_day(fullpath):
        print(f"Downloading {filename}")
        urlretrieve(hashfile, fullpath, DownloadProgressBar())

    hd = digest.hexdigest()
    with open(fullpath, 'r') as f:
        content = f.read()
        m_hash = hashpattern.search(content)
        _hash = m_hash.group(1)
        if _hash != hd and args.force:
            LOG.error(f"Hash mismatch {hd} != {_hash} for {filename}")
        else:
            assert hd == _hash, f"Hash mismatch {hd} != {_hash}, use --force to bypass"

def download_stage3(args, url=None, cfg={}) -> str:
    uname = cfg.get("architecture", os.uname().machine)
    if uname.startswith("ppc"):
        uname = "ppc"  # fix gentoo not having separate 32/64bit ppc urls/files
    C = gentooimgr.config.config(architecture=uname)
    if url is None:
        if not hasattr(args, "profile"):
            # Set this to either the config value or empty, defaulting it to openrc
            args.profile = cfg.get("initsys")
        if args.profile == "systemd":
            url = os.path.join(C.GENTOO_BASE_STAGE_SYSTEMD_URL, C.GENTOO_LATEST_STAGE_SYSTEMD_FILE)

        else:
            url = os.path.join(C.GENTOO_BASE_STAGE_OPENRC_URL, C.GENTOO_LATEST_STAGE_OPENRC_FILE)

    filename = os.path.basename(url)
    fullpath = os.path.join(args.download_dir, filename)
    if not os.path.exists(fullpath) or args.redownload or older_than_a_day(fullpath):
        urlretrieve(url, fullpath, DownloadProgressBar())

    hashtype, latest, size = parse_latest_stage3_text(fullpath)
    size = int(size)

    filename = latest
    fullpath = os.path.join(args.download_dir, filename)
    if not os.path.exists(fullpath) or args.redownload:
        url = os.path.join(
                C.GENTOO_BASE_STAGE_SYSTEMD_URL if args.profile == "systemd" else \
                C.GENTOO_BASE_STAGE_OPENRC_URL,
                filename)
        urlretrieve(url, fullpath, DownloadProgressBar())

    # Verify byte size
    stage3size = os.path.getsize(fullpath)
    assert size == stage3size, f"Stage 3 size {size} does not match expected value {stage3size}."
    verify(args, hashtype, C.GENTOO_BASE_STAGE_SYSTEMD_URL if args.profile == "systemd" else \
           C.GENTOO_BASE_STAGE_OPENRC_URL,  stage3hashpattern, filename)
    return fullpath


def download_portage(args, url=None, cfg={}) -> str:
    """Handle downloading of portage system for installation into cloud image

    We always download the latest portage package and rename it to today's date.
    If using today's date to grab portage, sometimes depending on timezone, the
    package won't be available. If always using latest, worst case scenario is you
    have a portage package a day late.


    """
    uname = cfg.get("architecture", os.uname().machine)
    if uname.startswith("ppc"):
        uname = "ppc"  # fix gentoo not having separate 32/64bit ppc urls/files
    C = gentooimgr.config.config(architecture=uname)
    if url is None:
        url = C.GENTOO_PORTAGE_FILE

    base = os.path.basename(url)  # Uses 'latest' filename
    today = date.today()
    # Write latest to today's date so we don't constantly redownload, but
    filename = base.replace("latest", "%d%d%d" % (today.year, today.month, today.day))
    fullpath = os.path.join(args.download_dir, filename)
    # Portage is always "latest" in this case, so definitely check if older than a day and redownload.
    if not os.path.exists(fullpath) or args.redownload or older_than_a_day(fullpath):
        print(f"Downloading {filename} ({base})")
        urlretrieve(url, fullpath, DownloadProgressBar())

    return fullpath


def download(args, config, url=None) -> str:
    """Download txt file with iso name and hash type
    :Parameters:
        - args: Namespace with parsed arguments
        - config: Namespace of configurations from gentooimgr.config.config()
        - url: str or None. If None, will generate a url to the latest minimal install iso

    :Returns:
        Full path to the downloaded iso file

    Will cause program to exit if iso byte size fails to match expected value.
    """
    # TODO: ensure downloads and even checks are based on the values from checks from last request
    # This may mean looking for all files (based on regex/glob) and checking dates, finding max, etc.
    if url is None:
        url = os.path.join(config.GENTOO_BASE_ISO_URL, config.GENTOO_LATEST_ISO_FILE)

    # Download the latest txt file
    filename = os.path.basename(url)
    fullpath = os.path.join(args.download_dir, filename)
    if not os.path.exists(fullpath) or args.redownload or older_than_a_day(fullpath):
        print(f"Downloading {filename}")
        urlretrieve(url, fullpath, DownloadProgressBar())

    hashtype, latest, size = parse_latest_iso_text(fullpath)
    size = int(size)

    # Download the iso file
    filename = latest
    fullpath = os.path.join(args.download_dir, filename)
    if not os.path.exists(fullpath) or args.redownload :
        print(f"Downloading {filename}")
        url = os.path.join(config.GENTOO_BASE_ISO_URL, filename)
        urlretrieve(url, fullpath, DownloadProgressBar())

    # Verify byte size
    isosize = os.path.getsize(fullpath)
    assert size == isosize, f"ISO size {size} does not match expected value {isosize}."
    verify(args, hashtype, config.GENTOO_BASE_ISO_URL, isohashpattern, filename)

    return fullpath
