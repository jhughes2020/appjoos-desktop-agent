from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from desktop_agent.storage.bootstrap_db import bootstrap_all
from desktop_agent.ui.main_window import MainWindow


def main() -> None:
    bootstrap_all()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()