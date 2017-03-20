import sys
import time
import random
import logging
import ConfigParser

import requests
from PyQt4 import QtGui, QtCore
import pyHook
import pythoncom

config = ConfigParser.RawConfigParser()
config.read('config.cfg')

logging.basicConfig(filename='program.log', 
    level=logging.DEBUG, 
    format='%(created)i:%(message)s',
    )

user_active_global = (False, time.time())

class ActivityDetectionThread(QtCore.QThread):
    def run(self):
        hm = pyHook.HookManager()
        hm.KeyDown = self.set_active
        hm.HookKeyboard()
        pythoncom.PumpMessages()

    def set_active(self, event):
        global user_active_global
        print 'active'
        user_active_global = (True, time.time())

class TimeKeeperThread(QtCore.QThread):
    def __init__(self):
        self.time_between_tasks = config.getint('Main', 'time_between_tasks')
        super(TimeKeeperThread, self).__init__()

    def run(self):
        global user_active_global
        self.next_task_time = time.time() + self.time_between_tasks
        while True:
            if time.time() - user_active_global[1] > 300:
                user_active_global = (False, user_active_global[1])
            if time.time() > self.next_task_time:
                if user_active_global[0]:
                    self.trigger_task()
            time.sleep(10)

    def trigger_task(self):
        self.next_task_time + self.time_between_tasks
        self.emit(QtCore.SIGNAL('triggerTask'))


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
            logging.info('displaying: {}'.format(next_))
            self.w.lcd.display(next_)
            time.sleep(1)
            if not self.w.isVisible():
                return

class ColorThread(WindowThread):
    def __init__(self, w):
        self.opacity_step = config.getfloat('ColorRectangle', 'opacity_step')
        self.opacity_time = config.getfloat('ColorRectangle', 'opacity_time')
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
        logging.info('Clicked {}'.format(val))
        if val == 7:
            logging.info('closing window')
            self.close()

class ColorWindow(QtGui.QWidget):
    def __init__(self):
        super(ColorWindow, self).__init__()
        self.width = config.getint('ColorRectangle', 'width')
        self.height = config.getint('ColorRectangle', 'height')
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
        logging.info('user clicked on rectangle. opacity level: {}'.format(self.windowOpacity()))
        self.close()

    def startTask(self):
        if self.isVisible():
            return
        logging.info('showing ColorWindow')
        self.show()
        self.thread = ColorThread(self)
        self.thread.start()

def main():
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    trayWidget = QtGui.QWidget()
    trayIcon = SystemTrayIcon(QtGui.QIcon('icon.png'), trayWidget)

    trayIcon.show()
    logging.info('starting application')

    t = ActivityDetectionThread()
    t.start()

    t2 = TimeKeeperThread()
    t2.start()

    task = config.get('Main', 'task')
    if task == 'color-rectangle':
        colorWindow = ColorWindow()
        colorWindow.connect(t2, QtCore.SIGNAL('triggerTask'), colorWindow.startTask)
    elif task == 'numbers':
        colorWindow = ColorWindow()
        colorWindow.connect(t2, QtCore.SIGNAL('triggerTask'), colorWindow.startTask)


    sys.exit(app.exec_())

def show_number_window(numberWindow):
    logging.info('showing NumberWindow')
    numberWindow.show()
    thread = NumberThread(numberWindow)
    # thread.finished.connect(app.exit)
    thread.start()
    return thread
    

if __name__ == '__main__':
    main()