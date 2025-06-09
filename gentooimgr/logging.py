import logging
from argparse import Namespace
LOG = logging.getLogger('GI ')


def set_logger(args: Namespace) -> None:
    logging.basicConfig(level=logging.INFO if not args.debug else logging.DEBUG,
                        filename=args.logfile,
                        filemode='a' if args.logfile else None,
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S'
    )

