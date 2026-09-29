import argparse

from armada_app.window import run
from armada_runtime.environment import Environment


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the desktop backend window.")
    parser.add_argument(
        "--target",
        help="URL or file:// URI the window loads. Defaults to the built frontend.",
    )
    run(parser.parse_args().target or Environment.default_frontend_target())


if __name__ == "__main__":
    main()
