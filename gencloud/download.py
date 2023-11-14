"""Module to handle downloading and verification of Gentoo images
"""
import os
import re
import requests
import tempfile
import gencloud.config as config

hashpattern = re.compile(config.GENTOO_FILE_HASH_RE, re.MULTILINE)
isopattern =  re.compile(config.GENTOO_FILE_ISO_RE, re.MULTILINE)

def check_for_iso(path=None, against=None, update=False):
    pass

def parse_latest_text(downloadpath) -> tuple:
    """Returns a tuple of (hash type, iso name, iso bytes)
    """
    with open(downloadpath) as f:
        content = f.read()
        m_hash = hashpattern.search(content)
        m_iso = isopattern.search(content)
        return (m_hash.group(0) if not m_hash is None else None,
                m_iso.group(1) if not m_iso is None else None,
                m_iso.group(2) if not m_iso is None else None,)

def download(args, url=None, use_latest=False):
    """
    :Parameters:
        - url: str or None. If None, will generate a url to the latest minimal install iso
    """
    if url is None:
        url = os.path.join(config.GENTOO_BASE_URL, config.GENTOO_LATEST_FILE)

    # Download the latest txt file
    filename = os.path.basename(url)
    downloadpath = os.path.join(config.TEMPORARY_DIRECTORY, filename)
    if not os.path.exists(downloadpath) or args.redownload:
        r = requests.get(url)
        if r.status_code == 200:
            with open(downloadpath, 'wb') as f:
                f.write(r.content)
            print("Written %s to %s" % (filename, config.TEMPORARY_DIRECTORY))

    hashtype, latest, size = parse_latest_text(downloadpath)

    has_image = check_for_iso(against=latest, update=use_latest)
    if has_image:
        return None



