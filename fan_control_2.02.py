# -*- coding: utf-8 -*-
#
# Author: ATRedline
# More information: https://github.com/ATRedline/ESP32_Fan_Control
# Version: 2.02
#
# This is application for ESP32 microcontroller to provide it abillity of controling system fans and ledlights.
# This application use MSIAfterburner.NET.dll by Nick Сonnors and need MSI Afterburner to be launched
# You can get MSIAfterburner.NET.dll here: https://forums.guru3d.com/threads/msi-afterburner-net-class-library.339656/
#
# Written with PyQt5 by Riverbank Computing Limited
#
# This file may be used under the terms of the GNU General Public License
# version 3.0 as published by the Free Software Foundation and appearing in
# the file LICENSE included in the packaging of this file.  Please review the
# following information to ensure the GNU General Public License version 3.0
# requirements will be met: http://www.gnu.org/copyleft/gpl.html.
#


import os
import pickle
import serial
import subprocess as sup
import sys
import threading
import time
import winreg
import webbrowser

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal, QByteArray
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import QWidget, QMessageBox, QSystemTrayIcon, QAction, QMenu, QApplication, QColorDialog


def thread(my_func):
    """Декоратор, запускающий функцию в отдельном потоке:"""
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()
    return wrapper


"""Раздел UI_________________________________________________________________________________________________________"""


