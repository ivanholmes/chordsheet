from PyQt5 import QtWidgets, QtGui


class MItemModel(QtGui.QStandardItemModel):
    """
    Special item model to ensure whole row is moved.
    """

    def dropMimeData(self, data, action, row, col, parent):
        """
        Always move the entire row, and don't allow column "shifting"
        """
        return super().dropMimeData(data, action, row, 0, parent)


class MProxyStyle(QtWidgets.QProxyStyle):
    """
    Proxy style to change the appearance of the TableView.
    """

    def drawPrimitive(self, element, option, painter, widget=None):
        """
        Draw a line across the entire row rather than just the column
        we're hovering over.
        """
        if element == self.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
            option_new = QtWidgets.QStyleOption(option)
            option_new.rect.setLeft(0)
            if widget:
                option_new.rect.setRight(widget.width())
            option = option_new
        super().drawPrimitive(element, option, painter, widget)


class MTableView(QtWidgets.QTableView):
    """
    Subclass the built in TableView to customise it.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.model = MItemModel()
        self.setModel(self.model)

        self.verticalHeader().hide()
        self.horizontalHeader().show()
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)

        self.setShowGrid(False)
        # self.setDragDropMode(self.InternalMove)
        # self.setDragDropOverwriteMode(False)

        # Set our custom style - this draws the drop indicator across the whole row
        self.setStyle(MProxyStyle())


class ChordTableView(MTableView):
    """
    Subclass MTableView to add properties just for the chord table.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.model.setHorizontalHeaderLabels(['Chord', 'Guitar voicing', 'Piano voicing'])

    def populate(self, cList):
        """
        Fill the table from a list of Chord objects.
        """
        self.model.removeRows(0, self.model.rowCount())
        for c in cList:
            rowList = [QtGui.QStandardItem(c.name), QtGui.QStandardItem(
                ",".join(c.voicings['guitar'] if 'guitar' in c.voicings.keys() else "")),
                QtGui.QStandardItem(
                ",".join(c.voicings['piano'] if 'piano' in c.voicings.keys() else ""))]
            for item in rowList:
                item.setEditable(False)
                item.setDropEnabled(False)

            self.model.appendRow(rowList)


class SectionTableView(MTableView):
    """
    Subclass MTableView to add properties just for the section table.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.model.setHorizontalHeaderLabels(['Name'])

    def populate(self, sList):
        """
        Fill the table from a list of Section objects.
        """
        self.model.removeRows(0, self.model.rowCount())
        for s in sList:
            rowList = [QtGui.QStandardItem(s.name)]
            for item in rowList:
                item.setEditable(False)
                item.setDropEnabled(False)

            self.model.appendRow(rowList)


class BlockTableView(MTableView):
    """
    Subclass MTableView to add properties just for the block table.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.model.setHorizontalHeaderLabels(['Chord', 'Length', 'Notes'])

    def populate(self, bList):
        """
        Fill the table from a list of Block objects.
        """
        self.model.removeRows(0, self.model.rowCount())
        for b in bList:
            rowList = [QtGui.QStandardItem((b.chord.name if b.chord else "")), QtGui.QStandardItem(
                str(b.length)), QtGui.QStandardItem(b.notes)]
            for item in rowList:
                item.setEditable(False)
                item.setDropEnabled(False)

            self.model.appendRow(rowList)
