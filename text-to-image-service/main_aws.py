import argparse

from main import parse_args, run


def main() -> None:
    args = parse_args()
    if args.device == "auto":
        args.device = "cuda"
    run(args)


if __name__ == "__main__":
    main()
