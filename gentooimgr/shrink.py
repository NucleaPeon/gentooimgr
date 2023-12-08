import os
import datetime
from subprocess import PIPE, Popen

def shrink(args, config,  stamp=None):
    if stamp is None:
        dt = datetime.datetime.utcnow()
        # 0 padded month and day timestamp
        stamp = f"{dt.year}-{dt.month:02d}-{dt.day:02d}"
    name, ext = os.path.splitext(config.get("imagename") or args.img)
    filename = f"{name}-{stamp}.img"
    proc = Popen(["virt-sparsify", "--compress", img, filename])
    proc.communicate()
    return filename
