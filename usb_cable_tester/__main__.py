from .cli import main as _cli_main


def main() -> int:
    return _cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
