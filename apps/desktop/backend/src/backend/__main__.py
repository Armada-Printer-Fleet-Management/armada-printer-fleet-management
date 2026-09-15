import argparse

from backend.window import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the desktop backend window.")
    parser.add_argument("--target", required=True, help="URL or file:// URI the window loads.")
    run(parser.parse_args().target)


if __name__ == "__main__":
    main()
