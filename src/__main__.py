"""Allow running the package directly: python -m src.teams_webhook"""

import sys

from .teams_webhook import main

if __name__ == "__main__":
    sys.exit(main())
