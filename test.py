import sys
import psutil
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QPlainTextEdit
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class Cpu(QWidget):
    def __init__(self):
        super().__init__()

        self.usage_icon_name()

        self.cpu_data = []

        self.timer = QTimer()
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.axis = self.figure.add_subplot(1, 1, 1)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QPushButton('1 second', clicked=lambda: self.start_timer(1000)))
        self.layout.addWidget(QPushButton('10 seconds', clicked=lambda: self.start_timer(10000)))
        self.layout.addWidget(QPushButton('1 minute', clicked=lambda: self.start_timer(60000)))
        self.layout.addWidget(QPushButton('clear logs', clicked=lambda: self.clear_usage_log()))

        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.canvas)

    def usage_icon_name(self):
        self.setWindowTitle('CPU Usage')
        self.setWindowIcon(QIcon('img/images.png'))
    def start_timer(self, time):
        self.timer.stop()
        self.timer.start(time)
        self.timer.timeout.connect(self.update_usage_log)

    def update_usage_log(self):
        cpu_percent = psutil.cpu_percent()
        self.cpu_data.append(cpu_percent)
        self.text_edit.appendPlainText(f'CPU usage: {cpu_percent}%')
        with open('cpu_usage.txt', 'a') as f:
            f.write(f'CPU usage: {cpu_percent}%\n')
        self.axis.clear()
        self.axis.plot(self.cpu_data, color='red')
        self.canvas.draw()

    def clear_usage_log(self):
        self.text_edit.clear()
        with open('cpu_usage.txt', 'wb'):
            pass


app = QApplication(sys.argv)

window = Cpu()

window.show()

sys.exit(app.exec_())
