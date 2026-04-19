from __future__ import annotations

from desktop_agent.storage.migrate_usage import migrate as migrate_usage
from desktop_agent.storage.migrate_network import migrate as migrate_network
from desktop_agent.storage.migrate_speedtest import migrate as migrate_speedtest


def bootstrap_all() -> None:
    migrate_usage()
    migrate_network()
    migrate_speedtest()


if __name__ == "__main__":
    bootstrap_all()
    print("Database bootstrap complete.")