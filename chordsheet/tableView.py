import sys
from PyQt5 import QtWidgets, QtGui, QtCore

class MItemModel(QtGui.QStandardItemModel):

    def dropMimeData(self, data, action, row, col, parent):
        """
        Always move the entire row, and don't allow column "shifting"
        """
        return super().dropMimeData(data, action, row, 0, parent)
	
class MProxyStyle(QtWidgets.QProxyStyle):

    def drawPrimitive(self, element, option, painter, widget=None):
        """
        Draw a line across the entire row rather than just the column
        we're hovering over.  This may not always work depending on global
        style.
        """
        if element == self.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
            option_new = QtWidgets.QStyleOption(option)
            option_new.rect.setLeft(0)
            if widget:
                option_new.rect.setRight(widget.width())
            option = option_new
        super().drawPrimitive(element, option, painter, widget)

class MTableView(QtWidgets.QTableView):

    def __init__(self, parent):
        super().__init__(parent)

        self.verticalHeader().hide()
        self.horizontalHeader().show()
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.setShowGrid(False)
        #self.setDragDropMode(self.InternalMove)
        #self.setDragDropOverwriteMode(False)

        # Set our custom style - this draws the drop indicator across the whole row
        self.setStyle(MProxyStyle())

        self.model =  MItemModel()
        self.setModel(self.model)

class ChordTableView(MTableView):

    def __init__(self, parent):
        super().__init__(parent)

        self.model.setHorizontalHeaderLabels(['Chord', 'Voicing'])

    def populate(self, cList):
        self.model.removeRows(0, self.model.rowCount())
        for c in cList:
            rowList = [QtGui.QStandardItem(c.name), QtGui.QStandardItem(",".join(c.guitar if hasattr(c, 'guitar') else ""))]
            for item in rowList:
                item.setEditable(False)
                item.setDropEnabled(False)

            self.model.appendRow(rowList)

class BlockTableView(MTableView):

    def __init__(self, parent):
        super().__init__(parent)

        self.model.setHorizontalHeaderLabels(['Chord', 'Length', 'Notes'])

    def populate(self, bList):
        self.model.removeRows(0, self.model.rowCount())
        for b in bList:
            rowList = [QtGui.QStandardItem((b.chord.name if b.chord else "")), QtGui.QStandardItem(str(b.length)), QtGui.QStandardItem(b.notes)]
            for item in rowList:
                item.setEditable(False)
                item.setDropEnabled(False)

            self.model.appendRow(rowList)