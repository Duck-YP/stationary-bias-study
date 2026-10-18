"""Remove machine-specific path prefixes from archived metadata only."""
import re

LOCAL_PATH = re.compile(r"[A-Z]:[\\/][^\s\"'`<>;,\)]+")


def portable_metadata(data: bytes) -> bytes:
    def replace(match):
        path = re.sub(r"[\\/]+", "/", match.group())
        if path.endswith("/python.exe"):
            return "python"
        if "/stationary-bias-study" in path:
            suffix = path.split("/stationary-bias-study", 1)[1]
            return "." + suffix
        if "/Downloads/" in path:
            return "original_attachments/" + path.split("/Downloads/", 1)[1]
        return "original_environment/" + path.rsplit("/", 1)[-1]

    return LOCAL_PATH.sub(replace, data.decode("utf-8")).encode("utf-8")
