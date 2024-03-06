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
import databox


class Cpu(QWidget):
    def __init__(self):
        super().__init__()

        self.usage_icon_name()

        self.conn = self.create_connection()
        self.create_table(self.conn)
        self.delete_old_value_table(self.conn)

        self.timer = QTimer()
        self.time_timer = QTimer()
        self.time_timer.start(databox.ONE_SECOND)
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)

        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.axis = self.figure.add_subplot(1, 1, 1)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QPushButton('1 second', clicked=lambda: self.start_timer(databox.ONE_SECOND)))
        self.layout.addWidget(QPushButton('10 seconds', clicked=lambda: self.start_timer(databox.TEN_SECONDS)))
        self.layout.addWidget(QPushButton('1 minute', clicked=lambda: self.start_timer(databox.ONE_MINUTE)))
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

        self.start_timer(databox.ONE_SECOND)

    def create_connection(self):
        """создание файла базы данных"""
        conn = None;
        try:
            conn = sqlite3.connect('cpu_usage.sqlite')

            return conn
        except Error as e:
            print(e)

        return conn

    def create_table(self, conn):
        """создание базы данных"""
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

    def delete_old_value_table(self, conn):
        """очистка базы данных"""
        try:
            cursor = conn.cursor()
            cursor.execute("""
               DELETE FROM cpu_usage;
            """)
            conn.commit()
        except Error as e:
            print(e)

    def insert_cpu_usage(self, conn, cpu_percent, time):
        """ вставка данных в БД"""
        try:
            conn.execute("""
                   INSERT INTO cpu_usage(usage, time) VALUES (?, ?)
               """, (cpu_percent, time))
            conn.commit()
        except Error as e:
            print(e)

    def usage_icon_name(self):
        """ Метод для присваивания имени и иконки программы"""
        self.setWindowTitle('CPU Usage')
        self.setWindowIcon(QIcon('img/images.png'))

    def stop_timer(self):
        """Метод остановки таймера, если он используется"""
        if self.timer is not None and self.timer.isActive():
            self.timer.stop()

    def start_timer(self, interval: int) -> None:
        """Метод для запуска таймера с заданным интервалом"""
        self.stop_timer()
        self.delete_old_value_table(self.conn)
        self.text_edit.clear()

        for i in range(len(self.cpu_data) - 1):
            if self.times[i] % (interval // databox.SECONDS_CONVERTER) == 0:
                self.cpu_data_sorted.append(self.cpu_data[i])
                self.insert_cpu_usage(self.conn, self.cpu_data[i], self.times[i])

        for i in range(len(self.cpu_data) - 1):
            if self.times[i] % (interval // databox.SECONDS_CONVERTER) == 0:
                self.text_edit.appendPlainText(f'CPU usage: {str(self.cpu_data[i])}%')

        self.update_interval = interval // databox.SECONDS_CONVERTER
        self.axis.clear()
        self.axis.plot(self.times[::self.update_interval], self.cpu_data[::self.update_interval], color='#2ABf9E')
        self.axis.set_xlabel("Time (s)")
        self.axis.set_ylabel("CPU Usage (%)")
        self.canvas.draw()
        self.timer.stop()
        self.timer.start(databox.ONE_SECOND)
        try:
            self.timer.timeout.disconnect()
        except TypeError:
            pass
        self.timer.timeout.connect(self.update_cpu_usage)

    def update_cpu_usage(self):
        """ Метод для обновления использования ЦП и записи данных в файл и на график"""
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
        self.time_elapsed += 1


def run_app_py():
    """Запуск app.py файл, для отображения данных на веб-странице"""
    subprocess.Popen(["python", "app.py"])


def open_webpage(url):
    """открытие веб-страницы"""
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
