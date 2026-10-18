import sys

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--manga-finish-self-test":
        from desktop_app.manga_finish_check import run_check
        raise SystemExit(run_check(sys.argv[2]))
    from desktop_app.main import run
    raise SystemExit(run())
