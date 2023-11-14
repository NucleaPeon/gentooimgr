import os
import argparse
import pathlib
import multiprocessing

def main(args):
    '''Gentoo Cloud Image Builder Utility'''

    if args.action == "build":
        import gencloud.builder
        gencloud.builder.build(args)

    elif args.action == "run":
        import gencloud.run

    elif args.action == "test":
        import gencloud.test

    elif args.action == "clean":
        import gencloud.clean

    elif args.action == "status":
        import gencloud.status
        gencloud.status.print_template(**vars(args))


if __name__ == "__main__":
    """Gentoo Cloud Image Builder Utility"""
    parser = argparse.ArgumentParser(prog="gencloud", description="Gentoo Cloud Image Builder Utility")
    parser.add_argument("-c", "--config", nargs='?', type=pathlib.Path,
                        help="Path to a custom conf file")
    parser.add_argument("-t", "--temporary-dir", nargs='?', type=pathlib.Path,
                        default="/tmp", help="Path to temporary directory for downloading files")
    parser.add_argument("-j", "--threads", type=int, default=multiprocessing.cpu_count(),
                        help="Number of threads to use for building and emerging software")
    parser.add_argument("-d", "--download-dir", type=pathlib.Path, default=os.getcwd(),
                        help="Path to the desired download directory (default: current)")
    parser.add_argument("--openrc", dest="profile", action="store_const", const="openrc",
                        help="Select OpenRC as the Gentoo Init System")
    parser.add_argument("--systemd", dest="profile", action="store_const", const="systemd",
                        help="Select SystemD as the Gentoo Init System")

    subparsers = parser.add_subparsers(help="gencloud actions", dest="action")
    subparsers.required = True

    # Build action
    parser_build = subparsers.add_parser('build', help="Build a Gentoo Cloud Image")
    parser_build.add_argument("image", default=None, type=str, nargs='?',
                              help="Specify the exact image (date) you want to build; ex: 20231112T170154Z. Defaults to downloading the latest image. If image exists, will automatically use that one instead of checking online.")
    parser_build.add_argument("--no-verify", dest="verify", action="store_false", help="Do not verify downloaded iso")
    parser_build.add_argument("--verify", dest="verify", action="store_true", default=True,
                              help="Verify downloaded iso")
    parser_build.add_argument("--redownload", action="store_true", help="Overwrite downloaded files")

    parser_run = subparsers.add_parser('run', help="Run a Gentoo Cloud Image in QEMU")

    parser_test = subparsers.add_parser('test', help="Test whether image is a legitamite cloud configured image")

    parser_clean = subparsers.add_parser('clean', help="Remove all downloaded files")
    parser_clean.add_argument("-f", "--force", action="store_true", help="Do not prompt to remove files")

    parser_status = subparsers.add_parser('status', help="Review information, downloaded images and configurations")

    args = parser.parse_args()
    main(args)
