from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import pyqtSignal

class MComboBox(QComboBox):
    """
    Modified version of combobox that emits a signal with the current item when clicked.
    """
    clicked = pyqtSignal(str)

    def showPopup(self):
        self.clicked.emit(self.currentText())
        super().showPopup()