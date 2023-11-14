"""Module to handle downloading and verification of Gentoo images
"""
import os
import re
import sys
import hashlib
import progressbar
from urllib.request import urlretrieve
import tempfile
import gencloud.config as config

hashpattern =    re.compile(config.GENTOO_FILE_HASH_RE, re.MULTILINE)
isopattern =     re.compile(config.GENTOO_FILE_ISO_RE, re.MULTILINE)
ioshashpattern = re.compile(config.GENTOO_FILE_ISO_HASH_RE, re.MULTILINE)

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

def parse_latest_text(fullpath) -> tuple:
    """Returns a tuple of (hash type, iso name, iso bytes)
    """
    with open(fullpath) as f:
        content = f.read()
        m_hash = hashpattern.search(content)
        m_iso = isopattern.search(content)
        return (m_hash.group(1) if not m_hash is None else None,
                m_iso.group(1) if not m_iso is None else None,
                m_iso.group(2) if not m_iso is None else None,)

def verify(args, _type: str, filename: str) -> bool:
    """Downloads hash file and run a hash check on the file
    :Parameters:
        - _type: str hash type
        - download_dir: str path to download directory
        - filename: str name of file to check (used to download corresponding hash file)

            A install-amd64-minimal-20231112T170154Z.iso file will have a
              install-amd64-minimal-20231112T170154Z.iso.sha256 for example.

    :Returns:
        Whether iso was verified using the specified hash

    """
    digest = hashlib.file_digest(open(os.path.join(args.download_dir, filename), 'rb'), _type.lower())
    filename = filename+f".{_type.lower()}"  # Update to hash file
    hashfile = os.path.join(config.GENTOO_BASE_URL, filename)
    fullpath = os.path.join(args.download_dir, os.path.basename(hashfile))
    if not os.path.exists(fullpath) or args.redownload:
        print(f"Downloading {filename}")
        urlretrieve(hashfile, fullpath, DownloadProgressBar())


    hd = digest.hexdigest()
    with open(fullpath, 'r') as f:
        content = f.read()
        m_isohash = ioshashpattern.search(content)
        _hash = m_isohash.group(1)
        print(_hash, hd, m_isohash)
        assert hd == _hash


def download(args, url=None) -> str:
    """Download txt file with iso name and hash type
    :Parameters:
        - args: Namespace with parsed arguments
        - url: str or None. If None, will generate a url to the latest minimal install iso

    :Returns:
        Full path to the downloaded iso file

    Will cause program to exit if iso byte size fails to match expected value.
    """
    if url is None:
        url = os.path.join(config.GENTOO_BASE_URL, config.GENTOO_LATEST_FILE)

    # Download the latest txt file
    filename = os.path.basename(url)
    fullpath = os.path.join(args.download_dir, filename)
    if not os.path.exists(fullpath) or args.redownload:
        print(f"Downloading {filename}")
        urlretrieve(url, fullpath, DownloadProgressBar())

    hashtype, latest, size = parse_latest_text(fullpath)
    size = int(size)

    # Download the iso file
    filename = latest
    fullpath = os.path.join(args.download_dir, filename)
    if not os.path.exists(fullpath) or args.redownload:
        print(f"Downloading {filename}")
        url = os.path.join(config.GENTOO_BASE_URL, filename)
        urlretrieve(url, fullpath, DownloadProgressBar())

    # Verify byte size
    isosize = os.path.getsize(fullpath)
    assert size == isosize
    verify(args, hashtype, filename)

    return fullpath

