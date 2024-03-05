import sys
import psutil
import os
import datetime
import sqlite3
import webbrowser
import subprocess
from sqlite3 import Error
from typing import List
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QPlainTextEdit
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
import PyQt5.QtCore as QtCore
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from databox import *


class Cpu(QWidget):
    def __init__(self):
        super().__init__()

        self.usage_icon_name()

        self.conn = self.create_connection()
        self.create_table(self.conn)
        self.delete_old_value_table(self.conn)

        self.timer = QTimer()
        self.time_timer = QTimer()
        self.time_timer.start(Const.ONE_SECOND)
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)

        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.axis = self.figure.add_subplot(1, 1, 1)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QPushButton('1 second', clicked=lambda: self.start_timer(Const.ONE_SECOND)))
        self.layout.addWidget(QPushButton('10 seconds', clicked=lambda: self.start_timer(Const.TEN_SECONDS)))
        self.layout.addWidget(QPushButton('1 minute', clicked=lambda: self.start_timer(Const.ONE_MINUTE)))
        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.canvas)

        if not os.path.exists('logs'):
            os.makedirs('logs')

        self.log_file_name = os.path.join('logs', datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

        self.cpu_data: List[float] = []
        self.cpu_data_sorted: List[float] = []
        self.times: List[int] = []
        self.time_elapsed: int = 0
        self.update_interval: int = 1

        self.start_timer(Const.ONE_SECOND)
    """создание файла базы данных"""

    def create_connection(self):
        conn = None;
        try:
            conn = sqlite3.connect('cpu_usage.sqlite')

            return conn
        except Error as e:
            print(e)

        return conn

    """создание базы данных"""

    def create_table(self, conn):
        try:
            conn.execute("DROP TABLE IF EXISTS cpu_usage")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cpu_usage (
                    id INTEGER PRIMARY KEY,
                    usage REAL,
                    time INTEGER
                );
            """)
        except Error as e:
            print(e)

    """очистка базы данных"""

    def delete_old_value_table(self, conn):
        try:
            cursor = conn.cursor()
            cursor.execute("""
               DELETE FROM cpu_usage;
            """)
            conn.commit()
        except Error as e:
            print(e)

    def select_all_cpu_usage(self, conn):
        try:
            cursor = conn.cursor()
            cursor.execute("""
                   SELECT * FROM cpu_usage
               """)
            t = cursor.fetchall()
        except Error as e:
            print(e)

    """ вставка данных в БД"""

    def insert_cpu_usage(self, conn, cpu_percent, time):
        try:
            conn.execute("""
                   INSERT INTO cpu_usage(usage, time) VALUES (?, ?)
               """, (cpu_percent, time))
            conn.commit()
        except Error as e:
            print(e)

    """ Метод для присваивания имени и иконки программы"""

    def usage_icon_name(self):
        self.setWindowTitle('CPU Usage')
        self.setWindowIcon(QIcon('img/images.png'))

    def stop_timer(self):
        if self.timer is not None and self.timer.isActive():
            self.timer.stop()

    """Метод для запуска таймера с заданным интервалом"""

    def start_timer(self, interval: int) -> None:
        self.stop_timer()
        self.delete_old_value_table(self.conn)
        self.text_edit.clear()

        for i in range(len(self.cpu_data) - 1):
            if  self.times[i] % (interval // Const.SECONDS_CONVERTER) == 0:
                self.cpu_data_sorted.append(self.cpu_data[i])
                self.insert_cpu_usage(self.conn, self.cpu_data[i], self.times[i])

        for i in range(len(self.cpu_data) - 1):
            if self.times[i] % (interval // Const.SECONDS_CONVERTER) == 0:
                self.text_edit.appendPlainText(f'CPU usage: {str(self.cpu_data[i])}%')

        self.update_interval = interval // Const.SECONDS_CONVERTER
        self.axis.clear()
        self.axis.plot(self.times[::self.update_interval], self.cpu_data[::self.update_interval], color='#2ABf9E')
        self.axis.set_xlabel("Time (s)")
        self.axis.set_ylabel("CPU Usage (%)")
        self.canvas.draw()
        self.timer.stop()
        self.timer.start(Const.ONE_SECOND)
        try:
            self.timer.timeout.disconnect()
        except TypeError:
            pass    
        self.timer.timeout.connect(self.update_cpu_usage)

    """ Метод для обновления использования ЦП и записи данных в файл и на график"""

    def update_cpu_usage(self):
        cpu_percent = psutil.cpu_percent()
        self.cpu_data.append(cpu_percent)
        self.times.append(self.time_elapsed)
        with open(self.log_file_name, 'a') as f:
            f.write(f'Time: {self.time_elapsed}s, CPU usage: {cpu_percent}%\n')
        if self.time_elapsed % self.update_interval == 0:
            self.axis.clear()
            self.axis.plot(self.times[::self.update_interval], self.cpu_data[::self.update_interval], color='#2ABf9E')
            self.axis.set_xlabel("Time (s)")
            self.axis.set_ylabel("CPU Usage (%)")
            self.canvas.draw()
            self.text_edit.appendPlainText(f'CPU usage: {cpu_percent}%')
            self.insert_cpu_usage(self.conn, cpu_percent, self.time_elapsed)
            self.select_all_cpu_usage(self.conn)
        self.time_elapsed += 1


"""Запуск app.py файл, для отображения данных на веб-странице"""


def run_app_py():
    subprocess.Popen(["python", "app.py"])


"""открытие веб-страницы"""


def open_webpage(url):
    webbrowser.open(url)


def main():
    app = QApplication(sys.argv)

    file = QtCore.QFile("style/style.qss")
    file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
    stream = QtCore.QTextStream(file)
    app.setStyleSheet(stream.readAll())

    window = Cpu()
    window.show()

    webpage_url = "http://127.0.0.1:5000"
    open_webpage(webpage_url)

    run_app_py()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
