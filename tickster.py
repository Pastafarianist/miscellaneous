#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, platform
import csv

from PyQt5.QtCore import Qt, QEvent, QT_VERSION_STR, PYQT_VERSION_STR
from PyQt5.QtWidgets import (
    QWidget, QMainWindow, QAction, qApp, QApplication, QDesktopWidget, QMessageBox,
    QPushButton, QHBoxLayout, QVBoxLayout, QLineEdit, QFileDialog, QLabel, QStyle
)
from PyQt5.QtGui import QPixmap, QPainter, QPen

__version__ = '1.0'

csv_filename = 'coords.csv'
cross_size = 20
cross_colors = [Qt.red, Qt.green, Qt.blue, Qt.yellow]


def is_image_filename(fname):
    return os.path.splitext(fname)[1] in ('.png', '.jpg', '.jpeg', '.bmp')


def row_to_desc(row):
    # expected format: filename x1 y1 ... x4 y4 comment
    # some of (xi, yi) may be empty strings, meaning that those
    # coordinates were not selected
    filename = row[0]
    ticks_str = [(row[i], row[i + 1]) for i in range(1, 9, 2) if row[i]]
    ticks = [(int(x), int(y)) for x, y in ticks_str]
    comment = row[9]
    return ImageDescriptor(filename, ticks, comment)


def desc_to_row(desc):
    flat_ticks = []
    for tick in desc.ticks:
        flat_ticks.append(str(tick[0]))
        flat_ticks.append(str(tick[1]))
    flat_ticks.extend('' for _ in range(2 * (4 - len(desc.ticks))))
    return [desc.filename] + flat_ticks + [desc.comment]


class ImageDescriptor(object):
    def __init__(self, filename, ticks, comment):
        self.filename = filename
        self.ticks = ticks
        self.comment = comment


