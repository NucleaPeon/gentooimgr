import os
import datetime
from subprocess import PIPE, Popen
from gentooimgr.logging import LOG


def shrink(args, config,  stamp=None):
    if stamp is None:
        dt = datetime.datetime.utcnow()
        # 0 padded month and day timestamp
        stamp = f"{dt.year}-{dt.month:02d}-{dt.day:02d}"
    name, ext = os.path.splitext(config.get("imagename") or args.image)
    # ext includes the .
    filename = f"{name}-{stamp}{ext}"
    LOG.info(f"\t::Shrink {args.image} to {filename}")
    image = args.image
    if args.convert:
        proc = Popen(["virt-sparsify", "--convert", "qcow2", image, f"converted-{image}"])
        proc.communicate()
        if args.only_convert:
            return filename, proc.returncode

        image = f"converted-{image}"

    proc = Popen(["virt-sparsify", "--compress", image, filename])
    proc.communicate()
    return filename, proc.returncode
