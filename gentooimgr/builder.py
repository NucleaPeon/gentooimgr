import os
import argparse
import gentooimgr.config
import gentooimgr.download as download
import gentooimgr.qemu as qemu
import gentooimgr.common
import gentooimgr.errorcodes
from gentooimgr.logging import LOG

def build(args: argparse.Namespace, config: dict) -> int:
    c = gentooimgr.config.config(config.get("architecture"))
    iso = config.get("iso") or download.download(args, c)
    stage3 = config.get("stage3") or download.download_stage3(args)
    portage = config.get("portage") or download.download_portage(args)
    filename = f"{args.image}.{args.format}"
    image, code = qemu.create_image(args, config)
    if not os.path.exists(image):
        raise Exception(f"Image {image} does not exist")

    is_default = os.path.basename(image) == filename
    LOG.info(f"\t:: {image}")
    print(f"Image {image} build successfully.\nRun `python -m gentooimgr run{' ' + image if not is_default else ''} --iso {iso}`")
    return code
