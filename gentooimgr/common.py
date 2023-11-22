import os
import sys
import time
import copy
import json
from subprocess import Popen, PIPE

import gentooimgr.config

def older_than_a_day(fullpath):
    if not os.path.exists(fullpath):
        return True  # Don't fail on missing files
    filetime = os.path.getmtime(fullpath)
    return time.time() - filetime > gentooimgr.config.DAY_IN_SECONDS


def find_iso(download_dir):
    name = None
    ext = None
    found = []
    for f in os.listdir(download_dir):
        name, ext = os.path.splitext(f)
        if ext == ".iso":
            found.append(os.path.join(download_dir, f))

    return found

def make_iso_from_dir(mydir):
    """ Generates an iso with gentooimgr inside it for use inside a live cd guest
    :Returns:
        path to iso that was created or NoneType if mydir is not found
    """
    if not os.path.exists(mydir):
        return

    print(f"\t:: Making ISO with dir of {mydir}")
    path = os.path.join(mydir, "..", "cloudgen.iso")
    proc = Popen(["mkisofs",
        "--input-charset", "utf-8",
        "-J",
        "-r",
        "-V", "gentooimgr",
        "-m", "*.img",
        "-m", "*.iso",
        "-o", path,
        mydir
        ], stdout=PIPE, stderr=PIPE)
    proc.communicate()

    return path

def portage_from_dir(d, filename=None):
    """Find portage file from directory. Will do a check in os.listdir() for portage*.tar.bz2.

    If a filename is provided, this function either returns that filename assuming it exists in d,
    or return None. If filename is None, this looks through all entries for portage files and if
    only one exists, returns it, otherwise None.
    """
    found = []
    for f in os.listdir(d):
        if filename is not None:
            if filename == f:
                found.append(f)
        elif f.startswith("portage") and f.endswith(".tar.xz"):
            found.append(f)

    if len(found) > 1:
        sys.stderr.write("\tEE: More than one portage file exists, please specify the exact portage file with --portage [file]  or remove all others\n")
        sys.stderr.write(''.join([f"\t{f}\n" for f in found]))
        sys.stderr.write(f"in {d}\n")
        sys.exit(1)

    return found[0] if found else None


def stage3_from_dir(d, filename=None):
    """Find stage3 file from directory. Will do a check in os.listdir() for stage3*.tar.xz.

    If a filename is provided, this function either returns that filename assuming it exists in d,
    or return None. If filename is None, this looks through all entries for stage3 files and if
    only one exists, returns it, otherwise None.
    """
    found = []
    for f in os.listdir(d):
        if filename is not None:
            if filename == f:
                found.append(f)
        elif f.startswith("stage3") and f.endswith(".tar.xz"):
            found.append(f)

    if len(found) > 1:
        sys.stderr.write("More than one stage3 file exists, please specify the exact stage3 file or remove all others\n")
        sys.stderr.write(''.join([f"\t{f}\n" for f in found]))
        sys.stderr.write(f"in {d}\n")
        return None

    return found[0] if found else None

def generatecfg(args, config="gentoo.cfg"):
    path = args.download_dir
    cfgpath = os.path.join(path, config)
    cfg = copy.deepcopy(gentooimgr.config.CLOUD_CFG)  # Use defaults only
    if os.path.exists(cfgpath):
        try:
            with open(cfgpath, 'r') as f:
                cfg.update(json.loads(f.read()))
        except:
            print("\tEE: Specified config file doesn't exist or cannot be loaded as json")

    return cfg

def load_config(args):
    cfg = generatecfg(args)
    if args.config:
        override = generatecfg(args, config=args.config)
        cfg.update(cfgoverride)

    if cfg.get("portage") is None:
        cfg['portage'] = portage_from_dir(args.download_dir, filename=args.portage or cfg.get("portage"))
    if cfg.get("stage3") is None:
        cfg['stage3'] = stage3_from_dir(args.download_dir, filename=args.stage3 or cfg.get("stage3"))

    return cfg

