# signature_pad.py
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QMouseEvent, QPaintEvent, QPixmap
from PyQt5.QtCore import Qt, QPoint


class SignaturePad(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 150)
        self.setStyleSheet("border: 1px solid #ccc; background-color: white;")
        self.path = []
        self.pixmap = QPixmap(self.size())
        self.pixmap.fill(Qt.white)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)

        for i in range(1, len(self.path)):
            painter.drawLine(self.path[i - 1], self.path[i])

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.path.append(event.pos())
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton:
            self.path.append(event.pos())
            painter = QPainter(self.pixmap)
            pen = QPen(Qt.black, 2)
            painter.setPen(pen)
            if len(self.path) >= 2:
                painter.drawLine(self.path[-2], self.path[-1])
            self.update()

    def clear(self):
        self.path = []
        self.pixmap.fill(Qt.white)
        self.update()

    def get_signature_image(self):
        return self.pixmap