class CustomQLabel(QLabel):
    def paintEvent(self, event):
        super().paintEvent(event)

        qp = QPainter()
        qp.begin(self)
        # dirty, but the alternative is to have ugly calls to super() and qp.begin()
        self.parent().parent().drawTicks(qp)
        qp.end()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_dir = os.getcwd()
        self.descriptors = {}
        self.image_names = []
        self.current_index = 0
        self.pixmap = None
        self.scaledPixmap = None

        self.initUI()
        self.reloadDirectory()

    def initUI(self):
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        self.statusBar()

        # menu
        openIcon = qApp.style().standardIcon(QStyle.SP_DirOpenIcon)
        openFolder = QAction(openIcon, 'Open folder..', self)
        openFolder.setShortcut('Ctrl+O')
        openFolder.setStatusTip('Open a new folder with images')
        openFolder.triggered.connect(self.showDialog)

        exitIcon = qApp.style().standardIcon(QStyle.SP_DialogCloseButton)
        exitAction = QAction(exitIcon, '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFolder)
        fileMenu.addAction(exitAction)

        aboutMenu = menubar.addMenu('&About')
        aboutAction = QAction('&About', self)
        aboutAction.setShortcut('F1')
        aboutAction.setStatusTip('About the author')
        aboutAction.triggered.connect(self.about)
        aboutMenu.addAction(aboutAction)

        # window contents
        self.label = CustomQLabel(self)
        self.label.setMinimumSize(1, 1)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.mousePressEvent = self.handleImageClick
        self.label.installEventFilter(self)

        self.commentEdit = QLineEdit()
        self.commentEdit.setPlaceholderText("Enter comment here...")
        self.commentEdit.setDragEnabled(True)  # Allows drag-n-drop in the text field
        self.commentEdit.textChanged.connect(self.saveComment)

        prevIcon = qApp.style().standardIcon(QStyle.SP_ArrowBack)
        prevButton = QPushButton("Previous image")
        prevButton.setIcon(prevIcon)
        prevButton.setToolTip("PageUp")

        nextIcon = qApp.style().standardIcon(QStyle.SP_ArrowForward)
        nextButton = QPushButton("Next image")
        nextButton.setIcon(nextIcon)
        nextButton.setToolTip("PageDown")

        prevButton.clicked.connect(self.moveBackward)
        nextButton.clicked.connect(self.moveForward)

        hbox = QHBoxLayout()
        hbox.addWidget(self.commentEdit)
        hbox.addWidget(prevButton)
        hbox.addWidget(nextButton)

        vbox = QVBoxLayout()
        vbox.addWidget(self.label)
        vbox.addLayout(hbox)

        centralWidget.setLayout(vbox)

        # window itself
        self.setGeometry(300, 300, 800, 480)
        self.center()
        self.setWindowTitle('Tickster')
        self.show()

    def about(self):
        QMessageBox.about(self, "About",
                          """<b> Tickster version %s </b>
                <p>Copyright &copy; 2015-10-07 by Dmitry Nikulin.
                <ul>
                  <li>Python %s</li>
                  <li>PyQt %s</li>
                  <li>Qt %s</li>
                </ul>
                <p>Esc to exit, Ctrl+O to open a folder, PageUp/PageDown to navigate.</p>
                <p>Data is saved automatically in <b>%s</b> when switching between images,
                directories, and on exit.</p>""" %
                          (__version__, platform.python_version(), PYQT_VERSION_STR,
                           QT_VERSION_STR, csv_filename))

    def eventFilter(self, source, event):
        if source is self.label and event.type() == QEvent.Resize:
            # re-scaling the pixmap when the label resizes
            self.setPixmap()
        return super(MainWindow, self).eventFilter(source, event)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_PageDown:
            self.moveForward()
        elif event.key() == Qt.Key_PageUp:
            self.moveBackward()

    def closeEvent(self, event):
        if self.image_names:
            self.saveDescriptors()
        event.accept()

    def moveBackward(self):
        if self.image_names:
            self.saveDescriptors()

            if self.current_index == 0:
                self.current_index = len(self.image_names) - 1
            else:
                self.current_index -= 1
            self.reloadImage()
        else:
            self.statusBar().showMessage('No images loaded')

    def moveForward(self):
        if self.image_names:
            self.saveDescriptors()

            if self.current_index == len(self.image_names) - 1:
                self.current_index = 0
            else:
                self.current_index += 1
            self.reloadImage()
        else:
            self.statusBar().showMessage('No images loaded')

    def saveComment(self, text):
        if self.image_names:
            self.descriptors[self.image_names[self.current_index]].comment = text

    def showDialog(self):
        new_dir = QFileDialog.getExistingDirectory(self, 'Open image folder', self.current_dir)

        if new_dir:
            if self.image_names:
                self.saveDescriptors()

            self.current_dir = new_dir
            self.reloadDirectory()
        else:
            self.statusBar().showMessage('Nothing was selected')

    def reloadDirectory(self):
        self.image_names = []
        self.descriptors = {}
        self.current_index = 0

        self.label.clear()

        contents = os.listdir(self.current_dir)
        if csv_filename in contents:
            with open(os.path.join(self.current_dir, csv_filename)) as f:
                reader = csv.reader(f)
                for row in reader:
                    desc = row_to_desc(row)
                    self.descriptors[desc.filename] = desc

        self.image_names = [fname for fname in contents if is_image_filename(fname)]

        if self.image_names:
            self.image_names.sort()
            self.reloadImage()
        else:
            self.statusBar().showMessage('No images found in %s' % self.current_dir)

    def reloadImage(self):
        image_name = self.image_names[self.current_index]

        if image_name not in self.descriptors:
            self.descriptors[image_name] = ImageDescriptor(image_name, [], '')

        self.commentEdit.setText(self.descriptors[image_name].comment)
        # ticks are drawn elsewhere

        self.pixmap = QPixmap(os.path.join(self.current_dir, image_name))
        self.setPixmap()

        self.updateStatusBar()

    def setPixmap(self):
        if self.image_names:
            self.scaledPixmap = self.pixmap.scaled(
                self.label.size(), Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.label.setPixmap(self.scaledPixmap)

    def handleImageClick(self, event):
        if self.image_names:
            ticks = self.descriptors[self.image_names[self.current_index]].ticks
            pt = event.pos()
            x, y = pt.x(), pt.y()

            pixmap_x = (x * 2 + self.scaledPixmap.size().width() - self.label.size().width()) / 2
            pixmap_y = (y * 2 + self.scaledPixmap.size().height() - self.label.size().height()) / 2

            # adding +1 so that the indexes are 1-based instead of 0-based
            image_x = round(pixmap_x * self.pixmap.size().width() / self.scaledPixmap.size().width()) + 1
            image_y = round(pixmap_y * self.pixmap.size().height() / self.scaledPixmap.size().height()) + 1

            if 1 <= image_x <= self.pixmap.size().width() and 1 <= image_y <= self.pixmap.size().height():
                if len(ticks) >= 4:
                    del ticks[0]
                ticks.append((image_x, image_y))

            self.updateStatusBar()

        event.accept()
        self.label.repaint()

    def updateStatusBar(self):
        if self.image_names:
            desc = self.descriptors[self.image_names[self.current_index]]
            self.statusBar().showMessage('[%d / %d (%d)] %s | %r' % (
                self.current_index + 1, len(self.image_names),
                len(self.descriptors), desc.filename, desc.ticks
            ))

    def drawTicks(self, qp):
        if self.image_names:
            ticks = self.descriptors[self.image_names[self.current_index]].ticks
            for i, (image_x, image_y) in enumerate(ticks):
                pen = QPen(cross_colors[i], 2, Qt.SolidLine)
                qp.setPen(pen)

                # subtracting 1 because the coordinates are stored as 1-based
                # no need to care whether they fit in the image
                pixmap_x = (image_x - 1) * self.scaledPixmap.size().width() / self.pixmap.size().width()
                pixmap_y = (image_y - 1) * self.scaledPixmap.size().height() / self.pixmap.size().height()

                x = round((pixmap_x * 2 + self.label.size().width() - self.scaledPixmap.size().width()) / 2)
                y = round((pixmap_y * 2 + self.label.size().height() - self.scaledPixmap.size().height()) / 2)

                cross_t = y - (cross_size // 2)
                cross_b = y + (cross_size // 2)
                cross_l = x - (cross_size // 2)
                cross_r = x + (cross_size // 2)

                qp.drawLine(x, cross_t, x, cross_b)
                qp.drawLine(cross_l, y, cross_r, y)

    def saveDescriptors(self):
        # skipping empty descriptors
        rows = [desc_to_row(desc) for desc in self.descriptors.values() if (desc.ticks or desc.comment)]

        if rows:
            rows.sort(key=lambda row: row[0])
            with open(os.path.join(self.current_dir, csv_filename), 'w') as f:
                writer = csv.writer(f)
                writer.writerows(rows)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wnd = MainWindow()
    sys.exit(app.exec_())
