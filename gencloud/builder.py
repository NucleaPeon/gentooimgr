import argparse
import gencloud.config as config
import gencloud.download as download
import requests

def build(args: argparse.Namespace, image: str | None = None) -> None:
    print(f"builder.py module build() {image}")
    download.download(args)
