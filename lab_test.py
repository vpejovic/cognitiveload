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

class LogTailerThread(QtCore.QThread):
    TRIGGERS = ['Sync Slide', 'Hidden Pattern Question Slide', "Finding A's Question Slide", 'Gestalt Completion Question Slide',
    'Pursuit Test Question Slide', 'Number Comparison Question Slide', "Scattered X's Question Slide"]
    STOPPERS = ['Break Slide', 'TimeIsUp Slide', 'Rating Slide']
    QUITTERS = ['End Slide']
    def run(self):
        log_file = open(INPUT_FILE_PATH, 'r')

        for line in tailer.follow(log_file):
            self.parse_line(line)

    def parse_line(self, line):
        print(line)
        parts = line.split(', ')
        if len(parts) > 1:
            slide_name = parts[1].strip()
            if slide_name in self.TRIGGERS:
                self.trigger_task()
            elif slide_name in self.STOPPERS:
                self.stop_task()
            elif slide_name in self.QUITTERS:
                QtCore.QCoreApplication.exit()

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


class ColorThread(WindowThread):
    def __init__(self, w, positions):
        self.positions = positions
        self.opacity_step = config.getfloat('ColorRectangle', 'opacity_step')
        self.SLEEP_TIME = config.getfloat('ColorRectangle', 'opacity_time')
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

    taskWindow = ColorWindow()

    taskWindow.connect(t2, QtCore.SIGNAL('triggerTask'), taskWindow.startTask)
    taskWindow.connect(t2, QtCore.SIGNAL('stopTask'), taskWindow.stopTask)

    sys.exit(app.exec_())    

if __name__ == '__main__':
    import os.path
    # INPUT_FILE_PATH = sys.argv[1]
    # OUTPUT_FILE_PATH = sys.argv[2]
    LOG_DIR = config.get('Main', 'log_dir')
    INPUT_FILE_NAME = config.get('Main', 'input_file')
    OUTPUT_FILE_NAME = config.get('Main', 'output_file')
    INPUT_FILE_PATH = os.path.join(LOG_DIR, INPUT_FILE_NAME)
    OUTPUT_FILE_PATH = os.path.join(LOG_DIR, OUTPUT_FILE_NAME)
    logging.basicConfig(filename=OUTPUT_FILE_PATH, 
        level=logging.DEBUG, 
        format='%(created)i:%(message)s',
        )
    main()