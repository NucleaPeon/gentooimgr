import os
import sys
import argparse
import pathlib
import gencloud.common
import gencloud.config


def main(args):
    '''Gentoo Cloud Image Builder Utility'''

    if args.action == "build":
        import gencloud.builder
        gencloud.builder.build(args)

    elif args.action == "run":
        import gencloud.run
        gencloud.run.run(args)

    elif args.action == "test":
        import gencloud.test

    elif args.action == "clean":
        import gencloud.clean

    elif args.action == "status":
        import gencloud.status
        gencloud.status.print_template(**vars(args))

    elif args.action == "cloud-cfg":
        import gencloud.cloud
        gencloud.cloud.configure(args)

    elif args.action == "command":
        import gencloud.command
        gencloud.command.command()

    elif args.action == "chroot":
        import gencloud.chroot
        gencloud.chroot.chroot(path=args.mountpoint, shell="/bin/bash")

if __name__ == "__main__":
    """Gentoo Cloud Image Builder Utility"""
    parser = argparse.ArgumentParser(prog="gencloud", description="Gentoo Cloud Image Builder Utility")
    parser.add_argument("-c", "--config", nargs='?', type=pathlib.Path,
                        help="Path to a custom conf file")
    parser.add_argument("-t", "--temporary-dir", nargs='?', type=pathlib.Path,
                        default=os.getcwd(), help="Path to temporary directory for downloading files")
    parser.add_argument("-j", "--threads", type=int, default=gencloud.config.THREADS,
                        help="Number of threads to use for building and emerging software")
    parser.add_argument("-d", "--download-dir", type=pathlib.Path, default=os.getcwd(),
                        help="Path to the desired download directory (default: current)")
    parser.add_argument("--openrc", dest="profile", action="store_const", const="openrc",
                        help="Select OpenRC as the Gentoo Init System")
    parser.add_argument("--systemd", dest="profile", action="store_const", const="systemd",
                        help="Select SystemD as the Gentoo Init System")
    parser.add_argument("-f", "--force", action="store_true",
                        help="Let action occur at potential expense of data loss or errors (applies to clean and cloud-cfg)")
    subparsers = parser.add_subparsers(help="gencloud actions", dest="action")
    subparsers.required = True

    # Build action
    parser_build = subparsers.add_parser('build', help="Download and verify all the downloaded components for cloud image")
    parser_build.add_argument("image", default=None, type=str, nargs='?',
                              help="Specify the exact image (date) you want to build; ex: 20231112T170154Z. Defaults to downloading the latest image. If image exists, will automatically use that one instead of checking online.")
    parser_build.add_argument("--no-verify", dest="verify", action="store_false", help="Do not verify downloaded iso")
    parser_build.add_argument("--verify", dest="verify", action="store_true", default=True,
                              help="Verify downloaded iso")
    parser_build.add_argument("--redownload", action="store_true", help="Overwrite downloaded files")

    parser_run = subparsers.add_parser('run', help="Run a Gentoo Image in QEMU to process it into a cloud image")

    parser_run.add_argument("--iso", default=None, type=pathlib.Path, nargs='?',
                            help="Run the specified image in qemu")
    parser_run.add_argument("image", default=gencloud.config.GENTOO_IMG_NAME,
                            type=pathlib.Path, nargs="?",
                            help="Run the specified image in qemu")
    parser_run.add_argument("-m", "--mounts", nargs='+', default=[],
                            help="Path to iso files to mount into the running qemu instance")

    parser_test = subparsers.add_parser('test', help="Test whether image is a legitamite cloud configured image")

    parser_clean = subparsers.add_parser('clean', help="Remove all downloaded files")
    # --force also applies to clean action

    parser_status = subparsers.add_parser('status', help="Review information, downloaded images and configurations")

    parser_cloud = subparsers.add_parser("cloud-cfg", help="Configure a guest qemu VM with cloud image infrastructure")
    parser_cloud.add_argument("--virtio", action="store_true",
                              help="Configure kernel with virtio support for bare metal")

    parser_chroot = subparsers.add_parser("chroot", help="Bind mounts and enter chroot with shell on guest. Unmounts binds on shell exit")
    parser_chroot.add_argument("mountpoint", nargs='?', default=gencloud.config.GENTOO_MOUNT,
                               help="Point to mount and run the chroot and shell")

    parser_cmd = subparsers.add_parser('command', help="Handle bind mounts and run command(s) in guest chroot, then unmount binds")
    parser_cmd.add_argument("cmds", nargs='*',
                            help="Commands to run (quote each command if more than one word, ie: \"grep 'foo'\" \"echo foo\")")

    args = parser.parse_args()

    isos = gencloud.common.find_iso(args.download_dir)
    if args.action == "run" and args.iso is None and len(isos) > 1:
        print(f"Error: multiple iso files were found in {args.download_dir}, please specify one using `--iso [iso]`")
        sys.exit(1)


    main(args)
