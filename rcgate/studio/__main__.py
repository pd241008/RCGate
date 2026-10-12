"""Start the localhost studio API. Offline flags are set before model libraries load."""

from __future__ import annotations

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from rcgate.studio.server import main

if __name__ == "__main__":
    raise SystemExit(main())
