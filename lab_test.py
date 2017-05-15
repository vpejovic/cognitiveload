import sys
import os
import time
import random
import logging
import ConfigParser

import requests
from PyQt4 import QtGui, QtCore
import pyHook
import pythoncom
import tailer

config = ConfigParser.RawConfigParser()
config.read('lab_config.cfg')

LOGGING_DIR = 'C:\ProgramData\cog_app'
if not os.path.exists(LOGGING_DIR):
    os.makedirs(LOGGING_DIR)

logging.basicConfig(filename=LOGGING_DIR+'\lab_program.log', 
    level=logging.DEBUG, 
    format='%(created)i:%(message)s',
    )


class LogTailerThread(QtCore.QThread):
    TRIGGERS = ['Sync Slide', 'Hidden Pattern Question Slide', "Finding A's Question Slide", 'Gestalt Completion Question Slide',
    'Pursuit Test Question Slide', 'Number Comparison Question Slide', "Scattered X's Question Slide"]
    STOPPERS = ['Break Slide', 'TimeIsUp Slide', 'Rating Slide']
    def run(self):
        log_file = open(config.get('Main', 'log_file'), 'r')

        for line in tailer.follow(log_file):
            self.parse_line(line)

    def parse_line(self, line):
        parts = line.split(', ')
        if len(parts) > 1:
            if parts[1].strip() in self.TRIGGERS:
                self.trigger_task()
            elif parts[1].strip() in self.STOPPERS:
                self.stop_task()

    def trigger_task(self):
        self.emit(QtCore.SIGNAL('triggerTask'))

    def stop_task(self):
        self.emit(QtCore.SIGNAL('stopTask'))


class WindowThread(QtCore.QThread):
    def __init__(self, w):
        self.w = w
        super(WindowThread, self).__init__()

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

class SumNumbersWindow(QtGui.QWidget):
    def __init__(self):
        super(SumNumbersWindow, self).__init__()
        self.initUI()
        self.sum_ = 0
        self.previous_numbers = []
        self.reset_previous_numbers()
        self.status = 'RUNNING'

    def initUI(self):
        self.lcd = QtGui.QLCDNumber(self)
        self.lcd.setDigitCount(1)
        self.lcd.display(0)
        self.btn = QtGui.QPushButton('Potrdi', self)
        self.btn.clicked.connect(self.onClicked)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.lcd)
        vbox.addWidget(self.btn)
        self.setLayout(vbox)
        x = config.getint('SumNumbers', 'x')
        y = config.getint('SumNumbers', 'y')
        width = config.getint('SumNumbers', 'width')
        height = config.getint('SumNumbers', 'height')
        self.setGeometry(x, y, width, height)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.white)
        self.setPalette(p)
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    def reset_previous_numbers(self):
        prev_num = config.getint('SumNumbers', 'previous_numbers')
        self.previous_numbers = [0] * prev_num

    def onClicked(self):
        sum_limit = config.getint('SumNumbers', 'sum_limit')
        if self.status != 'RUNNING':
            return
        if self.sum_ >= sum_limit:
            self.success()
        else:
            self.failure()

    def success(self):
        logging.info('user guessed correctly sum was {}'.format(self.sum_))
        self.sum_ = 0
        self.status = 'PAUSE'
        self.reset_previous_numbers()
        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.green)
        self.setPalette(p)

    def failure(self):
        logging.info('user guessed incorrectly sum was {}'.format(self.sum_))
        self.status = 'PAUSE'
        self.sum_ = 0
        self.reset_previous_numbers()
        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.red)
        self.setPalette(p)

    def startTask(self):
        if self.isVisible():
            return
        self.show()
        self.thread = SumNumbersThread(self)
        self.thread.start()

    def stopTask(self):
        self.close()

