import sys
import time
import random
import logging
import ConfigParser

import requests
from PyQt4 import QtGui, QtCore

config = ConfigParser.RawConfigParser()
config.read('config.cfg')

logging.basicConfig(filename='program.log', level=logging.DEBUG)

class WindowThread(QtCore.QThread):
    def __init__(self, w):
        self.w = w
        super(WindowThread, self).__init__()

class NumberThread(WindowThread):
    def run(self):
        prev = 0
        next_ = 0
        while True:
            while prev == next_:
                next_ = random.randint(0, 9)
            prev = next_
            logging.info('displaying: {}, at time: {}'.format(next_, time.time()))
            self.w.lcd.display(next_)
            time.sleep(1)
            if not self.w.isVisible():
                return

class ColorThread(WindowThread):
    def __init__(self, w):
        self.opacity_step = float(config.get('ColorRectangle', 'opacity_step'))
        self.opacity_time = float(config.get('ColorRectangle', 'opacity_time'))
        super(ColorThread, self).__init__(w)

    def run(self):
        opacity = 0
        while True:
            if not self.w.isVisible():
                return
            self.w.setWindowOpacity(opacity)
            opacity += self.opacity_step
            time.sleep(self.opacity_time)

class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super(SystemTrayIcon, self).__init__(icon, parent)

        menu = QtGui.QMenu(parent)
        exitAction = menu.addAction("Exit")
        self.setContextMenu(menu)
        QtCore.QObject.connect(exitAction,QtCore.SIGNAL('triggered()'), self.exit)

    def exit(self):
        logging.info('exiting application')
        QtCore.QCoreApplication.exit()

class NumberWindow(QtGui.QWidget):
    def __init__(self):
        super(NumberWindow, self).__init__()

        self.initUI()

    def initUI(self):
        self.lcd = QtGui.QLCDNumber(self)
        self.lcd.setDigitCount(1)
        self.lcd.display(0)
        btn = QtGui.QPushButton('Click me!', self)
        btn.clicked.connect(self.onClicked)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.lcd)
        vbox.addWidget(btn)
        self.setLayout(vbox)

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('User Test')
        self.setWindowIcon(QtGui.QIcon('icon.png'))

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    def onClicked(self):
        val = self.lcd.intValue()
        logging.info('Clicked {} @ {}'.format(val, time.time()))
        if val == 7:
            logging.info('closing window')
            self.close()

class ColorWindow(QtGui.QWidget):
    def __init__(self):
        super(ColorWindow, self).__init__()
        self.width = int(config.get('ColorRectangle', 'width'))
        self.height = int(config.get('ColorRectangle', 'height'))
        self.initUI()

    def initUI(self):
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        self.setPalette(palette)
        self.setWindowOpacity(0)
        center = QtGui.QApplication.desktop().screen().rect().center()
        x = center.x() - self.width / 2
        y = center.y() - self.height / 2
        self.setGeometry(x, y, self.width, self.height)
        self.setWindowTitle('User Test')
        self.setWindowIcon(QtGui.QIcon('icon.png'))

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)

    def mousePressEvent(self, event):
        self.close()

def main():
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    trayWidget = QtGui.QWidget()
    trayIcon = SystemTrayIcon(QtGui.QIcon('icon.png'), trayWidget)

    trayIcon.show()

    colorWindow = ColorWindow()
    t = show_color_window(colorWindow)

    # numberWindow = NumberWindow()
    # t = show_number_window(numberWindow)
    sys.exit(app.exec_())

def show_color_window(colorWindow):
    colorWindow.show()
    thread = ColorThread(colorWindow)
    thread.start()
    return thread

def show_number_window(numberWindow):
    numberWindow.show()
    thread = NumberThread(numberWindow)
    # thread.finished.connect(app.exit)
    thread.start()
    return thread
    

if __name__ == '__main__':
    main()