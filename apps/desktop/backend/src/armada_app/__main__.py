import argparse
import logging
import sys

from armada_app.window import run
from armada_runtime.environment import Environment
from armada_runtime.logger import ApplicationLogger


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the desktop backend window.")
    parser.add_argument(
        "--target",
        help="URL or file:// URI the window loads. Defaults to the built frontend.",
    )
    args = parser.parse_args()
    ApplicationLogger(
        Environment.log_path(),
        level=logging.DEBUG if Environment.is_dev else logging.INFO,
        console=sys.stderr,
    ).install()
    logging.getLogger(__name__).info("Starting", extra={"development": Environment.is_dev})
    run(args.target or Environment.default_frontend_target())


if __name__ == "__main__":
    main()