class SumNumbersThread(WindowThread):
    def run(self):
        display_time = config.getfloat('SumNumbers', 'display_time')
        between_time = config.getfloat('SumNumbers', 'between_time')
        prev_num = config.getint('SumNumbers', 'previous_numbers')
        prev = 0
        next_ = 0
        counter = 0
        while True:
            if self.w.status == 'PAUSE':
                time.sleep(between_time)
                p = self.w.palette()
                p.setColor(self.w.backgroundRole(), QtCore.Qt.white)
                self.w.setPalette(p)
                self.w.status = 'RUNNING'

            elif self.w.status == 'RUNNING':
                self.w.lcd.setVisible(False)
                self.w.btn.setVisible(False)
                time.sleep(between_time)
                while prev == next_:
                    next_ = random.randint(1, 9)
                prev = next_
                self.w.previous_numbers[counter % prev_num] = next_
                counter += 1
                self.w.sum_ = sum(self.w.previous_numbers)
                logging.info('displaying: {}, sum is: {}'.format(next_, self.w.sum_))
                print 'displaying: {}, sum is: {}'.format(next_, self.w.sum_)
                self.w.lcd.display(next_)
                self.w.lcd.setVisible(True)
                self.w.btn.setVisible(True)
                time.sleep(display_time)
            if not self.w.isVisible():
                return

class ColorThread(WindowThread):
    SLEEP_TIME = 0.1

    def __init__(self, w, positions):
        self.positions = positions
        self.opacity_step = config.getfloat('ColorRectangle', 'opacity_step')
        super(ColorThread, self).__init__(w)

    def run(self):
        starting_time = None
        previous_opacity = 0
        showing = False
        low_range = config.getint('Main', 'low_range')
        high_range = config.getint('Main', 'high_range')
        while self.w.isVisible():
            if showing:
                current_opacity = self.w.windowOpacity()
                if current_opacity < previous_opacity:
                    showing = False
                    continue
                self.w.setWindowOpacity(current_opacity + self.opacity_step)
                previous_opacity = current_opacity
            else:
                if starting_time is None:
                    position_key = random.choice(self.positions.keys())
                    position = self.positions[position_key]
                    self.w.move(*position)
                    starting_time = time.time() + random.randint(low_range, high_range)
                elif time.time() > starting_time:
                    starting_time = None
                    previous_opacity = 0
                    showing = True
                    logging.info('showing ColorWindow')
            time.sleep(self.SLEEP_TIME)


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
        topleft = QtGui.QApplication.desktop().screen().rect().topLeft()
        topright = QtGui.QApplication.desktop().screen().rect().topRight()
        bottomleft = QtGui.QApplication.desktop().screen().rect().bottomLeft()
        bottomright = QtGui.QApplication.desktop().screen().rect().bottomRight()
        self.positions = {'topleft': (topleft.x(), topleft.y()),
                 'topright': (topright.x() - self.width, topright.y()),
                 'bottomleft': (bottomleft.x(), bottomleft.y() - self.height),
                 'bottomright': (bottomright.x() - self.width, bottomright.y() - self.height),
                 }


        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)

    def mousePressEvent(self, event):
        if self.windowOpacity() < 0.05:
            return
        logging.info('user clicked on rectangle. opacity level: {}'.format(self.windowOpacity()))
        self.setWindowOpacity(0)

    def startTask(self):
        if self.isVisible():
            return
        self.setWindowOpacity(0)
        self.show()
        self.thread = ColorThread(self, self.positions)
        self.thread.start()

    def stopTask(self):
        self.running = False
        self.close()

def main():
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    trayWidget = QtGui.QWidget()
    trayIcon = SystemTrayIcon(QtGui.QIcon('icon.png'), trayWidget)

    trayIcon.show()
    logging.info('starting application')

    t2 = LogTailerThread()
    t2.start()

    task = config.get('Main', 'task')
    if task == 'color-rectangle':
        taskWindow = ColorWindow()
    elif task == 'sum-numbers':
        taskWindow = SumNumbersWindow()

    taskWindow.connect(t2, QtCore.SIGNAL('triggerTask'), taskWindow.startTask)
    taskWindow.connect(t2, QtCore.SIGNAL('stopTask'), taskWindow.stopTask)

    sys.exit(app.exec_())    

if __name__ == '__main__':
    main()