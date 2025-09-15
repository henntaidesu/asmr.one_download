from src.UI.download_page import DownloadPage
from PyQt6.QtWidgets import QApplication
import sys
import ctypes

# PyInstaller打包命令（确保隐藏控制台）：
# 方式1（推荐）: pyinstaller main.spec
# 方式2: pyinstaller --noconsole --onefile main.py
# 方式3: 运行build_exe.bat脚本自动打包

if __name__ == '__main__':
    # 更强力的控制台隐藏方法
    if getattr(sys, 'frozen', False):
        # 当打包为exe时，多种方式隐藏控制台
        try:
            import win32gui
            import win32con
            # 方法1: 使用win32gui隐藏窗口
            console_window = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(console_window, win32con.SW_HIDE)
        except ImportError:
            # 方法2: 使用ctypes隐藏控制台
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            except:
                pass
        except:
            # 方法3: 备用方案
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            except:
                pass

    app = QApplication(sys.argv)
    window = DownloadPage()
    window.show()
    sys.exit(app.exec())
