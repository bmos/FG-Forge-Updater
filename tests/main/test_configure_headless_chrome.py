from src.main import configure_headless_chrome


def convert_args_to_dict(args: list) -> dict[str, str]:
    return {key: value.split(",") if "," in value else value for arg in args for key, value in [arg.split("=") if "=" in arg else (arg, arg)]}


def test_configure_headless_chrome() -> None:
    options = configure_headless_chrome()
    args = convert_args_to_dict(options.arguments)
    assert "--headless" in args  # headless mode is active
    assert args["--headless"] == "new"  # headless mode is using new mode
    assert "--window-size" in args
    assert "--no-sandbox" in args
    assert int(args["--window-size"][0]) > 1024  # window size is at least 1024 wide
    assert int(args["--window-size"][1]) > 800  # window size is at least 800 tall
    assert "--user-agent" in args
    assert args["--user-agent"].__contains__("Mozilla/5.0 (compatible; FG-Forge-Updater")
    assert args["--user-agent"].__contains__("https://github.com/bmos/FG-Forge-Updater")