class MainWindow(QWidget):
    """Тут прописывается форма главного окна"""

    def __init__(self):

        """Раздел шрифтов и цветов"""

        window_palette = QtGui.QPalette()  # Цветовая палитра главного окна
        brush = QtGui.QBrush(QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        window_palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        window_palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        unispace_font = QtGui.QFont()  # Шрифт мониторинга
        unispace_font.setFamily("Unispace")
        unispace_font.setPointSize(18)
        unispace_font.setBold(True)
        unispace_font.setWeight(75)
        webdings_font = QtGui.QFont()  # Шрифт пиктограмм
        webdings_font.setFamily('Webdings')
        self.webdings_font = QtGui.QFont()  # Шрифт пиктограмм
        self.webdings_font.setPointSize(7)
        self.webdings_font.setFamily('Webdings')
        self.window_font = QtGui.QFont()  # Шрифт окна
        self.window_font.setPointSize(9)
        self.window_font.setFamily("Segoe UI")
        self.palette = QtGui.QPalette()
        self.simple_font = QtGui.QFont()
        self.active_button_font = QtGui.QFont()
        self.active_button_font.setBold(True)

        """Раздел описанния характеристик окна"""

        QWidget.__init__(self)
        self.icon = QtGui.QIcon()
        self.icon.addPixmap(QtGui.QPixmap(fc_path + r'\resources\fan_control.ico'), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setObjectName("Form")
        self.resize(238, 247)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        self.setMaximumSize(238, 247)
        self.setWindowIcon(self.icon)
        self.setPalette(window_palette)
        self.setWindowTitle("Fan Control 2.02")

        """Раздел создания Tray-меню"""

        self.show_action = QAction("", self)
        self.led_action = QAction("", self)
        self.quit_action = QAction("", self)
        self.show_action.triggered.connect(self.show)
        self.led_action.triggered.connect(self.led_button)
        self.quit_action.triggered.connect(self.exit_func)
        tray_menu = QMenu()
        tray_menu.addAction(self.show_action)
        tray_menu.addAction(self.led_action)
        tray_menu.addAction(self.quit_action)
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.icon)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.doubleclick_func)

        """Раздел описания элементов окна"""

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        spacer1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        spacer2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        spacer3 = QtWidgets.QSpacerItem(30, 20, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)  # Tab 1
        spacer4 = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        spacer5 = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        spacer6 = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        spacer7 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        spacer8 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        spacer9 = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QtWidgets.QTabWidget(self)
        self.tabWidget.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setFont(self.window_font)
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_2.setObjectName("gridLayout_2")

        """Раздел описания элементов первой вкладки"""

        self.label_4 = QtWidgets.QLabel(self.tab)  # Этикетка имён ГПУ
        self.label_4.setPalette(self.text_palette([0, 170, 0]))
        self.label_4.setFont(unispace_font)
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.tab)  # Этикетка температур ГПУ
        self.label_5.setPalette(self.text_palette([255, 170, 0]))
        self.label_5.setFont(unispace_font)
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(self.tab)
        self.label_6.setPalette(self.text_palette([0, 155, 230]))
        self.label_6.setFont(unispace_font)
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.tab)
        self.label_7.setPalette(self.text_palette([255, 170, 0]))
        self.label_7.setFont(unispace_font)
        self.label_7.setObjectName("label_7")
        self.gridLayout_2.addWidget(self.label_7, 2, 2, 1, 1)
        self.gridLayout_2.addWidget(self.label_6, 2, 0, 1, 1)
        self.gridLayout_2.addWidget(self.label_5, 1, 2, 1, 1)
        self.gridLayout_2.addWidget(self.label_4, 1, 0, 1, 1)
        self.gridLayout_2.addItem(spacer, 0, 0, 1, 1)
        self.gridLayout_2.addItem(spacer1, 1, 3, 1, 1)
        self.gridLayout_2.addItem(spacer2, 3, 0, 1, 1)
        self.gridLayout_2.addItem(spacer3, 1, 1, 1, 1)
        self.tabWidget.addTab(self.tab, "")

        """Раздел описания элементов второй вкладки"""

        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label = QtWidgets.QLabel(self.tab_2)  # Этикетка "Язык"
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.tab_2)  # Этикетка "Статус подключения"
        self.label_2.setText("")
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.tab_2)  # Этикетка "Порт"
        self.label_3.setObjectName("label_3")
        self.label_8 = QtWidgets.QLabel(self.tab_2)  # Этикетка "Эмблема подключения"
        self.label_8.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label_8.setObjectName("label_8")
        self.label_8.setFont(webdings_font)
        self.checkBox = QtWidgets.QCheckBox(self.tab_2)  # Чекбокс автозапуска
        self.checkBox.setObjectName("checkBox")
        self.checkBox_2 = QtWidgets.QCheckBox(self.tab_2)  # Чекбокс подсветки
        self.checkBox_2.setObjectName("checkBox")
        self.comboBox = QtWidgets.QComboBox(self.tab_2)  # Комбобокс выбора порта
        self.comboBox.setObjectName("comboBox")
        self.pushButton = QtWidgets.QPushButton(self.tab_2)  # Кнопка "Подключиться"
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(self.tab_2)  # Кнопка выбора Русского языка
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_2.setText("РУС")
        self.pushButton_3 = QtWidgets.QPushButton(self.tab_2)  # Кнопка выбора Английского языка
        self.pushButton_3.setObjectName("pushButton_3")
        self.pushButton_3.setText("ENG")
        self.pushButton_4 = QtWidgets.QPushButton(self.tab_2)  # Кнопка расширенных настроек
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_5 = QtWidgets.QPushButton(self.tab_2)  # Кнопка выбора цвета подсветки
        self.pushButton_5.setFont(self.webdings_font)
        self.pushButton_5.setObjectName("pushButton_5")
        self.pushButton_5.setText("gggg")
        self.pushButton_5.setDisabled(True)
        self.line = QtWidgets.QFrame(self.tab_2)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout_3.addWidget(self.label, 5, 2, 1, 1)
        self.gridLayout_3.addWidget(self.pushButton, 1, 4, 1, 1)
        self.gridLayout_3.addWidget(self.checkBox, 8, 2, 1, 3)
        self.gridLayout_3.addWidget(self.comboBox, 1, 3, 1, 1)
        self.gridLayout_3.addWidget(self.label_2, 2, 3, 1, 1)
        self.gridLayout_3.addWidget(self.label_8, 2, 2, 1, 1)
        self.gridLayout_3.addWidget(self.pushButton_2, 5, 3, 1, 1)
        self.gridLayout_3.addWidget(self.label_3, 1, 2, 1, 1)
        self.gridLayout_3.addWidget(self.pushButton_3, 5, 4, 1, 1)
        self.gridLayout_3.addWidget(self.pushButton_4, 9, 2, 1, 3)
        self.gridLayout_3.addWidget(self.checkBox_2, 7, 2, 1, 2)
        self.gridLayout_3.addWidget(self.pushButton_5, 7, 4, 1, 1)
        self.gridLayout_3.addWidget(self.line, 3, 2, 1, 3)
        self.gridLayout_3.addItem(spacer4, 9, 2, 1, 1)
        self.gridLayout_3.addItem(spacer5, 6, 2, 1, 1)
        self.gridLayout_3.addItem(spacer6, 0, 2, 1, 1)
        self.gridLayout_3.addItem(spacer7, 11, 2, 1, 1)
        self.gridLayout_3.addItem(spacer8, 5, 5, 1, 1)
        self.gridLayout_3.addItem(spacer9, 4, 2, 1, 1)
        self.tabWidget.addTab(self.tab_2, "")
        self.gridLayout.addWidget(self.tabWidget, 1, 0, 1, 1)
        QtCore.QMetaObject.connectSlotsByName(self)

        """секция подпроцессов от ui"""

        self.processing = Processing()
        self.processing.output[QByteArray, QByteArray].connect(self.processing_feedback)
        self.processing_state = 0
        self.com_search = ComSearch()

    @thread
    def led_button(self, arg):
        """Функция обрабатывающая нажатие кнопки подсветки в трее"""
        processing_state = 0
        ledlights = settings_window.lineEdit_5.text()
        if ledlights:
            ledlights = int(ledlights)
        if ledlights:
            if self.processing_state:
                processing_state = 1
                self.processing.exiting = 1
                while self.processing_state:
                    time.sleep(0.1)
            if self.checkBox_2.isChecked():
                self.checkBox_2.setChecked(False)
            else:
                self.checkBox_2.setChecked(True)
            while not sp.busy:
                time.sleep(0.1)
            while sp.busy:
                time.sleep(0.1)
            if processing_state:
                self.processing.exiting = 0
                self.processing.start()

    @thread
    def exit_func(self, arg):
        """Функция закрытия программы"""
        self.tabWidget.setDisabled(True)
        settings_window.tabWidget.setDisabled(True)
        sp.answer_result = 1
        while sp.busy:
            time.sleep(0.1)
        if appSettings.settings['led_en'] and sp.opened_port:
            sp.send('cmnd;fn121b0;fn221b0;fn321b00;fn421b00;np0000000000000000')
            time.sleep(0.1)
            sp.answer_result = 1
        elif sp.opened_port:
            sp.send('cmnd;fn121b0;fn221b0;fn321b00;fn421b00;')
            time.sleep(0.1)
            sp.answer_result = 1
        while sp.busy:
            time.sleep(0.1)
        self.tray_icon.hide()
        QApplication.quit()

    def colour_button_palette(self, col):
        """Функция создания палитры цвета кнопок выбора цвета"""
        palette = self.palette
        brush = QtGui.QBrush(QColor(col))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QColor(col))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QColor(225, 225, 225))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        return palette

    def text_palette(self, col):
        """Функция, возвращающая объект палитры с заданным цветом"""
        palette = self.palette
        brush = QtGui.QBrush(QColor(col[0], col[1], col[2]))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        return palette

    def closeEvent(self, event):
        """Событие при нажатии на "Крестик" окна QT"""
        if settings_window.isHidden():
            self.tabWidget.setCurrentIndex(0)
        self.hide()
        event.ignore()

    def processing_feedback(self, gpu, cpu):
        """фукция обновления мониторинга по сигналу из processing"""
        gpu_data = gpu.data().decode('utf-8')
        cpu_data = cpu.data().decode('utf-8')
        if gpu_data == 'show':
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            self.label_5.setText(gpu_data)
            self.label_7.setText(cpu_data)
        pass

    def doubleclick_func(self, reason):
        """Действие двойного щелчка иконки в трее"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()


class SettingsWindow(QWidget):
    """Тут прописывается форма окна настроек"""

    def __init__(self):

        """Раздел описанния характеристик окна"""

        QWidget.__init__(self)
        self.setObjectName("Form2")
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        self.setWindowIcon(ui.icon)
        self.resize(327, 348)
        self.setMaximumSize(327, 348)
        self.testing_process = 0
        self.last_tab = 0

        "Раздел описания элементов окна"

        spacer = QtWidgets.QSpacerItem(20, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        spacer1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        spacer2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        spacer3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        spacer4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        spacer5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        spacer6 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        spacer7 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        spacer8 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        spacer9 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        spacer10 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        spacer11 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        spacer12 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        spacer13 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QtWidgets.QTabWidget(self)
        self.tabWidget.setFont(ui.window_font)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setTabPosition(QtWidgets.QTabWidget.East)
        self.tabWidget.setUsesScrollButtons(False)

        "Раздел описания элементов первой вентиляторов"

        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.line = QtWidgets.QFrame(self.tab_2)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.lineEdit = QtWidgets.QLineEdit(self.tab_2)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHeightForWidth(self.lineEdit.sizePolicy().hasHeightForWidth())
        self.lineEdit.setSizePolicy(size_policy)
        self.lineEdit.setMaximumSize(QtCore.QSize(60, 16777215))
        self.lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit.setInputMask('9' * 2)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.tab_2)
        size_policy.setHeightForWidth(self.lineEdit_2.sizePolicy().hasHeightForWidth())
        self.lineEdit_2.setSizePolicy(size_policy)
        self.lineEdit_2.setMaximumSize(QtCore.QSize(60, 16777215))
        self.lineEdit_2.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.lineEdit_2.setInputMask('9' * 2)
        self.lineEdit_3 = QtWidgets.QLineEdit(self.tab_2)
        size_policy.setHeightForWidth(self.lineEdit_3.sizePolicy().hasHeightForWidth())
        self.lineEdit_3.setSizePolicy(size_policy)
        self.lineEdit_3.setMaximumSize(QtCore.QSize(60, 16777215))
        self.lineEdit_3.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.lineEdit_3.setInputMask('9' * 2)
        self.lineEdit_4 = QtWidgets.QLineEdit(self.tab_2)
        self.lineEdit_4.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.lineEdit_4.setText('21')
        self.lineEdit_4.setInputMask('9' * 2)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        self.lineEdit_4.setSizePolicy(size_policy)
        self.lineEdit_7 = QtWidgets.QLineEdit(self.tab_2)
        size_policy.setHeightForWidth(self.lineEdit_7.sizePolicy().hasHeightForWidth())
        self.lineEdit_7.setSizePolicy(size_policy)
        self.lineEdit_7.setMaximumSize(QtCore.QSize(60, 16777215))
        self.lineEdit_7.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_7.setObjectName("lineEdit_7")
        self.lineEdit_7.setInputMask('9' * 2)
        self.label = QtWidgets.QLabel(self.tab_2)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.tab_2)
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.tab_2)
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.tab_2)
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.tab_2)
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(self.tab_2)
        self.label_6.setObjectName("label_6")
        self.label_8 = QtWidgets.QLabel(self.tab_2)
        self.label_8.setObjectName("label_8")
        self.label_16 = QtWidgets.QLabel(self.tab_2)
        self.label_16.setObjectName("label_16")
        self.pushButton = QtWidgets.QPushButton(self.tab_2)
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_2.setMaximumSize(QtCore.QSize(80, 16777215))
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_3 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_3.setMaximumSize(QtCore.QSize(80, 16777215))
        self.pushButton_3.setObjectName("pushButton_3")
        self.pushButton_4 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_4.setMaximumSize(QtCore.QSize(80, 16777215))
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_5 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_5.setMaximumSize(QtCore.QSize(80, 16777215))
        self.pushButton_5.setObjectName("pushButton_5")
        self.pushButton_6 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_6.setMaximumSize(QtCore.QSize(80, 16777215))
        self.pushButton_6.setObjectName("pushButton_6")
        self.pushButton_8 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_8.setObjectName("pushButton_8")
        self.horizontalSlider = QtWidgets.QSlider(self.tab_2)
        self.horizontalSlider.setMaximum(100)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.checkBox = QtWidgets.QCheckBox(self.tab_2)
        self.checkBox.setObjectName("checkBox")
        self.checkBox.setText("CPU")
        self.checkBox_2 = QtWidgets.QCheckBox(self.tab_2)
        self.checkBox_2.setObjectName("checkBox_2")
        self.checkBox_2.setChecked(True)
        self.checkBox_2.setText("GPU")
        self.checkBox_3 = QtWidgets.QCheckBox(self.tab_2)
        self.checkBox_3.setObjectName("checkBox")
        self.checkBox_4 = QtWidgets.QCheckBox(self.tab_2)
        self.checkBox_4.setObjectName("checkBox_4")
        self.checkBox_4.setText('3-pin')
        self.comboBox = QtWidgets.QComboBox(self.tab_2)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHeightForWidth(self.comboBox.sizePolicy().hasHeightForWidth())
        self.comboBox.setSizePolicy(size_policy)
        self.comboBox.setMinimumSize(QtCore.QSize(60, 16777215))
        self.comboBox.setObjectName("comboBox")
        self.comboBox.clear()
        self.comboBox.addItems(['1', '2', '3', '4'])
        self.horizontalLayout_2.addWidget(self.checkBox)
        self.horizontalLayout_2.addWidget(self.checkBox_2)
        self.gridLayout_4.addWidget(self.pushButton_2, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.pushButton_3, 1, 0, 1, 1)
        self.gridLayout_4.addWidget(self.pushButton_4, 2, 0, 1, 1)
        self.gridLayout_4.addWidget(self.pushButton_5, 3, 0, 1, 1)
        self.gridLayout_4.addWidget(self.pushButton_6, 4, 0, 1, 1)
        self.gridLayout_4.addWidget(self.lineEdit, 1, 1, 1, 1)
        self.gridLayout_4.addWidget(self.label_3, 0, 2, 1, 1)
        self.gridLayout_4.addWidget(self.label_4, 1, 2, 1, 1)
        self.gridLayout_4.addWidget(self.label_5, 2, 2, 1, 1)
        self.gridLayout_4.addWidget(self.label_6, 3, 2, 1, 1)
        self.gridLayout_4.addWidget(self.label_16, 4, 2, 1, 1)
        self.gridLayout_4.addWidget(self.lineEdit_2, 2, 1, 1, 1)
        self.gridLayout_4.addWidget(self.lineEdit_3, 3, 1, 1, 1)
        self.gridLayout_4.addWidget(self.lineEdit_7, 4, 1, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout_4, 10, 0, 1, 4)
        self.gridLayout_3.addWidget(self.horizontalSlider, 8, 0, 1, 4)
        self.gridLayout_3.addLayout(self.horizontalLayout_2, 5, 0, 1, 1)
        self.gridLayout_3.addWidget(self.line, 3, 0, 1, 4)
        self.gridLayout_3.addWidget(self.label, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.label_8, 4, 1, 1, 1)
        self.gridLayout_3.addWidget(self.label_2, 4, 0, 1, 1)
        self.gridLayout_3.addWidget(self.comboBox, 0, 1, 1, 1)
        self.gridLayout_3.addWidget(self.lineEdit_4, 5, 1, 1, 1)
        self.gridLayout_3.addWidget(self.checkBox_3, 1, 0, 1, 1)
        self.gridLayout_3.addWidget(self.checkBox_4, 1, 1, 1, 1)
        self.gridLayout_3.addWidget(self.pushButton, 9, 0, 1, 3)
        self.gridLayout_3.addWidget(self.pushButton_8, 9, 3, 1, 1)
        self.gridLayout_3.addItem(spacer, 2, 0, 1, 1)
        self.gridLayout_3.addItem(spacer1, 14, 0, 1, 1)
        self.gridLayout_3.addItem(spacer2, 0, 3, 1, 1)
        self.tabWidget.addTab(self.tab_2, "")

        "Раздел описания элементов вкладки подсветки"

        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.tab_3)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.comboBox_2 = QtWidgets.QComboBox(self.tab_3)
        self.comboBox_2.setObjectName("comboBox_2")
        self.comboBox_3 = QtWidgets.QComboBox(self.tab_3)
        self.comboBox_3.setObjectName("comboBox_3")
        self.comboBox_3.addItems(['1', '2', '3', '4'])
        self.label_9 = QtWidgets.QLabel(self.tab_3)
        self.label_9.setObjectName("label_9")
        self.label_10 = QtWidgets.QLabel(self.tab_3)
        self.label_10.setObjectName("label_10")
        self.label_11 = QtWidgets.QLabel(self.tab_3)
        self.label_11.setObjectName("label_11")
        self.label_12 = QtWidgets.QLabel(self.tab_3)
        self.label_12.setObjectName("label_12")
        self.label_13 = QtWidgets.QLabel(self.tab_3)
        self.label_13.setObjectName("label_13")
        self.label_14 = QtWidgets.QLabel(self.tab_3)
        self.label_14.setObjectName("label_14")
        self.lineEdit_5 = QtWidgets.QLineEdit(self.tab_3)
        self.lineEdit_5.setInputMethodHints(QtCore.Qt.ImhNone)
        self.lineEdit_5.setMaxLength(3)
        self.lineEdit_5.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_5.setObjectName("lineEdit_5")
        self.lineEdit_5.setInputMask('9' * 3)
        self.checkBox_5 = QtWidgets.QCheckBox(self.tab_3)
        self.checkBox_5.setObjectName("checkBox_5")
        self.checkBox_6 = QtWidgets.QCheckBox(self.tab_3)
        self.checkBox_6.setObjectName("checkBox_6")
        self.checkBox_7 = QtWidgets.QCheckBox(self.tab_3)
        self.checkBox_7.setObjectName("checkBox_7")
        self.pushButton_9 = QtWidgets.QPushButton(self.tab_3)
        self.pushButton_9.setFont(ui.webdings_font)
        self.pushButton_9.setObjectName("pushButton_9")
        self.pushButton_9.setText("gggg")
        self.pushButton_10 = QtWidgets.QPushButton(self.tab_3)
        self.pushButton_10.setObjectName("pushButton_10")
        self.pushButton_12 = QtWidgets.QPushButton(self.tab_3)
        self.pushButton_12.setFont(ui.webdings_font)
        self.pushButton_12.setObjectName("pushButton_12")
        self.pushButton_12.setText("gggg")
        self.pushButton_12.setDisabled(True)
        self.pushButton_13 = QtWidgets.QPushButton(self.tab_3)
        self.pushButton_13.setFont(ui.webdings_font)
        self.pushButton_13.setObjectName("pushButton_13")
        self.pushButton_13.setText("gggg")
        self.pushButton_13.setDisabled(True)
        self.pushButton_14 = QtWidgets.QPushButton(self.tab_3)
        self.pushButton_14.setFont(ui.webdings_font)
        self.pushButton_14.setObjectName("pushButton_14")
        self.pushButton_14.setText("gggg")
        self.pushButton_14.setDisabled(True)
        self.horizontalSlider_2 = QtWidgets.QSlider(self.tab_3)
        self.horizontalSlider_2.setMaximum(100)
        self.horizontalSlider_2.setSingleStep(10)
        self.horizontalSlider_2.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_2.setObjectName("horizontalSlider_2")
        self.horizontalSlider_4 = QtWidgets.QSlider(self.tab_3)
        self.horizontalSlider_4.setMaximum(100)
        self.horizontalSlider_4.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_4.setObjectName("horizontalSlider_4")
        self.gridLayout_5.addWidget(self.label_9, 0, 1, 1, 1)
        self.gridLayout_5.addWidget(self.label_10, 5, 1, 1, 1)
        self.gridLayout_5.addWidget(self.label_11, 8, 1, 1, 1)
        self.gridLayout_5.addWidget(self.label_12, 9, 1, 1, 1)
        self.gridLayout_5.addWidget(self.label_13, 13, 1, 1, 1)
        self.gridLayout_5.addWidget(self.label_14, 2, 1, 1, 1)
        self.gridLayout_5.addWidget(self.comboBox_2, 8, 2, 1, 2)
        self.gridLayout_5.addWidget(self.comboBox_3, 13, 2, 1, 2)
        self.gridLayout_5.addWidget(self.checkBox_5, 14, 1, 1, 1)
        self.gridLayout_5.addWidget(self.lineEdit_5, 0, 2, 1, 2)
        self.gridLayout_5.addWidget(self.checkBox_6, 15, 1, 1, 1)
        self.gridLayout_5.addWidget(self.checkBox_7, 16, 1, 1, 1)
        self.gridLayout_5.addWidget(self.pushButton_9, 5, 2, 1, 2)
        self.gridLayout_5.addWidget(self.pushButton_10, 11, 1, 1, 3)
        self.gridLayout_5.addWidget(self.pushButton_12, 14, 2, 1, 2)
        self.gridLayout_5.addWidget(self.pushButton_13, 15, 2, 1, 2)
        self.gridLayout_5.addWidget(self.pushButton_14, 16, 2, 1, 2)
        self.gridLayout_5.addWidget(self.horizontalSlider_2, 3, 1, 1, 3)
        self.gridLayout_5.addWidget(self.horizontalSlider_4, 9, 2, 1, 2)
        self.gridLayout_5.addItem(spacer3, 17, 1, 1, 1)
        self.gridLayout_5.addItem(spacer4, 10, 1, 1, 1)
        self.gridLayout_5.addItem(spacer5, 4, 1, 1, 1)
        self.gridLayout_5.addItem(spacer6, 0, 0, 1, 1)
        self.gridLayout_5.addItem(spacer7, 1, 1, 1, 1)
        self.gridLayout_5.addItem(spacer8, 6, 1, 1, 1)
        self.gridLayout_5.addItem(spacer9, 12, 1, 1, 1)
        self.gridLayout_5.addItem(spacer10, 0, 4, 1, 1)
        self.tabWidget.addTab(self.tab_3, "")

        "Раздел описания элементов вкладки дополнительно"

        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.gridLayout_7 = QtWidgets.QGridLayout(self.tab_4)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.line_2 = QtWidgets.QFrame(self.tab_4)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.label_15 = QtWidgets.QLabel(self.tab_4)
        self.label_15.setTextFormat(QtCore.Qt.AutoText)
        self.label_15.setWordWrap(True)
        self.label_15.setObjectName("label_15")
        self.label_17 = QtWidgets.QLabel(self.tab_4)
        self.label_17.setObjectName("label_17")
        self.lineEdit_6 = QtWidgets.QLineEdit(self.tab_4)
        self.lineEdit_6.setObjectName("lineEdit_6")
        self.lineEdit_6.setInputMask('9' * 2)
        self.pushButton_15 = QtWidgets.QPushButton(self.tab_4)
        self.pushButton_15.setObjectName("pushButton_15")
        self.pushButton_16 = QtWidgets.QPushButton(self.tab_4)
        self.pushButton_16.setObjectName("pushButton_16")
        self.gridLayout_7.addItem(spacer13, 6, 0, 1, 1)
        self.gridLayout_7.addWidget(self.line_2, 2, 0, 1, 3)
        self.gridLayout_7.addWidget(self.label_15, 5, 0, 1, 3)
        self.gridLayout_7.addWidget(self.label_17, 0, 0, 1, 1)
        self.gridLayout_7.addWidget(self.lineEdit_6, 0, 1, 1, 1)
        self.gridLayout_7.addWidget(self.pushButton_15, 3, 0, 1, 3)
        self.gridLayout_7.addWidget(self.pushButton_16, 0, 2, 1, 1)
        self.tabWidget.addTab(self.tab_4, "")

        "Раздел описания элементов вкладки информация"

        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_7 = QtWidgets.QLabel(self.tab)
        self.label_7.setObjectName("label_7")
        self.label_7.setPixmap(QPixmap(fc_path + r'\resources\esp32.png'))
        self.pushButton_11 = QtWidgets.QPushButton(self.tab)
        self.pushButton_11.setObjectName("pushButton_11")
        self.pushButton_7 = QtWidgets.QPushButton(self.tab)
        self.pushButton_7.setObjectName("pushButton_7")
        self.gridLayout_2.addItem(spacer11, 1, 0, 1, 1)
        self.gridLayout_2.addItem(spacer12, 1, 2, 1, 1)
        self.gridLayout_2.addWidget(self.label_7, 1, 1, 1, 1)
        self.gridLayout_2.addWidget(self.pushButton_11, 0, 0, 1, 3)
        self.gridLayout_2.addWidget(self.pushButton_7, 2, 0, 1, 3)
        self.tabWidget.addTab(self.tab, "")
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.tab_icon = QtGui.QIcon()
        self.tab_icon.addPixmap(QtGui.QPixmap(fc_path + r'\resources\info_bar.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.tabWidget.setTabIcon(self.tabWidget.indexOf(self.tab),self.tab_icon)

    def closeEvent(self, event):
        """Событие при нажатии на "Крестик" окна настроек"""
        if sp.opened_port:
            ui.tabWidget.setCurrentIndex(0)
        if self.testing_process:
            self.testing_process = 0
        self.last_tab = 0
        appSettings.save_lines()
        appSettings.save_aditional()
        appSettings.save_led_settings()
        appSettings.save()
        ui.tabWidget.setEnabled(True)
        if ui.isHidden():
            ui.show()


"""Раздел классов приложения_________________________________________________________________________________________"""


class AppSettings:
    """В данном классе хранятся настройки приложения, функции их сохранения и загрузки с жёсткого диска,
    функции обновления интерфейса и смены языка"""

    def __init__(self):

        self.settings = dict(lang='ru', com='', line_1=True, line_2=False, line_3=False, line_4=False,
                             l1_control=0, l2_control=0, l3_control=0, l4_control=0,
                             l1_min='0', l1_pos1=['50', '60'], l1_pos2=['70', '65'], l1_pos3=['90', '70'],
                             l1_pos4=['100', '80'], l1_3pin=False, l1_freq='21',
                             l2_min='0', l2_pos1=['50', '60'], l2_pos2=['70', '65'], l2_pos3=['90', '70'],
                             l2_pos4=['100', '80'], l2_3pin=False, l2_freq='21',
                             l3_min='0', l3_pos1=['50', '60'], l3_pos2=['70', '65'], l3_pos3=['90', '70'],
                             l3_pos4=['100', '80'], l3_3pin=False, l3_freq='21',
                             l4_min='0', l4_pos1=['50', '60'], l4_pos2=['70', '65'], l4_pos3=['90', '70'],
                             l4_pos4=['100', '80'], l4_3pin=False, l4_freq='21',
                             led_en=0, ledlights='0', led_bright=90, led_col='#FFFF5A', overheat1='#FFAA00',
                             overheat1_en=0, overheat2='#FF5500', overheat2_en=0, overheat3='#FF0000',
                             overheat3_en=0, led_ef=0, led_ef_sp=0, led_for_line=1, boost_zone = '50')
        self.cl = '1'
        self.lang_string_ru = ['Мониторинг', 'Настройки', 'Порт:', 'Подкл.', 'Язык:', 'Автозапуск приложения',
                               'Расширенные настройки', 'Вентиляторы', 'Дополнительно', 'Линия управления:', 'Включена',
                               'Контроль за:', '{0}% - Тест', 'Минимальные обороты', 'Первая зона',
                               'Вторая зона', 'Третья зона', 'Проект Fan Control на GitHub',
                               'Сказать "СПАСИБО" автору\n(Yandex Money)', 'Подключено!', 'Нет связи!', 'Ошибка',
                               'Запущенный процесс MSI Afterburner не найден!', 'Частота, kHz:', 'Стоп',
                               'Подсветка LED', 'Четвёртая зона', 'Подсветка', 'Колличество точек:', 'Яркость',
                               '(нет)', 'Цвет:', 'Эффекты', 'Скорость', 'Тест', 'Индикация зоны 2-3',
                               'Индикация зоны 3-4', 'Индикация зоны 4+', 'Индикация линии PWM:', 'Показать', 'Выход',
                               'Подсветка', 'Применить', 'Сервисный режим', 'Зона буста 3-pin:',
                               'В сервисном режиме ESP32 не будет загружать скрипт Fan Control! Для выхода необходимо удалить файл "service" при помощи утилиты Espy']
        self.lang_string_en = ['Monitoring', 'Settings', 'Port:', 'Connect', 'Lang:', 'Start with Windows',
                               'Advanced settings', 'FANs', 'Advanced', 'PWM line:', 'Enabled', 'Control for:',
                               '0% - Test', 'Minimal PWM', ' Zone One', ' Zone Two', ' Zone Three',
                               'Fan Control Project on Github', 'Donation (Yandex Money)', 'Connected!',
                               'No connection!', 'Error', 'No running MSI Afterburner process was found',
                               'Frequency, kHz:', 'Stop', 'Backlight', ' Zone Four', 'LED', 'Number of LEDs:',
                               'Brightness', '(static)', 'Colour:', 'Effects', 'Speed', 'Test', 'Zone 2-3 indication',
                               'Zone 3-4 indication', 'Zone 4+ indication', 'Indication of line:', 'Show', 'Exit',
                               'Ledlight', 'Apply', 'Service mode', '3-pin boost zone:',
                               'In service mode ESP32 will not inicialize Fan Control scrypt! To exit of it, you need to remove file "service" with Espy utility']
        self.lang_string = []


    def save(self):
        """Функция сохраняющая настройки программы в файл"""
        f = open(fc_path + 'fan_control.cfg', 'wb')
        pickle.dump(self.settings, f)
        f.close()

    def load(self):
        """Функция загрузки настроек из файла, вызывается при инициализации прораммы"""
        if not os.path.isfile(fc_path + 'fan_control.cfg'):  # Проверяем существования файла конфигурации
            ui.tabWidget.setCurrentIndex(1)
            ui.com_search.start()
        else:
            new_settings = ''
            try:
                r = open(fc_path + 'fan_control.cfg', 'rb')  # Если файл конфигурации существует считываем настройки
                new_settings = pickle.load(r)
                r.close()
            except EOFError:  # Если файл поврежден и не открывается - удаляем и делаем чистый запуск
                os.remove(fc_path + 'fan_control.cfg')
                ui.tabWidget.setCurrentIndex(1)
            if new_settings:
                self.settings = new_settings
                ui.comboBox.clear()
                ui.comboBox.addItem(self.settings['com'])
        if 'FanControl' in autoload_values():
            ui.checkBox.setChecked(True)
        ui.pushButton_5.setPalette(ui.colour_button_palette(self.settings['led_col']))
        settings_window.pushButton_9.setPalette(ui.colour_button_palette(self.settings['led_col']))
        settings_window.pushButton_12.setPalette(ui.colour_button_palette(self.settings['overheat1']))
        settings_window.pushButton_13.setPalette(ui.colour_button_palette(self.settings['overheat2']))
        settings_window.pushButton_14.setPalette(ui.colour_button_palette(self.settings['overheat3']))
        settings_window.lineEdit_5.setText(self.settings['ledlights'])
        try:  # Данная конструкция применяется, т.к. настройка введена ПОСЛЕ релиза, а в настройки добавлена новая опция
            settings_window.lineEdit_6.setText(self.settings['boost_zone'])
        except:
            settings_window.lineEdit_6.setText('50')
        settings_window.horizontalSlider_2.setValue(self.settings['led_bright'])
        settings_window.horizontalSlider_4.setValue(self.settings['led_ef_sp'])
        settings_window.comboBox_3.setCurrentIndex(self.settings['led_for_line'] - 1)
        led_elements_control()
        if self.settings['overheat1_en']:
            settings_window.checkBox_5.setChecked(True)
            settings_window.pushButton_12.setEnabled(True)
        if self.settings['overheat2_en']:
            settings_window.checkBox_6.setChecked(True)
            settings_window.pushButton_13.setEnabled(True)
        if self.settings['overheat3_en']:
            settings_window.checkBox_7.setChecked(True)
            settings_window.pushButton_14.setEnabled(True)
        self.set_lang()
        settings_window.comboBox_2.setCurrentIndex(self.settings['led_ef'])
        if not settings_window.comboBox_2.currentIndex():
            settings_window.label_12.setDisabled(True)
            settings_window.horizontalSlider_4.setDisabled(True)

    def save_lines(self):
        """Функция сохраняющая состояние выбранной линии PWM"""
        if settings_window.checkBox.isChecked() and settings_window.checkBox_2.isChecked():
            control = 2
        elif settings_window.checkBox.isChecked() and not settings_window.checkBox_2.isChecked():
            control = 1
        elif settings_window.checkBox_2.isChecked() and not settings_window.checkBox.isChecked():
            control = 0
        else:
            control = -1
        line = settings_window.checkBox_3.isChecked()
        line_3pin = settings_window.checkBox_4.isChecked()
        line_freq = settings_window.lineEdit_4.text()
        if not line_freq:
            line_freq = '21'
        elif line_freq == '0':
            line_freq = '1'
        elif int(line_freq) > 61:
            line_freq = '61'
        min_pwm = settings_window.pushButton_2.text()[:-1]
        pos1 = [settings_window.pushButton_3.text()[:-1], settings_window.lineEdit.text()]
        pos2 = [settings_window.pushButton_4.text()[:-1], settings_window.lineEdit_2.text()]
        pos3 = [settings_window.pushButton_5.text()[:-1], settings_window.lineEdit_3.text()]
        pos4 = [settings_window.pushButton_6.text()[:-1], settings_window.lineEdit_7.text()]
        new_values = {'line_{0}'.format(self.cl): line, 'l{0}_control'.format(self.cl): control,
                      'l{0}_min'.format(self.cl): min_pwm, 'l{0}_pos1'.format(self.cl): pos1,
                      'l{0}_pos2'.format(self.cl): pos2, 'l{0}_pos3'.format(self.cl): pos3,
                      'l{0}_pos4'.format(self.cl): pos4, 'l{0}_3pin'.format(self.cl): line_3pin,
                      'l{0}_freq'.format(self.cl): line_freq}
        self.settings.update(new_values)

    def save_led_settings(self):
        """Функция частично сохраняющая настройки подсветки LED"""
        leds = settings_window.lineEdit_5.text().replace(' ', '')
        if leds:
            if self.settings['ledlights'] != settings_window.lineEdit_5.text():
                self.settings['ledlights'] = settings_window.lineEdit_5.text()
                if not int(appSettings.settings['ledlights']):
                    appSettings.settings['led_en'] = False
        else:
            settings_window.lineEdit_5.setText(self.settings['ledlights'])
        self.settings['led_ef'] = settings_window.comboBox_2.currentIndex()
        self.settings['led_bright'] = settings_window.horizontalSlider_2.value()
        self.settings['led_ef_sp'] = settings_window.horizontalSlider_4.value()
        self.settings['led_for_line'] = int(settings_window.comboBox_3.currentText())
        led_elements_control()

    def save_aditional(self):
        boost_zone = settings_window.lineEdit_6.text()
        if not boost_zone:
            boost_zone = '10'
            settings_window.lineEdit_6.setText(boost_zone)
        elif boost_zone == '0':
            boost_zone = '10'
            settings_window.lineEdit_6.setText(boost_zone)
        elif int(boost_zone) > 90:
            boost_zone = '90'
            settings_window.lineEdit_6.setText(boost_zone)
        self.settings.update({'boost_zone':boost_zone})

    def set_values(self, line):
        """Функция устанавливающая значения формы настроек в зависимости от выбранной линии PWM"""
        settings_window.checkBox_3.setChecked(self.settings['line_{0}'.format(line)])
        settings_window.checkBox_4.setChecked(self.settings['l{0}_3pin'.format(line)])
        line_state()
        if self.settings['l{0}_control'.format(line)] == 2:
            settings_window.checkBox.setChecked(True)
            settings_window.checkBox_2.setChecked(True)
        elif self.settings['l{0}_control'.format(line)] == 1:
            settings_window.checkBox.setChecked(True)
            settings_window.checkBox_2.setChecked(False)
        else:
            settings_window.checkBox.setChecked(False)
            settings_window.checkBox_2.setChecked(True)

        settings_window.pushButton_2.setText(self.settings['l{0}_min'.format(line)] + '%')
        settings_window.pushButton_3.setText(self.settings['l{0}_pos1'.format(line)][0] + '%')
        settings_window.pushButton_4.setText(self.settings['l{0}_pos2'.format(line)][0] + '%')
        settings_window.pushButton_5.setText(self.settings['l{0}_pos3'.format(line)][0] + '%')
        settings_window.pushButton_6.setText(self.settings['l{0}_pos4'.format(line)][0] + '%')
        settings_window.lineEdit.setText(self.settings['l{0}_pos1'.format(line)][1])
        settings_window.lineEdit_2.setText(self.settings['l{0}_pos2'.format(line)][1])
        settings_window.lineEdit_3.setText(self.settings['l{0}_pos3'.format(line)][1])
        settings_window.lineEdit_7.setText(self.settings['l{0}_pos4'.format(line)][1])
        settings_window.lineEdit_4.setText(self.settings['l{0}_freq'.format(line)])

    def set_lang(self):
        """Функция пробрасывающая языковые строки в интерфейс. Языковая строка определяется по ключу lang в settings"""
        if self.settings['lang'] == 'ru':
            self.lang_string = self.lang_string_ru
            ui.pushButton_2.setFont(ui.active_button_font)
            ui.pushButton_3.setFont(QtGui.QFont())
        else:
            self.lang_string = self.lang_string_en
            ui.pushButton_2.setFont(QtGui.QFont())
            ui.pushButton_3.setFont(ui.active_button_font)
        effects = [self.lang_string[30], '1', '2', '3', '4']
        ui.tabWidget.setTabText(ui.tabWidget.indexOf(ui.tab), self.lang_string[0])
        ui.tabWidget.setTabText(ui.tabWidget.indexOf(ui.tab_2), self.lang_string[1])
        ui.label.setText(self.lang_string[4])
        ui.label_3.setText(self.lang_string[2])
        ui.pushButton.setText(self.lang_string[3])
        ui.pushButton_4.setText(self.lang_string[6])
        ui.checkBox.setText(self.lang_string[5])
        ui.checkBox_2.setText(self.lang_string[25])
        ui.show_action.setText(self.lang_string[39])
        ui.led_action.setText(self.lang_string[41])
        ui.quit_action.setText(self.lang_string[40])
        settings_window.setWindowTitle(self.lang_string[1])
        settings_window.comboBox_2.addItems(effects)
        settings_window.pushButton.setText(self.lang_string[12].format('0'))
        settings_window.pushButton_7.setText(self.lang_string[18])
        settings_window.pushButton_8.setText(self.lang_string[24])
        settings_window.pushButton_10.setText(self.lang_string[34])
        settings_window.pushButton_11.setText(self.lang_string[17])
        settings_window.pushButton_15.setText(self.lang_string[43])
        settings_window.pushButton_16.setText(self.lang_string[42])
        settings_window.tabWidget.setTabText(settings_window.tabWidget.indexOf(settings_window.tab_4),
                                             self.lang_string[8])
        settings_window.tabWidget.setTabText(settings_window.tabWidget.indexOf(settings_window.tab_2),
                                             self.lang_string[7])
        settings_window.tabWidget.setTabText(settings_window.tabWidget.indexOf(settings_window.tab_3),
                                             self.lang_string[27])
        settings_window.label.setText(self.lang_string[9])
        settings_window.label_2.setText(self.lang_string[11])
        settings_window.checkBox_3.setText(self.lang_string[10])
        settings_window.checkBox_5.setText(self.lang_string[35])
        settings_window.checkBox_6.setText(self.lang_string[36])
        settings_window.checkBox_7.setText(self.lang_string[37])
        settings_window.label_3.setText(self.lang_string[13])
        settings_window.label_4.setText(self.lang_string[14])
        settings_window.label_5.setText(self.lang_string[15])
        settings_window.label_6.setText(self.lang_string[16])
        settings_window.label_8.setText(self.lang_string[23])
        settings_window.label_9.setText(self.lang_string[28])
        settings_window.label_10.setText(self.lang_string[31])
        settings_window.label_11.setText(self.lang_string[32])
        settings_window.label_13.setText(self.lang_string[38])
        settings_window.label_15.setText(self.lang_string[45])
        settings_window.label_16.setText(self.lang_string[26])
        settings_window.label_17.setText(self.lang_string[44])
        settings_window.label_12.setText('{0} ({1}):'.format(self.lang_string[33],
                                                             settings_window.horizontalSlider_4.value()))
        settings_window.label_14.setText('{0} ({1}):'.format(self.lang_string[29],
                                                             settings_window.horizontalSlider_2.value()))


class Afterburner:
    """Класс объекта получающего данные из MSI AB"""

    def __init__(self):
        import clr
        clr.AddReference(fc_path + 'MSIAfterburner.NET.dll')  # Добавляет библиотеку в поле видимости Python.Net
        import MSI.Afterburner  # Импортируем библиотеку
        self.msi = MSI.Afterburner

    def get_values(self, fr=0):
        """Функция, получающая данные из MSI Afterburner"""
        values = []
        try:
            values = self.msi.HardwareMonitor().Entries  # получаем данные из MSIAfterburner.NET.dll
        except:  # Событие, происходящее при смене настроек в MSI Afterburner, или, если MSI AB не запущен
            if fr:
                QMessageBox.critical(ui, appSettings.lang_string[21], appSettings.lang_string[22], QMessageBox.Ok)
            else:
                os.spawnv(os.P_NOWAIT, fc_path + 'fan_control_reset.exe', ['-'])
                QApplication.quit()
        if values:
            temperature_entries, gpu_temperatures, cpu_temperatures = [], [], []  # создаём три списка под температуры
            for value in values:  # находим все элементы с температурами в hwm_entries по вхождению выражения
                if 'temperature;SrcUnits' in str(value):
                    temperature_entries.append(str(value))
            for value in temperature_entries:  # сортируем найденные темпрературы на CPU и GPU по вхождению выражений
                position = value.find('Data = ') + 7
                if value.startswith('SrcName = GPU'):
                    gpu_temperatures.append(int(value[position:position + 2]))
                else:
                    cpu_temperatures.append(int(value[position:position + 2]))
            return gpu_temperatures, cpu_temperatures
        else:
            return False

    def mon_conf(self):
        """Функция, конфигурирующая вкладку мониторинга"""
        mon_values = self.get_values(fr=1)
        if mon_values:
            cpu_count, gpu_count = len(mon_values[1]), len(mon_values[0])
            gpu_string, cpu_string = '', ''
            if gpu_count == 1:
                gpu_string = 'GPU'
            else:
                for i in range(gpu_count):
                    gpu_string += 'GPU{0}\n'.format(i + 1)
            for i in range(cpu_count):
                cpu_string += 'CPU{0}\n'.format(i + 1)
            if gpu_string.endswith('\n'):
                gpu_string = gpu_string[:-1]
            if cpu_string.endswith('\n'):
                cpu_string = cpu_string[:-1]
            ui.label_4.setText(gpu_string)
            ui.label_6.setText(cpu_string)
            lh = ui.label_4.height()
            if gpu_count == 1:
                gpu_label_size = lh - 7
            else:
                gpu_label_size = (lh * 2) - 7
            cpu_label_size = (lh * cpu_count) - 5
            ui.label_4.setMaximumHeight(gpu_label_size)
            ui.label_5.setMaximumHeight(gpu_label_size)
            ui.label_6.setMaximumHeight(cpu_label_size)
            ui.label_7.setMaximumHeight(cpu_label_size)
            return True
        else:
            return False


class SerialPort:
    """Класс объекта, производящего манипуляции с COM-портом"""

    def __init__(self):
        self.opened_port = False
        self.busy = False
        self.connecting = False
        self.answer_result = 0
        self.writing = False
        self.port = ''

    @thread
    def connect(self, port):
        """Функция, создающая подключение к COM-порту"""
        self.connecting = True
        try:
            self.opened_port = serial.Serial(port=port, baudrate=9600, timeout=0, write_timeout=3)
            self.port = port
            self.connecting = False
            ui.pushButton_4.setEnabled(True)
            led_elements_control()
        except (OSError, serial.SerialException):
            self.error()

    @thread
    def send(self, command):
        """Функция отправки команды в ком-порт.
        Функция предполагает подтверждение получения команды устройством, а в случае отсутствия ответа (например т.к.
        устройство не успело загрузиться или перезагрузилось) выполняет повторную отправку команды и/или реконнект"""
        if self.opened_port:
            self.busy = True
            self.answer_result = 0
            sending_count = 0
            reconnections = 0
            command = command.encode('utf-8')
            while sending_count < 2:  # Количество попыток передать команду
                try:
                    self.opened_port.write(command)
                    answer_count = 0  # модуль ожидания ответа устройства начинается тут_______________________________
                    while answer_count < 6:
                        time.sleep(1)
                        try:
                            answer = self.opened_port.read_all()
                        except AttributeError:
                            pass
                        if b'answ:done' in answer:
                            self.answer_result = 1
                            break
                        elif self.answer_result:
                            break
                        answer_count += 1
                    if self.answer_result:
                        self.busy = False
                        break
                    sending_count += 1
                    if sending_count == 2:  # Модуль переподключения
                        if not reconnections:
                            self.opened_port.close()
                            time.sleep(1)
                            self.opened_port = serial.Serial(port=self.port, baudrate=115200, timeout=0,
                                                             write_timeout=3)
                            sending_count = -1
                            reconnections = 1  # модуль ожидания ответа устройства завершается тут______________________
                except (OSError, serial.SerialException):  # происходит при неудачной попытке записать или читать из com
                    sending_count = 3
                    self.error()
            else:  # происходит при превышении порога ожидания ответа
                self.error()
        else:  # происходит, если компорт закрыт
            self.error()

    @thread
    def close(self):
        """Функция закрытия открытого подключения"""
        while self.busy:
            time.sleep(0.3)
        if self.opened_port:
            self.opened_port.close()
            self.opened_port = False

    def error(self):
        """Функция вызываемая при ошибках работы с COM-портом"""
        if ui.isHidden():
            ui.processing.show()
        self.busy = False
        self.connecting = False
        self.writing = False
        if self.opened_port:
            self.close()
            while self.opened_port:
                time.sleep(0.1)
        if not ui.tabWidget.currentIndex():
            ui.tabWidget.setCurrentIndex(1)
        if not settings_window.isHidden():
            settings_window.close()
        ui.com_search.exiting = 0
        ui.com_search.start()
        ui.pushButton_4.setDisabled(True)
        ui.checkBox_2.setDisabled(True)
        ui.pushButton_5.setDisabled(True)
        ui.label_2.setText(appSettings.lang_string[20])
        ui.label_8.setPalette(ui.text_palette([255, 0, 0]))
        ui.label_8.setText('r')


class ComSearch(QThread):
    """Класс объекта производящего поиск доступных ком-портов, вызывается в подпроцессе QT из главного окна ui"""

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False
        pass

    def run(self):
        com_keys = False
        while not self.exiting:
            com_keys = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM", 0, winreg.KEY_READ)
            port_list = []
            for num in range(100):
                try:
                    value = winreg.EnumValue(com_keys, num)
                    port_list.append(value[1])
                except OSError:
                    break
            current = ui.comboBox.currentText()
            ui.comboBox.clear()
            if port_list:
                if current in port_list:
                    port_list.remove(current)
                    ui.comboBox.addItem(current)
                    ui.comboBox.addItems(port_list)
                else:
                    if current in str(sp.opened_port):
                        sp.close()
                        ui.pushButton_4.setDisabled(True)
                        ui.label_2.setText(appSettings.lang_string[20])
                        ui.label_8.setPalette(ui.text_palette([255, 0, 0]))
                        ui.label_8.setText('r')
                    ui.comboBox.addItems(port_list)
            else:
                ui.comboBox.addItem('-')
            ui.comboBox.setCurrentIndex(0)
            ui.comboBox.setDisabled(False)
            time.sleep(2)
        else:
            if com_keys:
                winreg.CloseKey(com_keys)


class Processing(QThread):
    """Класс объекта обновляющего окно мониторинга и управляющего вентиляторами. Заапускается в подпроцессе ui"""
    output = pyqtSignal(QByteArray, QByteArray)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.ab = Afterburner()
        self.lines = {}
        self.led_for_lines = 0
        self.led_en = 0

    def show(self):
        """Вспомогательная функция (КОСТЫЛЬ), необходимая для передачи команды show() форме ui"""
        self.output.emit(b'show', b'')

    def command_preparing(self):
        """Функция предваритеьной подготовки значений температурных режимов PWM и COM-команд, вызывается из self.run"""
        self.lines = {}
        self.led_for_lines = 0
        self.led_en = appSettings.settings['led_en']
        control_for = ''
        led_num = int(appSettings.settings['ledlights'])
        led_effects = appSettings.settings['led_ef']
        ledlights = {}
        if self.led_en and led_num and not led_effects:
            if appSettings.settings['overheat1_en'] + appSettings.settings['overheat2_en'] + \
                    appSettings.settings['overheat3_en']:
                ledlights = {'led_pos1': led_command(1, appSettings.settings['led_col'])}
                for pos in range(2, 5):
                    adr = pos - 1
                    if appSettings.settings['overheat{0}_en'.format(adr)]:
                        ps = {'led_pos{0}'.format(pos): led_command(1, appSettings.settings['overheat{0}'.format(adr)])}
                    else:
                        ps = {'led_pos{0}'.format(pos): ''}
                    ledlights.update(ps)
                control_for = appSettings.settings['led_for_line']

        for num in range(1, 5):
            if appSettings.settings['line_{0}'.format(num)]:
                boost = 'h'
                if appSettings.settings['l{0}_3pin'.format(num)]:
                    boost = 'b'
                freq = appSettings.settings['l{0}_freq'.format(num)]
                if len(freq) == 1:
                    freq = '0{0}'.format(freq)
                minimal = 'fn{0}{1}{2}{3};'.format(num, freq, boost, appSettings.settings['l{0}_min'.format(num)])
                pos1 = 'fn{0}{1}{2}{3};'.format(num, freq, boost, appSettings.settings['l{0}_pos1'.format(num)][0])
                pos2 = 'fn{0}{1}{2}{3};'.format(num, freq, boost, appSettings.settings['l{0}_pos2'.format(num)][0])
                pos3 = 'fn{0}{1}{2}{3};'.format(num, freq, boost, appSettings.settings['l{0}_pos3'.format(num)][0])
                pos4 = 'fn{0}{1}{2}{3};'.format(num, freq, boost, appSettings.settings['l{0}_pos4'.format(num)][0])
                if ledlights and control_for == num:
                    minimal = '{0}{1}'.format(minimal, ledlights['led_pos1'])
                    pos1 = '{0}{1}'.format(pos1, ledlights['led_pos1'])
                    pos2 = '{0}{1}'.format(pos2, ledlights['led_pos2'])
                    pos3 = '{0}{1}'.format(pos3, ledlights['led_pos3'])
                    pos4 = '{0}{1}'.format(pos4, ledlights['led_pos4'])
                    self.led_for_lines += 1
                cur_line = {'targ': appSettings.settings['l{0}_control'.format(num)], 'min': minimal,
                            'pos1': [int(appSettings.settings['l{0}_pos1'.format(num)][1]), pos1],
                            'pos2': [int(appSettings.settings['l{0}_pos2'.format(num)][1]), pos2],
                            'pos3': [int(appSettings.settings['l{0}_pos3'.format(num)][1]), pos3],
                            'pos4': [int(appSettings.settings['l{0}_pos4'.format(num)][1]), pos4],
                            'state': 0}
                self.lines.update({'line{0}'.format(num): cur_line})


    def temp_processing(self, mcg, channel):
        """Функция, сверяющая температурную позицию линии PWM, вызывается из функции self.run"""
        line = self.lines[channel]
        state = line['state']
        command = ''
        if mcg >= line['pos4'][0] and state < 4:
            state = 4
            command = line['pos4'][1]
        elif mcg >= line['pos3'][0] and state < 3:
            state = 3
            command = line['pos3'][1]
        elif mcg >= line['pos2'][0] and state < 2:
            state = 2
            command = line['pos2'][1]
        elif mcg >= line['pos1'][0] and state == 0:
            state = 1
            command = line['pos1'][1]
        elif mcg < line['pos1'][0] and state > 0:
            state = 0
            command = line['min']
        elif mcg < line['pos2'][0] and state == 2:
            state = 1
            command = line['pos1'][1]
        elif mcg < line['pos3'][0] and state == 3:
            state = 2
            command = line['pos2'][1]
        elif mcg < line['pos4'][0] and state == 4:
            state = 3
            command = line['pos3'][1]
        self.lines[channel]['state'] = state
        return command

    def run(self):
        """Функция, отрисовывающая мониторинг"""
        self.command_preparing()  # Заранее готовим команды управления
        while sp.connecting:  # Проверяем, не выполняется ли подключение к ком-порту
            time.sleep(0.1)
        if sp.opened_port:
            ui.processing_state = 1
            while settings_window.testing_process:
                time.sleep(0.1)  # Если порт открыт, проверим, не происходит ли в данный момент процесс тестирования
            command = 'cmnd;'
            for key in self.lines:
                command += self.lines[key]['min']
            if not self.led_for_lines and self.led_en:
                command = command + led_command(2)
            sp.send(command)  # Выставим минимальные обороты при запуске процесса обработки температур
            while not self.exiting:
                temp_values = self.ab.get_values()
                if temp_values:
                    if not ui.isHidden():  # Обновляем значения мониторинга только если окно программы открыто
                        gpu_temp_string = ''
                        cpu_temp_string = ''
                        for i in temp_values[0]:
                            gpu_temp_string += '{0}\n'.format(i)
                        gpu_temp_string = gpu_temp_string[:-1]
                        for i in temp_values[1]:
                            cpu_temp_string += '{0}\n'.format(i)
                        cpu_temp_string = cpu_temp_string[:-1]
                        self.output.emit(gpu_temp_string.encode('utf-8'), cpu_temp_string.encode('utf-8'))
                    if not sp.busy:
                        command = ['cmnd;']
                        for line in self.lines:  # Проверяем каждую из линий на диапазон температур
                            if self.lines[line]['targ'] == 0:  # Определяем зону регулировки (CPU/GPU)
                                mcg = max(temp_values[0])
                            elif self.lines[line]['targ'] == 1:
                                mcg = max(temp_values[1])
                            elif self.lines[line]['targ'] == 2:
                                mcg = max(temp_values[0] + temp_values[1])
                            preparing = self.temp_processing(mcg, line)
                            if preparing:
                                command.append(preparing)
                        if len(command) > 1:
                            command = ''.join(command)
                            sp.send(command)
                    time.sleep(2)
                else:
                    break
            ui.processing_state = 0


"""Раздел обработки событий UI_______________________________________________________________________________________"""


@thread
def main_window_tab_control():
    """Функция обработки переключения вкладок основного окна. Запускается в отдельном процессе для синхронизации"""
    if ui.tabWidget.currentIndex() == 0:
        if sp.opened_port:
            ui.com_search.exiting = 1
            ui.processing.exiting = 0
            if not ui.processing_state:  # запускаем processing лишь если он успел выключиться
                ui.processing.start()
        else:
            ui.tabWidget.setCurrentIndex(1)
    elif ui.tabWidget.currentIndex() == 1:
        if not sp.opened_port:  # проверяем, есть ли соединение по com и выставляем доступность кнопки доп.настроек
            ui.pushButton_4.setDisabled(True)
            ui.label_2.setText(appSettings.lang_string[20])
            ui.label_8.setPalette(ui.text_palette([255, 0, 0]))
            ui.label_8.setText('r')
        else:
            ui.pushButton_4.setEnabled(True)
            ui.label_2.setText(appSettings.lang_string[19])
            ui.label_8.setPalette(ui.text_palette([34, 177, 76]))
            ui.label_8.setText('a')
        if sp.busy:
            sp.answer_result = 1
        ui.processing.exiting = 1
        ui.com_search.exiting = 0
        ui.com_search.start()


@thread
def connect_button():
    """Обработка нажатия клавиши теста выбранного ком-порта."""
    ui.label_8.setText('q')
    ui.label_2.setText('')
    ui.tabWidget.setDisabled(True)
    if sp.opened_port:
        sp.close()
    while sp.opened_port:
        time.sleep(0.1)
    sp.connect(ui.comboBox.currentText())
    while not sp.opened_port:
        time.sleep(0.1)
        if not sp.connecting:
            break
    if sp.opened_port:
        sp.send('cmnd;')
        while not sp.busy:
            time.sleep(0.1)
        while sp.busy:
            time.sleep(0.1)
        if sp.answer_result:
            ui.label_2.setText(appSettings.lang_string[19])
            ui.label_8.setPalette(ui.text_palette([34, 177, 76]))
            ui.label_8.setText('a')
        else:
            ui.label_2.setText(appSettings.lang_string[20])
            ui.label_8.setPalette(ui.text_palette([255, 0, 0]))
            ui.label_8.setText('r')
    ui.tabWidget.setEnabled(True)


@thread
def led_checkbox():
    status = int(ui.checkBox_2.isChecked())
    appSettings.settings['led_en'] = status
    if status:
        ui.led_action.setFont(ui.active_button_font)
        led_command(0)
        if not appSettings.settings['led_ef']:
            ui.pushButton_5.setEnabled(True)
    else:
        ui.tabWidget.setDisabled(True)
        ui.pushButton_5.setDisabled(True)
        ui.led_action.setFont(ui.simple_font)
        while ui.processing_state:
            time.sleep(0.1)
        sp.send('cmnd;np0000000000000000;')
        time.sleep(0.1)
        while sp.busy:
            time.sleep(0.1)
        if settings_window.isHidden():
            ui.tabWidget.setEnabled(True)
    pass


@thread
def boost_zone_button():
    """Обработка нажатия кнопки изменения границы зоны буста"""
    if settings_window.lineEdit_6.text() != appSettings.settings['boost_zone']:
        settings_window.tabWidget.setDisabled(True)
        appSettings.save_aditional()
        sp.send('cmnd;bz{0};'.format(appSettings.settings['boost_zone']))
        while not sp.busy:
            time.sleep(0.1)
        while sp.busy:
            time.sleep(0.1)
        settings_window.tabWidget.setEnabled(True)


@thread
def service_button():
    """Обработка нажатия кнопки перехода в service-режим"""
    settings_window.tabWidget.setDisabled(True)
    sp.send('cmnd;service;')
    while not sp.busy:
        time.sleep(0.1)
    while sp.busy:
        time.sleep(0.1)
    ui.exit_func(0)


@thread
def testing():
    """Функция, обрабатывающая нажатие на кнопку 'Тест' окна settings_window"""
    settings_window.testing_process = 1
    duty = settings_window.horizontalSlider.value()
    testing_func(duty)
    settings_window.pushButton_8.setEnabled(True)


@thread
def stop_testing():
    """Функция, обрабатывающая нажатие на кнопку 'Стоп' окна settings_window"""
    duty = settings_window.pushButton_2.text()[:-1]
    testing_func(duty)
    settings_window.horizontalSlider.setValue(0)
    settings_window.testing_process = 0


def led_command(arg, col=0):
    """Функция подготавливающая управляющую комнду LED-ленты и (опционально) отправляющая её на устройство"""

    @thread
    def led_applying(cmnd):
        while sp.busy:
            time.sleep(0.1)
        sp.send(cmnd)
        while sp.busy:
            time.sleep(0.1)
        settings_window.tabWidget.setEnabled(True)
        if settings_window.isHidden():
            ui.tabWidget.setEnabled(True)

    command = ['np', '', '', '00', '00', '0']
    if settings_window.lineEdit_5.text().replace(' ', ''):
        if int(settings_window.lineEdit_5.text()):  # Блок ниже выполняется если введено колличество светодиодов
            leds_num = settings_window.lineEdit_5.text().replace(' ', '')
            if len(leds_num) == 1:
                command[1] = '00{0}'.format(leds_num)
            elif len(leds_num) == 2:
                command[1] = '0{0}'.format(leds_num)
            else:
                command[1] = leds_num
            brightness = str(settings_window.horizontalSlider_2.value())
            if brightness == '100':
                brightness = '99'
            elif len(brightness) == 1:
                brightness = '0{0}'.format(brightness)
            command[2] = str(brightness)
            if settings_window.comboBox_2.currentIndex():
                effect = str(settings_window.comboBox_2.currentIndex())
                if len(effect) == 1:
                    effect = '0{0}'.format(effect)
                command[3] = effect
                effect_speed = settings_window.horizontalSlider_4.value()
                effect_speed = str(max(1, min(99, effect_speed)))
                if len(effect_speed) == 1:
                    effect_speed = '0{0}'.format(effect_speed)
                command[4] = str(effect_speed)
            if col:
                command[5] = col[1:]
            else:
                command[5] = appSettings.settings['led_col'][1:]
            if not arg:  # Если вызов произошёл от кнопок - применяем полученную команду
                settings_window.tabWidget.setDisabled(True)
                ui.tabWidget.setDisabled(True)
                if not appSettings.settings['led_en']:
                    appSettings.settings['led_en'] = 1
                    ui.checkBox_2.setChecked(True)
                command = 'cmnd;' + ''.join(command) + '1;'
                led_applying(command)
            elif arg == 1:  # Если вызов произошёл от функции - возвращаем команду плавной установки цвета
                command = ''.join(command) + '0;'
                return command
            elif arg == 2:  # Если вызов произошёл от функции  - возвращаем команду быстрой установки цвета
                command = ''.join(command) + '1;'
                return command

        else:  # Выполняется если НЕ введено колличество светодиодов
            if not arg:
                pass
            else:
                return 'np0000000000000000;'
    else:
        settings_window.lineEdit_5.setText('0')


def slider_value_control():
    """Фнкция контролирующая перемещение слайдера оборотов (по значениям кратным 5)"""
    value = settings_window.horizontalSlider.value()
    if len(str(value)) == 1:
        if value > 5:
            a = 10 - value
            b = value - 5
            if a > b:
                value = 5
            else:
                value = 10
        elif value <= 5:
            a = 5 - value
            if a > value:
                value = 0
            else:
                value = 5
    elif value == 100:
        pass
    else:
        sec_val = int(str(value)[1])
        first_val = int(str(value)[0])
        vector = ''
        if sec_val > 5:
            a = 10 - sec_val
            b = sec_val - 5
            if a > b:
                sec_val = 5
            else:
                sec_val = 0
                vector = '+'
        elif sec_val <= 5:
            a = 5 - sec_val
            if a > sec_val:
                sec_val = 0
            else:
                sec_val = 5
        if vector == '+':
            first_val += 1
        value = int(str(first_val) + str(sec_val))
    settings_window.horizontalSlider.setValue(value)
    settings_window.pushButton.setText("{0}% - Тест".format(settings_window.horizontalSlider.value()))


def led_effetcs_combobox():
    """Функция, контролирующая комбобокс выбора LED-эффектов"""
    if not settings_window.comboBox_2.currentIndex():
        settings_window.label_12.setDisabled(True)
        settings_window.horizontalSlider_4.setDisabled(True)
        settings_window.pushButton_9.setEnabled(True)
        if appSettings.settings['line_3'] + appSettings.settings['line_2'] + appSettings.settings['line_1']:
            settings_window.label_10.setEnabled(True)
            settings_window.label_13.setEnabled(True)
            settings_window.comboBox_3.setEnabled(True)
            settings_window.checkBox_5.setEnabled(True)
            settings_window.checkBox_6.setEnabled(True)
            settings_window.checkBox_7.setEnabled(True)
            settings_window.pushButton_12.setEnabled(True)
            settings_window.pushButton_13.setEnabled(True)
            settings_window.pushButton_14.setEnabled(True)
    else:
        settings_window.label_12.setEnabled(True)
        settings_window.horizontalSlider_4.setEnabled(True)
        settings_window.pushButton_9.setDisabled(True)
        settings_window.pushButton_12.setDisabled(True)
        settings_window.pushButton_13.setDisabled(True)
        settings_window.pushButton_14.setDisabled(True)
        settings_window.comboBox_3.setDisabled(True)
        settings_window.label_10.setDisabled(True)
        settings_window.label_13.setDisabled(True)
        settings_window.checkBox_5.setDisabled(True)
        settings_window.checkBox_6.setDisabled(True)
        settings_window.checkBox_7.setDisabled(True)


def setting_window_tab_control():
    """Функция сохраняющая настройки при смене вкладки окна настроек, так же обрабатывающая состояние части элементов"""
    if settings_window.last_tab != settings_window.tabWidget.currentIndex():
        if settings_window.last_tab == 0:
            appSettings.save_lines()
        elif settings_window.last_tab == 1:
            appSettings.save_led_settings()
        elif settings_window.last_tab == 2:
            appSettings.save_aditional()
        settings_window.last_tab = settings_window.tabWidget.currentIndex()
    if settings_window.tabWidget.currentIndex() == 1:
        if not settings_window.comboBox_2.currentIndex():
            if appSettings.settings['line_3'] + appSettings.settings['line_2'] + appSettings.settings['line_1']:
                settings_window.label_13.setEnabled(True)
                settings_window.comboBox_3.setEnabled(True)
                settings_window.checkBox_5.setEnabled(True)
                settings_window.checkBox_6.setEnabled(True)
                settings_window.checkBox_7.setEnabled(True)
                settings_window.pushButton_12.setEnabled(True)
                settings_window.pushButton_13.setEnabled(True)
                settings_window.pushButton_14.setEnabled(True)
            else:
                settings_window.label_13.setDisabled(True)
                settings_window.comboBox_3.setDisabled(True)
                settings_window.checkBox_5.setDisabled(True)
                settings_window.checkBox_6.setDisabled(True)
                settings_window.checkBox_7.setDisabled(True)
                settings_window.pushButton_12.setDisabled(True)
                settings_window.pushButton_13.setDisabled(True)
                settings_window.pushButton_14.setDisabled(True)
            led_line_combobox()
        else:
            led_effetcs_combobox()


def line_state():
    """Действия чекбокса включения/выключения PWM-линии"""
    state = settings_window.checkBox_3.isChecked()
    settings_window.checkBox.setEnabled(state)
    settings_window.checkBox_2.setEnabled(state)
    settings_window.checkBox_4.setEnabled(state)
    settings_window.horizontalSlider.setEnabled(state)
    settings_window.pushButton.setEnabled(state)
    settings_window.pushButton_2.setEnabled(state)
    settings_window.pushButton_3.setEnabled(state)
    settings_window.pushButton_4.setEnabled(state)
    settings_window.pushButton_5.setEnabled(state)
    settings_window.pushButton_6.setEnabled(state)
    settings_window.lineEdit.setEnabled(state)
    settings_window.lineEdit_2.setEnabled(state)
    settings_window.lineEdit_3.setEnabled(state)
    settings_window.lineEdit_4.setEnabled(state)
    settings_window.lineEdit_7.setEnabled(state)
    settings_window.label_2.setEnabled(state)
    settings_window.label_3.setEnabled(state)
    settings_window.label_4.setEnabled(state)
    settings_window.label_5.setEnabled(state)
    settings_window.label_6.setEnabled(state)
    settings_window.label_8.setEnabled(state)
    settings_window.label_16.setEnabled(state)


def testing_func(duty):
    """функция, подготавливающая и отправляющая команду тестирования, вызывается из testing, stop_testing"""
    settings_window.pushButton.setDisabled(True)
    settings_window.pushButton_8.setDisabled(True)
    line = settings_window.comboBox.currentText()
    boost = 'h'
    if settings_window.checkBox_4.isChecked():
        boost = 'b'
    freq = settings_window.lineEdit_4.text()
    if len(freq) == 1:
        freq = '0{0}'.format(freq)
    elif len(freq) == 2:
        if int(freq) > 61:
            freq = '61'
    else:
        freq = '21'
    command = 'cmnd;fn{0}{1}{2}{3}'.format(line, freq, boost, duty)
    sp.send(command)
    while not sp.busy:
        time.sleep(0.1)
    while sp.busy:
        time.sleep(1)
    settings_window.pushButton.setEnabled(True)


def lang_button(arg):
    """Обработка нажатия клавиши смены языка"""
    if arg:
        ui.pushButton_2.setFont(ui.active_button_font)
        ui.pushButton_3.setFont(QtGui.QFont())
        appSettings.settings['lang'] = 'ru'
    else:
        ui.pushButton_3.setFont(ui.active_button_font)
        ui.pushButton_2.setFont(QtGui.QFont())
        appSettings.settings['lang'] = 'en'
    appSettings.set_lang()
    appSettings.save()


def autoload_checkbox():
    """Функция обработки чекбокса автозагрузки"""
    global executable
    key = winreg.HKEY_CURRENT_USER
    subkey = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    values_list = autoload_values()
    if ui.checkBox.isChecked():
        if 'FanControl' not in values_list:
            as_key = winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(as_key, 'FanControl', 0, 1, '"{0}" {1}'.format(executable, '-5'))
            winreg.CloseKey(as_key)
    else:
        if 'FanControl' in values_list:
            as_key = winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(as_key, 'FanControl')


def color_selector(zone):
    """Функция, обрабатывающая нажатия кнопок выбора цвета"""
    col = QColorDialog.getColor()
    if col.isValid():
        rgb = col.getRgb()[:-1]
        col = '#%02x%02x%02x' % rgb
        if zone < 1:
            appSettings.settings['led_col'] = col
            if not zone:
                led_command(0)
            ui.pushButton_5.setPalette(ui.colour_button_palette(col))
            settings_window.pushButton_9.setPalette(ui.colour_button_palette(col))
        else:
            appSettings.settings['overheat{0}'.format(zone)] = col
            exec('settings_window.pushButton_{0}.setPalette(ui.colour_button_palette(col))'.format(11 + zone))


def autoload_values():
    """Функция, получющая список автозагрузки, вызывается из autostart_checkbox и appSettings.load"""
    key = winreg.HKEY_CURRENT_USER
    subkey = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    as_key = winreg.OpenKey(key, subkey, 0, winreg.KEY_READ)
    values_list = []
    for i in range(100):
        try:
            value = winreg.EnumValue(as_key, i)
            values_list.append(value[0])
        except OSError:
            winreg.CloseKey(as_key)
            return values_list


def com_combobox():
    """Функция, обрабатывающая смену выбранного элемента combobox окна ui"""
    port = ui.comboBox.currentText()
    if port == '-':
        ui.pushButton.setDisabled(True)
        ui.pushButton_4.setDisabled(True)
    else:
        if not ui.pushButton_4.isEnabled():
            ui.pushButton.setEnabled(True)
        appSettings.settings['com'] = port
        appSettings.save()


def led_elements_control():
    """Функция контролирующее состояние элементов управления LED-подсветкой"""
    leds = int(appSettings.settings['ledlights'])
    if leds:
        ui.checkBox_2.setEnabled(True)
        ui.led_action.setEnabled(True)
        if not appSettings.settings['led_ef']:
            ui.pushButton_5.setEnabled(True)
    else:
        ui.checkBox_2.setChecked(False)
        ui.checkBox_2.setDisabled(True)
        ui.led_action.setDisabled(True)
        ui.led_action.setFont(ui.simple_font)
        ui.pushButton_5.setDisabled(True)
    if appSettings.settings['led_ef']:
        ui.pushButton_5.setDisabled(True)
    if appSettings.settings['led_en']:
        ui.led_action.setFont(ui.active_button_font)
        if not ui.checkBox_2.isChecked():
            ui.checkBox_2.setChecked(True)
            ui.pushButton_5.setEnabled(True)
    else:
        ui.pushButton_5.setDisabled(True)


def settings_button():
    """Обработка нажатия кнопки расширенных настроек"""
    ui.com_search.exiting = 1
    current_line = settings_window.comboBox.currentText()
    settings_window.comboBox.setCurrentIndex(0)
    settings_window.pushButton_8.setDisabled(True)
    if current_line == '1':
        appSettings.set_values('1')
    ui.tabWidget.setDisabled(True)
    settings_window.tabWidget.setCurrentIndex(0)
    settings_window.show()


def led_zone1_indication():
    """Обработка чекбокса включения индикации зоны нагрева 2-3"""
    if settings_window.checkBox_5.isChecked():
        appSettings.settings['overheat1_en'] = 1
        settings_window.pushButton_12.setEnabled(True)
    else:
        appSettings.settings['overheat1_en'] = 0
        settings_window.pushButton_12.setDisabled(True)


def led_zone2_indication():
    """Обработка чекбокса включения индикации зоны нагрева 3-4"""
    if settings_window.checkBox_6.isChecked():
        appSettings.settings['overheat2_en'] = 1
        settings_window.pushButton_13.setEnabled(True)
    else:
        appSettings.settings['overheat2_en'] = 0
        settings_window.pushButton_13.setDisabled(True)


def led_zone3_indication():
    """Обработка чекбокса включения индикации зоны нагрева 4+"""
    if settings_window.checkBox_7.isChecked():
        appSettings.settings['overheat3_en'] = 1
        settings_window.pushButton_14.setEnabled(True)
    else:
        appSettings.settings['overheat3_en'] = 0
        settings_window.pushButton_14.setDisabled(True)


def led_line_combobox():
    """Функция, контролирующая выбор линиии привязки LED-индикации температур"""
    if not appSettings.settings['line_{0}'.format(settings_window.comboBox_3.currentText())]:
        for i in range(1, 5):
            if appSettings.settings['line_{0}'.format(i)]:
                settings_window.comboBox_3.setCurrentIndex(i - 1)


def donate_button():
    """Обработка нажатия кнопки доната"""
    if appSettings.settings['lang'] == 'ru':
        webbrowser.open_new_tab('https://money.yandex.ru/to/41001350655590')
    else:
        webbrowser.open_new_tab('https://money.yandex.ru/to/41001350655590')


def gpu_checkbox():
    """Обработка смены состояния чекбокса ГПУ"""
    if not settings_window.checkBox_2.checkState():
        if not settings_window.checkBox.checkState():
            settings_window.checkBox.setChecked(True)


def cpu_checkbox():
    """Обработка смены состояния чекбокса ЦПУ"""
    if not settings_window.checkBox.checkState():
        if not settings_window.checkBox_2.checkState():
            settings_window.checkBox_2.setChecked(True)


def line_change():
    """Обработка комбо-бокса смены линии PWM"""
    appSettings.save_lines()
    appSettings.cl = settings_window.comboBox.currentText()
    appSettings.set_values(settings_window.comboBox.currentText())


def rpm_buttons(arg):
    """Обработка нажатия кнопок выбора оборотов"""
    text = '{0}%'.format(settings_window.horizontalSlider.value())
    exec('settings_window.pushButton_{0}.setText(text)'.format(arg))


def brightness_changed():
    """Обработка смены позиции слайдера яркости"""
    settings_window.label_14.setText('{0} ({1}):'.format(appSettings.lang_string[29],
                                                         settings_window.horizontalSlider_2.value()))


def effect_speed_changed():
    """Обработка смены позиции слайдера скорости эффекта"""
    settings_window.label_12.setText('{0} ({1}):'.format(appSettings.lang_string[33],
                                                         settings_window.horizontalSlider_4.value()))


def about_button():
    """Обработка нажатия кнопки посещения сайта проекта"""
    webbrowser.open_new_tab('https://github.com/ATRedline/ESP32_Fan_Control')


"""Раздел инициализации программы____________________________________________________________________________________"""

fc_path = os.path.abspath(sys.argv[0]).rfind('\\')
fc_path = os.path.abspath(sys.argv[0])[:fc_path+1]
auto_load = 0
if len(sys.argv) > 1:  # Модуль реализации отсрочки запуска по ключу из аргумента запуска
    arg = sys.argv[1][1:]
    if arg.isdigit():
        auto_load = 1
        arg = int(arg)
        time.sleep(arg)

tasklist, count = sup.Popen('tasklist', stdout=sup.PIPE, stdin=sup.DEVNULL, stderr=sup.DEVNULL, shell=True), 0
for i in tasklist.stdout:  # Проверяем наличие уже запущенного процесса программы
    if 'fan_control' in str(i):
        count += 1
if count < 3:  # Инициализируем программу при отсутствии уже запущенных копий
    app = QtWidgets.QApplication(sys.argv)
    ab = Afterburner()
    ui = MainWindow()
    settings_window = SettingsWindow()
    appSettings = AppSettings()
    appSettings.load()
    if ab.mon_conf():  # Инициализируем программу если удалось подключиться к MSI:AB
        del ab
        sp = SerialPort()
        if appSettings.settings['com']:
            sp.connect(appSettings.settings['com'])
            app_loading = 1
            ui.processing.start()
        if not auto_load:
            ui.show()
        ui.pushButton_2.clicked.connect(lambda: lang_button(1))
        ui.pushButton_3.clicked.connect(lambda: lang_button(0))
        ui.pushButton_4.clicked.connect(settings_button)
        ui.pushButton_5.clicked.connect(lambda: color_selector(0))
        ui.pushButton.clicked.connect(lambda: connect_button())
        ui.comboBox.currentTextChanged.connect(com_combobox)
        ui.checkBox.stateChanged.connect(autoload_checkbox)
        ui.checkBox_2.stateChanged.connect(lambda: led_checkbox())
        ui.tabWidget.currentChanged.connect(lambda: main_window_tab_control())
        settings_window.tabWidget.currentChanged.connect(setting_window_tab_control)
        settings_window.comboBox.currentTextChanged.connect(line_change)
        settings_window.comboBox_2.currentTextChanged.connect(led_effetcs_combobox)
        settings_window.checkBox.stateChanged.connect(cpu_checkbox)
        settings_window.checkBox_2.stateChanged.connect(gpu_checkbox)
        settings_window.checkBox_3.stateChanged.connect(line_state)
        settings_window.checkBox_5.stateChanged.connect(led_zone1_indication)
        settings_window.checkBox_6.stateChanged.connect(led_zone2_indication)
        settings_window.checkBox_7.stateChanged.connect(led_zone3_indication)
        settings_window.pushButton.clicked.connect(lambda: testing())
        settings_window.pushButton_2.clicked.connect(lambda: rpm_buttons(2))
        settings_window.pushButton_3.clicked.connect(lambda: rpm_buttons(3))
        settings_window.pushButton_4.clicked.connect(lambda: rpm_buttons(4))
        settings_window.pushButton_5.clicked.connect(lambda: rpm_buttons(5))
        settings_window.pushButton_6.clicked.connect(lambda: rpm_buttons(6))
        settings_window.pushButton_8.clicked.connect(lambda: stop_testing())
        settings_window.pushButton_10.clicked.connect(led_command)
        settings_window.pushButton_9.clicked.connect(lambda: color_selector(-1))
        settings_window.pushButton_12.clicked.connect(lambda: color_selector(1))
        settings_window.pushButton_13.clicked.connect(lambda: color_selector(2))
        settings_window.pushButton_14.clicked.connect(lambda: color_selector(3))
        settings_window.pushButton_15.clicked.connect(lambda: service_button())
        settings_window.pushButton_16.clicked.connect(lambda: boost_zone_button())
        settings_window.comboBox_3.currentIndexChanged.connect(led_line_combobox)
        settings_window.horizontalSlider.valueChanged.connect(slider_value_control)
        settings_window.horizontalSlider_2.valueChanged.connect(brightness_changed)
        settings_window.horizontalSlider_4.valueChanged.connect(effect_speed_changed)
        executable = os.path.abspath(sys.argv[0])
        app_loading = 0
        sys.exit(app.exec_())
    else:
        QApplication.quit()
else:
    QApplication.quit()
