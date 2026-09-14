"""``python -m scripts.bootstrap.stub --port N``."""
from __future__ import annotations

import argparse

from scripts.bootstrap.stub.server import serve


def main() -> int:
    """Serve until interrupted."""
    parser = argparse.ArgumentParser(prog="scripts.bootstrap.stub")
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    server = serve(args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
