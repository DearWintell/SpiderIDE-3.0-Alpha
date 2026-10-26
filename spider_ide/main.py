import sys
import os

def main():
    from PyQt6.QtWidgets import QApplication
    from spider_ide.ui.splash_screen import SplashScreen
    from spider_ide.ui.main_window import MainWindow
    

    app = QApplication(sys.argv)
    

    app.setStyle("Fusion")
    

    splash = SplashScreen()
    splash.show_animated(duration=700)  
    

    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    

    from PyQt6.QtCore import QTimer
    QTimer.singleShot(900, lambda: MainWindow(file_path=file_path).show())
    

    sys.exit(app.exec())


if __name__ == "__main__":
    main() 