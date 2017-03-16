import sys
import time
import random
import logging

import requests
from PyQt4 import QtGui, QtCore

logging.basicConfig(filename='program.log', level=logging.DEBUG)

class AThread(QtCore.QThread):
    def __init__(self, w):
        self.w = w
        super(AThread, self).__init__()
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

    def onClicked(self):
        val = self.lcd.intValue()
        logging.info('Clicked {} @ {}'.format(val, time.time()))
        if val == 7:
            logging.info('closing window')
            self.close()



def main():
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    trayWidget = QtGui.QWidget()
    trayIcon = SystemTrayIcon(QtGui.QIcon('icon.png'), trayWidget)

    trayIcon.show()

    response = requests.get("http://httpbin.org/ip")
    logging.info('Response took {} seconds.'.format(response.elapsed.total_seconds()))
    logging.info('IP: {}'.format(response.json()['origin']))

    numberWindow = NumberWindow()
    numberWindow.setWindowFlags(
        QtCore.Qt.WindowStaysOnTopHint
        | QtCore.Qt.FramelessWindowHint)
    numberWindow.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
    t = show_number_window(numberWindow)
    sys.exit(app.exec_())

def show_number_window(numberWindow):
    numberWindow.show()
    thread = AThread(numberWindow)
    # thread.finished.connect(app.exit)
    thread.start()
    return thread
    

if __name__ == '__main__':
    main()