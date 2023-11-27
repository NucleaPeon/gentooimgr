import os
import argparse
import gentooimgr.config as config
import gentooimgr.download as download
import gentooimgr.qemu as qemu
import requests

def build(args: argparse.Namespace, image: str | None = None) -> None:
    iso = download.download(args)
    stage3 = download.download_stage3(args)
    portage = download.download_portage(args)
    image = qemu.create_image(image=args.image,
                              size=args.size)
    is_default = os.path.basename(image) == "gentoo."+args.format
    print(image)
    print(f"Image {image} build successfully.\nRun `python -m gentooimgr run {iso}{' ' + image if not is_default else ''}`")
