import sys
import psutil
import os
import datetime
from typing import List , Dict
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QPlainTextEdit
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
import PyQt5.QtCore as QtCore
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


class Cpu(QWidget):
    def __init__(self):
        super().__init__()

        self.usage_icon_name()

        self.timer = QTimer()
        self.time_timer = QTimer()
        self.time_timer.start(1000)
        self.time_timer.timeout.connect(self.update_time)
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)

        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.axis = self.figure.add_subplot(1, 1, 1)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QPushButton('1 second', clicked=lambda: self.start_timer(1000)))
        self.layout.addWidget(QPushButton('10 seconds', clicked=lambda: self.start_timer(10000)))
        self.layout.addWidget(QPushButton('1 minute', clicked=lambda: self.start_timer(60000)))

        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.canvas)

        if not os.path.exists('logs'):
            os.makedirs('logs')

        self.log_file_name = os.path.join('logs', datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

        self.cpu_data: List = []
        self.times: List = []
        self.data: Dict = {}
        self.time_elapsed = 0
        self.update_interval = 1 

    # Метод для обновления прошедшего времени
    def update_time(self):
        self.time_elapsed += 0

    # Метод для присваивания имени и иконки программы
    def usage_icon_name(self):
        self.setWindowTitle('CPU Usage')
        self.setWindowIcon(QIcon('img/images.png'))

    # Метод для запуска таймера с заданным интервалом
    def start_timer(self, interval):
        self.text_edit.clear()
        for i in range(len(self.cpu_data) - 1):
            if self.times[i] % (interval // 1000) == 0 and self.times[i] != 0:
                self.text_edit.appendPlainText(f'CPU usage: {str(self.cpu_data[i])}%')
                print(self.cpu_data[i])
        self.update_interval = interval // 1000
        self.timer.stop()
        self.timer.start(1000)
        self.timer.timeout.connect(self.update_cpu_usage)

    # Метод для обновления использования ЦП и записи данных в файл и на график
    def update_cpu_usage(self):
        cpu_percent = psutil.cpu_percent()
        self.cpu_data.append(cpu_percent)
        self.times.append(self.time_elapsed)
        # self.data['CPU Usage'] = cpu_percent
        # print(self.data['CPU Usage'])
        with open(self.log_file_name, 'a') as f:
            f.write(f'Time: {self.time_elapsed}s, CPU usage: {cpu_percent}%\n')
        if self.time_elapsed % self.update_interval == 0:
            self.text_edit.appendPlainText(f'CPU usage: {cpu_percent}%')
            self.axis.clear()
            self.axis.plot(self.times[::self.update_interval], self.cpu_data[::self.update_interval], color='#2ABf9E')
            self.axis.set_xlabel("Time (s)")
            self.axis.set_ylabel("CPU Usage (%)")
            self.canvas.draw()
        self.time_elapsed += 1

def main():
    app = QApplication(sys.argv)

    file = QtCore.QFile("style/style.qss")
    file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
    stream = QtCore.QTextStream(file)
    app.setStyleSheet(stream.readAll())

    window = Cpu()
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
