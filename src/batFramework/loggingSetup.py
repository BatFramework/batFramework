import logging
import sys


def setup_logging(
    level: int = logging.INFO,
) -> None:

    # stdout
    console_handler = logging.StreamHandler(sys.stdout)


    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s | %(levelname)-8s | "
            "%(name)s:%(lineno)d | %(message)s"
        ),
        handlers=[console_handler],
        force=True,
    )