import os
import argparse
import gentooimgr.config as config
import gentooimgr.download as download
import gentooimgr.qemu as qemu
import gentooimgr.common
import requests

def build(args: argparse.Namespace, config: dict) -> None:

    iso = config.get("iso") or download.download(args)
    stage3 = config.get("stage3") or download.download_stage3(args)
    portage = config.get("portage") or download.download_portage(args)
    filename = f"{args.image}.{args.format}"
    image = qemu.create_image(args, config) if config.get("imagename") is None else config.get("imagename")
    if not os.path.exists(image):
        raise Exception(f"Image {image} does not exist")

    is_default = os.path.basename(image) == filename
    print(image)
    print(f"Image {image} build successfully.\nRun `python -m gentooimgr run{' ' + image if not is_default else ''} --iso {iso}`")
