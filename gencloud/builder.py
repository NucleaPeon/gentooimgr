import os
import argparse
import gencloud.config as config
import gencloud.download as download
import gencloud.qemu as qemu
import requests

def build(args: argparse.Namespace, image: str | None = None) -> None:
    iso = download.download(args)
    stage3 = download.download_stage3(args)
    portage = download.download_portage(args)
    image = qemu.create_image()
    is_default = os.path.basename(image) == "gentoo.img"
    print(image)
    print(f"Image {image} build successfully.\nRun `python -m gencloud run {iso}{' ' + image if not is_default else ''}`")
