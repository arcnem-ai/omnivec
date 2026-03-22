from __future__ import annotations

from omnivec.runners import PicvecRunner, TexvecRunner
from omnivec.settings import get_settings


def main() -> None:
    settings = get_settings()
    print("Warming texvec shared cache...")
    TexvecRunner(settings).ensure_shared_ready()
    print("Warming picvec shared cache...")
    PicvecRunner(settings).ensure_shared_ready()
    print("Shared caches are ready.")


if __name__ == "__main__":
    main()
