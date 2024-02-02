from main import configure_headless_chrome


def convert_args_to_dict(args):
    return {key: value.split(",") if "," in value else value for key, value in (arg.split("=") for arg in args)}


def test_configure_headless_chrome() -> None:
    options = configure_headless_chrome()
    args = convert_args_to_dict(options.arguments)
    assert "--headless" in args  # headless mode is active
    assert args["--headless"] == "new"  # headless mode is using new mode
    assert "--remote-debugging-port" in args  # remote debugging is active
    assert "--window-size" in args
    assert int(args["--window-size"][0]) > 1024  # window size is at least 1024 wide
    assert int(args["--window-size"][1]) > 800  # window size is at least 800 tall
