#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 29 00:02:24 2019

@author: ivan
"""

import sys
import fitz
import io
import subprocess
import os
import time
from copy import copy

from PyQt5.QtWidgets import QApplication, QAction, QLabel, QDialogButtonBox, QDialog, QFileDialog, QMessageBox, QPushButton, QLineEdit, QCheckBox, QSpinBox, QDoubleSpinBox, QTableWidgetItem, QTabWidget, QComboBox, QWidget, QScrollArea, QMainWindow, QShortcut
from PyQt5.QtCore import QFile, QObject, Qt, pyqtSlot, QSettings
from PyQt5.QtGui import QPixmap, QImage, QKeySequence
from PyQt5 import uic
from chordsheet.tableView import ChordTableView, BlockTableView
from chordsheet.comboBox import MComboBox
from chordsheet.pdfViewer import PDFViewer

from reportlab.lib.units import mm, cm, inch, pica
from reportlab.lib.pagesizes import A4, A5, LETTER, LEGAL
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from chordsheet.document import Document, Style, Chord, Block, Section
from chordsheet.render import Renderer
from chordsheet.parsers import parseFingering, parseName

import _version

# set the directory where our files are depending on whether we're running a pyinstaller binary or not
if getattr(sys, 'frozen', False):
    scriptDir = sys._MEIPASS
else:
    scriptDir = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

# enable automatic high DPI scaling on Windows
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setOrganizationName("Ivan Holmes")
QApplication.setOrganizationDomain("ivanholmes.co.uk")
QApplication.setApplicationName("Chordsheet")
settings = QSettings()

pdfmetrics.registerFont(
    TTFont('FreeSans', os.path.join(scriptDir, 'fonts', 'FreeSans.ttf')))
if sys.platform == "darwin":
    pdfmetrics.registerFont(
        TTFont('HelveticaNeue', 'HelveticaNeue.ttc', subfontIndex=0))

# dictionaries for combo boxes
pageSizeDict = {'A4': A4, 'A5': A5, 'Letter': LETTER, 'Legal': LEGAL}
# point is 1 because reportlab's native unit is points.
unitDict = {'mm': mm, 'cm': cm, 'inch': inch, 'point': 1, 'pica': pica}


class DocumentWindow(QMainWindow):
    """
    Class for the main window of the application.
    """

    def __init__(self, doc, style, filename=None):
        """
        Initialisation function for the main window of the application.

        Arguments:
        doc -- the Document object for the window to use
        style -- the Style object for the window to use
        """
        super().__init__()

        self.doc = doc
        self.style = style
        self.renderer = Renderer(self.doc, self.style)

        self.lastDoc = copy(self.doc)
        self.currentFilePath = filename

        self.UIFileLoader(str(os.path.join(scriptDir, 'ui', 'mainwindow.ui')))
        self.UIInitStyle()
        self.updateChordDict()
        self.updateSectionDict()
        self.currentSection = None

        self.setCentralWidget(self.window.centralWidget)
        self.setMenuBar(self.window.menuBar)
        self.setWindowTitle("Chordsheet")

        if filename:
            try:
                self.openFile(filename)
            except Exception:
                UnreadableMessageBox().exec()

    def closeEvent(self, event):
        """
        Reimplement the built in closeEvent to allow asking the user to save.
        """
        if self.saveWarning():
            self.close()

    def UIFileLoader(self, ui_file):
        """
        Loads the .ui file for this window and connects the UI elements to their actions.
        """
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        self.window = uic.loadUi(ui_file)
        ui_file.close()

        # link all the UI elements
        self.window.actionAbout.triggered.connect(self.menuFileAboutAction)

        self.window.actionNew.triggered.connect(self.menuFileNewAction)
        self.window.actionOpen.triggered.connect(self.menuFileOpenAction)
        self.window.actionSave.triggered.connect(self.menuFileSaveAction)
        self.window.actionSave_as.triggered.connect(self.menuFileSaveAsAction)
        self.window.actionSave_PDF.triggered.connect(
            self.menuFileSavePDFAction)
        self.window.actionPrint.triggered.connect(self.menuFilePrintAction)
        self.window.actionClose.triggered.connect(self.menuFileCloseAction)
        self.window.actionUndo.triggered.connect(self.menuEditUndoAction)
        self.window.actionRedo.triggered.connect(self.menuEditRedoAction)
        self.window.actionCut.triggered.connect(self.menuEditCutAction)
        self.window.actionCopy.triggered.connect(self.menuEditCopyAction)
        self.window.actionPaste.triggered.connect(self.menuEditPasteAction)

        self.window.actionNew.setShortcut(QKeySequence.New)
        self.window.actionOpen.setShortcut(QKeySequence.Open)
        self.window.actionSave.setShortcut(QKeySequence.Save)
        self.window.actionSave_as.setShortcut(QKeySequence.SaveAs)
        self.window.actionSave_PDF.setShortcut(QKeySequence("Ctrl+E"))
        self.window.actionPrint.setShortcut(QKeySequence.Print)
        self.window.actionClose.setShortcut(QKeySequence.Close)
        self.window.actionUndo.setShortcut(QKeySequence.Undo)
        self.window.actionRedo.setShortcut(QKeySequence.Redo)
        self.window.actionCut.setShortcut(QKeySequence.Cut)
        self.window.actionCopy.setShortcut(QKeySequence.Copy)
        self.window.actionPaste.setShortcut(QKeySequence.Paste)

        self.window.pageSizeComboBox.currentIndexChanged.connect(
            self.pageSizeAction)
        self.window.documentUnitsComboBox.currentIndexChanged.connect(
            self.unitAction)

        self.window.includedFontCheckBox.stateChanged.connect(
            self.includedFontAction)

        self.window.generateButton.clicked.connect(self.generateAction)

        # update whole document when any tab is selected
        self.window.tabWidget.tabBarClicked.connect(self.tabBarUpdateAction)

        self.window.guitarVoicingButton.clicked.connect(
            self.guitarVoicingAction)
        self.window.addChordButton.clicked.connect(self.addChordAction)
        self.window.removeChordButton.clicked.connect(self.removeChordAction)
        self.window.updateChordButton.clicked.connect(self.updateChordAction)

        # connecting clicked only works for this combo box because it's my own modified version (MComboBox)
        self.window.blockSectionComboBox.clicked.connect(
            self.blockSectionClickedAction)
        self.window.blockSectionComboBox.currentIndexChanged.connect(
            self.blockSectionChangedAction)
        self.window.addBlockButton.clicked.connect(self.addBlockAction)
        self.window.removeBlockButton.clicked.connect(self.removeBlockAction)
        self.window.updateBlockButton.clicked.connect(self.updateBlockAction)

        self.window.addSectionButton.clicked.connect(self.addSectionAction)
        self.window.removeSectionButton.clicked.connect(
            self.removeSectionAction)
        self.window.updateSectionButton.clicked.connect(
            self.updateSectionAction)

        self.window.chordTableView.clicked.connect(self.chordClickedAction)
        self.window.sectionTableView.clicked.connect(self.sectionClickedAction)
        self.window.blockTableView.clicked.connect(self.blockClickedAction)

    def UIInitDocument(self):
        """
        Fills the window's fields with the values from its document.
        """
        self.updateTitleBar()

        # set all fields to appropriate values from document
        self.window.titleLineEdit.setText(self.doc.title)
        self.window.subtitleLineEdit.setText(self.doc.subtitle)
        self.window.composerLineEdit.setText(self.doc.composer)
        self.window.arrangerLineEdit.setText(self.doc.arranger)
        self.window.timeSignatureSpinBox.setValue(self.doc.timeSignature)
        self.window.tempoLineEdit.setText(self.doc.tempo)

        self.window.chordTableView.populate(self.doc.chordList)
        self.window.sectionTableView.populate(self.doc.sectionList)
        # populate the block table with the first section, account for a document with no sections
        self.currentSection = self.doc.sectionList[0] if len(
            self.doc.sectionList) else None
        self.window.blockTableView.populate(
            self.currentSection.blockList if self.currentSection else [])
        self.updateSectionDict()
        self.updateChordDict()

    def UIInitStyle(self):
        """
        Fills the window's fields with the values from its style.
        """
        self.window.pageSizeComboBox.addItems(list(pageSizeDict.keys()))
        self.window.pageSizeComboBox.setCurrentText(
            list(pageSizeDict.keys())[0])

        self.window.documentUnitsComboBox.addItems(list(unitDict.keys()))
        self.window.documentUnitsComboBox.setCurrentText(
            list(unitDict.keys())[0])

        self.window.lineSpacingDoubleSpinBox.setValue(self.style.lineSpacing)

        self.window.leftMarginLineEdit.setText(str(self.style.leftMargin))
        self.window.rightMarginLineEdit.setText(str(self.style.rightMargin))
        self.window.topMarginLineEdit.setText(str(self.style.topMargin))
        self.window.bottomMarginLineEdit.setText(str(self.style.bottomMargin))


        self.window.fontComboBox.setDisabled(True)
        self.window.includedFontCheckBox.setChecked(True)

        self.window.beatWidthLineEdit.setText(str(self.style.unitWidth))

    def tabBarUpdateAction(self, index):
        self.updateDocument()
    
    def pageSizeAction(self, index):
        self.pageSizeSelected = self.window.pageSizeComboBox.itemText(index)

    def unitAction(self, index):
        self.unitSelected = self.window.documentUnitsComboBox.itemText(index)

    def includedFontAction(self):
        if self.window.includedFontCheckBox.isChecked():
            self.style.useIncludedFont = True
        else:
            self.style.useIncludedFont = False

    def chordClickedAction(self, index):
        # set the controls to the values from the selected chord
        self.window.chordNameLineEdit.setText(
            self.window.chordTableView.model.item(index.row(), 0).text())
        self.window.guitarVoicingLineEdit.setText(
            self.window.chordTableView.model.item(index.row(), 1).text())
        self.window.pianoVoicingLineEdit.setText(
            self.window.chordTableView.model.item(index.row(), 2).text())

    def sectionClickedAction(self, index):
        # set the controls to the values from the selected section
        self.window.sectionNameLineEdit.setText(
            self.window.sectionTableView.model.item(index.row(), 0).text())
        # also set the combo box on the block page to make it flow well
        curSecName = self.window.sectionTableView.model.item(
            index.row(), 0).text()
        if curSecName:
            self.window.blockSectionComboBox.setCurrentText(
                curSecName)

    def blockSectionClickedAction(self, text):
        if text:
            self.updateBlocks(self.sectionDict[text])

    def blockSectionChangedAction(self, index):
        sName = self.window.blockSectionComboBox.currentText()
        if sName:
            self.currentSection = self.sectionDict[sName]
            self.window.blockTableView.populate(self.currentSection.blockList)
        else:
            self.currentSection = None

    def blockClickedAction(self, index):
        # set the controls to the values from the selected block
        bChord = self.window.blockTableView.model.item(index.row(), 0).text()
        self.window.blockChordComboBox.setCurrentText(
            bChord if bChord else "None")
        self.window.blockLengthLineEdit.setText(
            self.window.blockTableView.model.item(index.row(), 1).text())
        self.window.blockNotesLineEdit.setText(
            self.window.blockTableView.model.item(index.row(), 2).text())

    def getPath(self, value):
        """
        Wrapper for Qt settings to return home directory if no setting exists.
        """
        return str((settings.value(value) if settings.value(value) else os.path.expanduser("~")))

    def setPath(self, value, fullpath):
        """
        Wrapper for Qt settings to set path to open/save from next time from current file location.
        """
        return settings.setValue(value, os.path.dirname(fullpath))

    def menuFileNewAction(self):
        if self.saveWarning(): # ask the user if they want to save 
            self.doc = Document()  #  new document object
            # copy this object as reference to check against on quitting
            self.lastDoc = copy(self.doc)
            #  reset file path (this document hasn't been saved yet)
            self.currentFilePath = None
            # new renderer
            self.renderer = Renderer(self.doc, self.style)
            self.UIInitDocument()
            self.updatePreview()

    def menuFileOpenAction(self):
        if self.saveWarning(): # ask the user if they want to save 
            filePath = QFileDialog.getOpenFileName(self.window.tabWidget, 'Open file', self.getPath(
                "workingPath"), "Chordsheet Markup Language files (*.xml *.cml);;Chordsheet Macro files (*.cma)")[0]
            if filePath:
                self.openFile(filePath)

    def openFile(self, filePath):
        """
        Opens a file from a file path and sets up the window accordingly.
        """
        self.currentFilePath = filePath
        
        fileExt = os.path.splitext(self.currentFilePath)[1].lower()
        
        if fileExt == ".cma":
            self.doc.loadCSMacro(self.currentFilePath)
        else: # if fileExt in [".xml", ".cml"]:
            self.doc.loadXML(self.currentFilePath)
            
        self.lastDoc = copy(self.doc)
        self.setPath("workingPath", self.currentFilePath)
        self.UIInitDocument()
        self.updatePreview()

    def menuFileSaveAction(self):
        self.updateDocument()

        fileExt = os.path.splitext(self.currentFilePath)[1].lower()

        if self.currentFilePath and fileExt != ".cma":
            # Chordsheet Macro files can't be saved at this time
            self.saveFile(self.currentFilePath)
        else:
            filePath = QFileDialog.getSaveFileName(self.window.tabWidget, 'Save file', self.getPath(
                "workingPath"), "Chordsheet ML files (*.xml *.cml)")[0]
            if filePath:
                self.saveFile(filePath)

    def menuFileSaveAsAction(self):
        self.updateDocument()
        filePath = QFileDialog.getSaveFileName(self.window.tabWidget, 'Save file', self.getPath(
            "workingPath"), "Chordsheet ML files (*.xml *.cml)")[0]
        if filePath:
            self.saveFile(filePath)

    def saveFile(self, filePath):
        """
        Saves a file to given file path and sets up environment.
        """
        self.currentFilePath = filePath
        
        fileExt = os.path.splitext(self.currentFilePath)[1].lower()
        
        if fileExt == ".cma":
            # At this stage we should never get here
            pass
        else: # if fileExt in [".xml", ".cml"]:
            self.doc.saveXML(self.currentFilePath)
            
        self.lastDoc = copy(self.doc)
        self.setPath("workingPath", self.currentFilePath)
        self.updateTitleBar()  # as we may have a new filename

    def menuFileSavePDFAction(self):
        self.updateDocument()
        self.updatePreview()
        filePath = QFileDialog.getSaveFileName(self.window.tabWidget, 'Save file', self.getPath(
            "lastExportPath"), "PDF files (*.pdf)")[0]
        if filePath:
            self.renderer.savePDF(filePath)
            self.setPath("lastExportPath", filePath)

    def menuFilePrintAction(self):
        if sys.platform == "darwin":
            pass
        #    subprocess.call()
        else:
            pass

    @pyqtSlot()
    def menuFileCloseAction(self):
        self.saveWarning()

    def menuFileAboutAction(self):
        AboutDialog()

    def menuEditUndoAction(self):
        try:
            QApplication.focusWidget().undo()  # see if the built in widget supports it
        except Exception:
            pass  #  if not just fail silently

    def menuEditRedoAction(self):
        try:
            QApplication.focusWidget().redo()
        except Exception:
            pass

    def menuEditCutAction(self):
        try:
            QApplication.focusWidget().cut()
        except Exception:
            pass

    def menuEditCopyAction(self):
        try:
            QApplication.focusWidget().copy()
        except Exception:
            pass

    def menuEditPasteAction(self):
        try:
            QApplication.focusWidget().paste()
        except Exception:
            pass

    def saveWarning(self):
        """
        Function to check if the document has unsaved data in it and offer to save it.
        """
        self.updateDocument()  # update the document to catch all changes

        if self.lastDoc == self.doc:
            return True
        else:
            wantToSave = UnsavedMessageBox().exec()

            if wantToSave == QMessageBox.Save:
                if not self.currentFilePath:
                    filePath = QFileDialog.getSaveFileName(self.window.tabWidget, 'Save file', str(
                        os.path.expanduser("~")), "Chordsheet ML files (*.xml *.cml)")
                    self.currentFilePath = filePath[0]
                self.doc.saveXML(self.currentFilePath)
                return True

            elif wantToSave == QMessageBox.Discard:
                return True
            
            else:
                return False

    def guitarVoicingAction(self):
        gdialog = GuitarDialog()

        voicing = gdialog.getVoicing()
        if voicing:
            self.window.guitarVoicingLineEdit.setText(voicing)

    def clearChordLineEdits(self):
        self.window.chordNameLineEdit.clear()
        self.window.guitarVoicingLineEdit.clear()
        self.window.pianoVoicingLineEdit.clear()
        # necessary on Mojave with PyInstaller (or previous contents will be shown)
        self.window.chordNameLineEdit.repaint()
        self.window.guitarVoicingLineEdit.repaint()
        self.window.pianoVoicingLineEdit.repaint()

    def clearSectionLineEdits(self):
        self.window.sectionNameLineEdit.clear()
        # necessary on Mojave with PyInstaller (or previous contents will be shown)
        self.window.sectionNameLineEdit.repaint()

    def clearBlockLineEdits(self):
        self.window.blockLengthLineEdit.clear()
        self.window.blockNotesLineEdit.clear()
        # necessary on Mojave with PyInstaller (or previous contents will be shown)
        self.window.blockLengthLineEdit.repaint()
        self.window.blockNotesLineEdit.repaint()

    def updateChordDict(self):
        """
        Updates the dictionary used to generate the Chord menu (on the block tab)
        """
        self.chordDict = {'None': None}
        self.chordDict.update({c.name: c for c in self.doc.chordList})
        self.window.blockChordComboBox.clear()
        self.window.blockChordComboBox.addItems(list(self.chordDict.keys()))

    def updateSectionDict(self):
        """
        Updates the dictionary used to generate the Section menu (on the block tab)
        """
        self.sectionDict = {s.name: s for s in self.doc.sectionList}
        self.window.blockSectionComboBox.clear()
        self.window.blockSectionComboBox.addItems(
            list(self.sectionDict.keys()))

    def removeChordAction(self):
        if self.window.chordTableView.selectionModel().hasSelection():  #  check for selection
            self.updateChords()

            row = self.window.chordTableView.selectionModel().currentIndex().row()
            oldName = self.window.chordTableView.model.item(row, 0).text()
            self.doc.chordList.pop(row)

            self.window.chordTableView.populate(self.doc.chordList)
            # remove the chord if any of the blocks have it attached
            for s in self.doc.sectionList:
                    for b in s.blockList:
                        if b.chord:
                            if b.chord.name == oldName:
                                b.chord = None
            self.window.blockTableView.populate(self.currentSection.blockList)
            self.clearChordLineEdits()
            self.updateChordDict()

    def addChordAction(self):
        success = False  # initialise
        self.updateChords()

        cName = parseName(self.window.chordNameLineEdit.text())
        if cName:
            self.doc.chordList.append(Chord(cName))
            if self.window.guitarVoicingLineEdit.text() or self.window.pianoVoicingLineEdit.text():
                if self.window.guitarVoicingLineEdit.text():
                    try:
                        self.doc.chordList[-1].voicings['guitar'] = parseFingering(
                            self.window.guitarVoicingLineEdit.text(), 'guitar')
                        success = True  #  chord successfully parsed
                    except Exception:
                        VoicingWarningMessageBox().exec()  # Voicing is malformed,  warn user
                if self.window.pianoVoicingLineEdit.text():
                    try:
                        self.doc.chordList[-1].voicings['piano'] = parseFingering(
                            self.window.pianoVoicingLineEdit.text(), 'piano')
                        success = True  #  chord successfully parsed
                    except Exception:
                        VoicingWarningMessageBox().exec()  # Voicing is malformed,  warn user
            else:
                success = True  #  chord successfully parsed
        else:
            ChordNameWarningMessageBox().exec()  # Chord has no name, warn user

        if success == True:  # if chord was parsed properly
            self.window.chordTableView.populate(self.doc.chordList)
            self.clearChordLineEdits()
            self.updateChordDict()

    def updateChordAction(self):
        success = False  # see comments above
        if self.window.chordTableView.selectionModel().hasSelection():  #  check for selection
            self.updateChords()
            row = self.window.chordTableView.selectionModel().currentIndex().row()
            oldName = self.window.chordTableView.model.item(row, 0).text()
            cName = parseName(self.window.chordNameLineEdit.text())
            if cName:
                self.doc.chordList[row].name = cName
                if self.window.guitarVoicingLineEdit.text() or self.window.pianoVoicingLineEdit.text():
                    if self.window.guitarVoicingLineEdit.text():
                        try:
                            self.doc.chordList[row].voicings['guitar'] = parseFingering(
                                self.window.guitarVoicingLineEdit.text(), 'guitar')
                            success = True  #  chord successfully parsed
                        except Exception:
                            VoicingWarningMessageBox().exec()  # Voicing is malformed,  warn user
                    if self.window.pianoVoicingLineEdit.text():
                        try:
                            self.doc.chordList[row].voicings['piano'] = parseFingering(
                                self.window.pianoVoicingLineEdit.text(), 'piano')
                            success = True  #  chord successfully parsed
                        except Exception:
                            VoicingWarningMessageBox().exec()  # Voicing is malformed,  warn user
                else:
                    success = True  #  chord successfully parsed
            else:
                ChordNameWarningMessageBox().exec()

            if success == True:
                self.updateChordDict()
                self.window.chordTableView.populate(self.doc.chordList)
                # update the names of chords in all blocklists in case they've already been used
                for s in self.doc.sectionList:
                    for b in s.blockList:
                        if b.chord:
                            if b.chord.name == oldName:
                                b.chord.name = cName
                if self.currentSection and self.currentSection.blockList:
                    self.window.blockTableView.populate(self.currentSection.blockList)
                self.clearChordLineEdits()

    def removeSectionAction(self):
        if self.window.sectionTableView.selectionModel().hasSelection():  #  check for selection
            self.updateSections()

            row = self.window.sectionTableView.selectionModel().currentIndex().row()
            self.doc.sectionList.pop(row)

            self.window.sectionTableView.populate(self.doc.sectionList)
            self.clearSectionLineEdits()
            self.updateSectionDict()

    def addSectionAction(self):
        self.updateSections()

        sName = self.window.sectionNameLineEdit.text()
        if sName and sName not in [s.name for s in self.doc.sectionList]:
            self.doc.sectionList.append(Section(name=sName))
            self.window.sectionTableView.populate(self.doc.sectionList)
            self.clearSectionLineEdits()
            self.updateSectionDict()
        else:
            # Section has no name or non unique, warn user
            SectionNameWarningMessageBox().exec()

    def updateSectionAction(self):
        if self.window.sectionTableView.selectionModel().hasSelection():  #  check for selection
            self.updateSections()
            row = self.window.sectionTableView.selectionModel().currentIndex().row()

            sName = self.window.sectionNameLineEdit.text()
            if sName and sName not in [s.name for s in self.doc.sectionList]:
                self.doc.sectionList[row].name = sName
                self.window.sectionTableView.populate(self.doc.sectionList)
                self.clearSectionLineEdits()
                self.updateSectionDict()
            else:
                # Section has no name or non unique, warn user
                SectionNameWarningMessageBox().exec()

    def removeBlockAction(self):
        if self.window.blockTableView.selectionModel().hasSelection():  #  check for selection
            self.updateBlocks(self.currentSection)

            row = self.window.blockTableView.selectionModel().currentIndex().row()
            self.currentSection.blockList.pop(row)

            self.window.blockTableView.populate(self.currentSection.blockList)

    def addBlockAction(self):
        self.updateBlocks(self.currentSection)

        try:
            #  can the value entered for block length be cast as a float
            bLength = float(self.window.blockLengthLineEdit.text())
        except Exception:
            bLength = False

        if bLength:  # create the block
            self.currentSection.blockList.append(Block(bLength,
                                                       chord=self.chordDict[self.window.blockChordComboBox.currentText(
                                                       )],
                                                       notes=(self.window.blockNotesLineEdit.text() if not "" else None)))
            self.window.blockTableView.populate(self.currentSection.blockList)
            self.clearBlockLineEdits()
        else:
            # show warning that length was not entered or in wrong format
            LengthWarningMessageBox().exec()

    def updateBlockAction(self):
        if self.window.blockTableView.selectionModel().hasSelection():  #  check for selection
            self.updateBlocks(self.currentSection)

            try:
                #  can the value entered for block length be cast as a float
                bLength = float(self.window.blockLengthLineEdit.text())
            except Exception:
                bLength = False

            row = self.window.blockTableView.selectionModel().currentIndex().row()
            if bLength:
                self.currentSection.blockList[row] = (Block(bLength,
                                                            chord=self.chordDict[self.window.blockChordComboBox.currentText(
                                                            )],
                                                            notes=(self.window.blockNotesLineEdit.text() if not "" else None)))
                self.window.blockTableView.populate(
                    self.currentSection.blockList)
                self.clearBlockLineEdits()
            else:
                LengthWarningMessageBox().exec()

    def generateAction(self):
        self.updateDocument()
        self.updatePreview()

    def updatePreview(self):
        """
        Update the preview shown by rendering a new PDF and drawing it to the scroll area.
        """
        try:
            self.currentPreview = self.renderer.stream()
        except Exception:
            QMessageBox.warning(self, "Preview failed", "Could not update the preview.",
                                buttons=QMessageBox.Ok, defaultButton=QMessageBox.Ok)

        self.window.pdfArea.update(self.currentPreview)

    def updateTitleBar(self):
        """
        Update the application's title bar to reflect the current document.
        """
        if self.currentFilePath:
            self.setWindowTitle(_version.appName + " – " +
                                os.path.basename(self.currentFilePath))
        else:
            self.setWindowTitle(_version.appName)

    def updateChords(self):
        """
        Update the chord list by reading the table.
        """
        chordTableList = []
        for i in range(self.window.chordTableView.model.rowCount()):
            chordTableList.append(
                Chord(parseName(self.window.chordTableView.model.item(i, 0).text()))),
            if self.window.chordTableView.model.item(i, 1).text():
                chordTableList[-1].voicings['guitar'] = parseFingering(
                    self.window.chordTableView.model.item(i, 1).text(), 'guitar')
            if self.window.chordTableView.model.item(i, 2).text():
                chordTableList[-1].voicings['piano'] = parseFingering(
                    self.window.chordTableView.model.item(i, 2).text(), 'piano')

        self.doc.chordList = chordTableList

    def matchSection(self, nameToMatch):
        """
        Given the name of a section, this function checks if it is already present in the document. 
        If it is, it's returned. If not, a new section with the given name is returned.
        """
        section = None
        for s in self.doc.sectionList:
            if s.name == nameToMatch:
                section = s
                break
        if section is None:
            section = Section(name=nameToMatch)
        return section

    def updateSections(self):
        """
        Update the section list by reading the table
        """
        sectionTableList = []
        for i in range(self.window.sectionTableView.model.rowCount()):
            sectionTableList.append(self.matchSection(
                self.window.sectionTableView.model.item(i, 0).text()))

        self.doc.sectionList = sectionTableList

    def updateBlocks(self, section):
        """
        Update the block list by reading the table.
        """

        blockTableList = []
        for i in range(self.window.blockTableView.model.rowCount()):
            blockLength = float(
                self.window.blockTableView.model.item(i, 1).text())
            blockChord = self.chordDict[(self.window.blockTableView.model.item(
                i, 0).text() if self.window.blockTableView.model.item(i, 0).text() else "None")]
            blockNotes = self.window.blockTableView.model.item(i, 2).text(
            ) if self.window.blockTableView.model.item(i, 2).text() else None
            blockTableList.append(
                Block(blockLength, chord=blockChord, notes=blockNotes))

        section.blockList = blockTableList

    def updateDocument(self):
        """
        Update the Document object by reading values from the UI.
        """
        self.doc.title = self.window.titleLineEdit.text(
        )  # Title can be empty string but not None
        self.doc.subtitle = (self.window.subtitleLineEdit.text(
        ) if self.window.subtitleLineEdit.text() else None)
        self.doc.composer = (self.window.composerLineEdit.text(
        ) if self.window.composerLineEdit.text() else None)
        self.doc.arranger = (self.window.arrangerLineEdit.text(
        ) if self.window.arrangerLineEdit.text() else None)
        self.doc.tempo = (self.window.tempoLineEdit.text()
                          if self.window.tempoLineEdit.text() else None)
        self.doc.timeSignature = int(self.window.timeSignatureSpinBox.value(
        )) if self.window.timeSignatureSpinBox.value() else self.doc.timeSignature

        self.style.pageSize = pageSizeDict[self.pageSizeSelected]
        self.style.unit = unitDict[self.unitSelected]
        self.style.leftMargin = float(self.window.leftMarginLineEdit.text(
        )) if self.window.leftMarginLineEdit.text() else self.style.leftMargin
        self.style.rightMargin = float(self.window.rightMarginLineEdit.text(
        )) if self.window.rightMarginLineEdit.text() else self.style.rightMargin
        self.style.topMargin = float(self.window.topMarginLineEdit.text(
        )) if self.window.topMarginLineEdit.text() else self.style.topMargin
        self.style.bottomMargin = float(self.window.bottomMarginLineEdit.text(
        )) if self.window.bottomMarginLineEdit.text() else self.style.bottomMargin
        self.style.lineSpacing = float(self.window.lineSpacingDoubleSpinBox.value(
        )) if self.window.lineSpacingDoubleSpinBox.value() else self.style.lineSpacing

        # make sure the unit width isn't too wide to draw!
        if self.window.beatWidthLineEdit.text():
            if (self.style.pageSize[0] - 2 * self.style.leftMargin * mm) >= (float(self.window.beatWidthLineEdit.text()) * 2 * self.doc.timeSignature * mm):
                self.style.unitWidth = float(
                    self.window.beatWidthLineEdit.text())
            else:
                maxBeatWidth = (
                    self.style.pageSize[0] - 2 * self.style.leftMargin * mm) / (2 * self.doc.timeSignature * mm)
                QMessageBox.warning(self, "Out of range", "Beat width is out of range. It can be a maximum of {}.".format(
                    maxBeatWidth), buttons=QMessageBox.Ok, defaultButton=QMessageBox.Ok)

        # update chords, sections, blocks
        self.updateChords()
        self.updateSections()
        if self.currentSection:
            self.updateBlocks(self.currentSection)

        self.style.font = (
            'FreeSans' if self.style.useIncludedFont else 'HelveticaNeue')
        # something for the font box here


class GuitarDialog(QDialog):
    """
    Dialogue to allow the user to enter a guitar chord voicing. Not particularly advanced at present!
    May be extended in future.
    """

    def __init__(self):
        super().__init__()
        self.UIFileLoader(
            str(os.path.join(scriptDir, 'ui', 'guitardialog.ui')))

    def UIFileLoader(self, ui_file):
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        self.dialog = uic.loadUi(ui_file)
        ui_file.close()

    def getVoicing(self):
        """
        Show the dialogue and return the voicing that has been entered.
        """
        if self.dialog.exec_() == QDialog.Accepted:
            result = [self.dialog.ELineEdit.text(),
                      self.dialog.ALineEdit.text(),
                      self.dialog.DLineEdit.text(),
                      self.dialog.GLineEdit.text(),
                      self.dialog.BLineEdit.text(),
                      self.dialog.eLineEdit.text()]
            resultJoined = ",".join(result)
            return resultJoined
        else:
            return None


class AboutDialog(QDialog):
    """
    Dialogue showing information about the program.
    """

    def __init__(self):
        super().__init__()
        self.UIFileLoader(str(os.path.join(scriptDir, 'ui', 'aboutdialog.ui')))

        icon = QImage(str(os.path.join(scriptDir, 'ui', 'icon.png')))
        self.dialog.iconLabel.setPixmap(QPixmap.fromImage(icon).scaled(self.dialog.iconLabel.width(
        ), self.dialog.iconLabel.height(), Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation))

        self.dialog.versionLabel.setText("Version " + _version.version)

        self.dialog.exec()

    def UIFileLoader(self, ui_file):
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        self.dialog = uic.loadUi(ui_file)
        ui_file.close()


class UnsavedMessageBox(QMessageBox):
    """
    Message box to alert the user of unsaved changes and allow them to choose how to act.
    """

    def __init__(self):
        super().__init__()

        self.setIcon(QMessageBox.Question)
        self.setWindowTitle("Unsaved changes")
        self.setText("The document has been modified.")
        self.setInformativeText("Do you want to save your changes?")
        self.setStandardButtons(
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        self.setDefaultButton(QMessageBox.Save)


class UnreadableMessageBox(QMessageBox):
    """
    Message box to warn the user that the chosen file cannot be opened.
    """

    def __init__(self):
        super().__init__()

        self.setIcon(QMessageBox.Warning)
        self.setWindowTitle("File cannot be opened")
        self.setText("The file you have selected cannot be opened.")
        self.setInformativeText("Please make sure it is in the right format.")
        self.setStandardButtons(QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)


class ChordNameWarningMessageBox(QMessageBox):
    """
    Message box to warn the user that a chord must have a name
    """

    def __init__(self):
        super().__init__()

        self.setIcon(QMessageBox.Warning)
        self.setWindowTitle("Unnamed chord")
        self.setText("Chords must have a name.")
        self.setInformativeText("Please give your chord a name and try again.")
        self.setStandardButtons(QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)


class SectionNameWarningMessageBox(QMessageBox):
    """
    Message box to warn the user that a section must have a name
    """

    def __init__(self):
        super().__init__()

        self.setIcon(QMessageBox.Warning)
        self.setWindowTitle("Unnamed section")
        self.setText("Sections must have a unique name.")
        self.setInformativeText(
            "Please give your section a unique name and try again.")
        self.setStandardButtons(QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)


class VoicingWarningMessageBox(QMessageBox):
    """
    Message box to warn the user that the voicing entered could not be parsed
    """

    def __init__(self):
        super().__init__()

        self.setIcon(QMessageBox.Warning)
        self.setWindowTitle("Malformed voicing")
        self.setText(
            "The voicing you entered was not understood and has not been applied.")
        self.setInformativeText(
            "Please try re-entering it in the correct format.")
        self.setStandardButtons(QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)


class LengthWarningMessageBox(QMessageBox):
    """
    Message box to warn the user that a block must have a length
    """

    def __init__(self):
        super().__init__()

        self.setIcon(QMessageBox.Warning)
        self.setWindowTitle("Block without valid length")
        self.setText("Blocks must have a whole number length.")
        self.setInformativeText(
            "Please enter a valid length for your block and try again.")
        self.setStandardButtons(QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    d = Document()
    s = Style()

    # pass first argument as filename
    w = DocumentWindow(d, s, filename=(
        sys.argv[1] if len(sys.argv) > 1 else None))
    w.show()

    sys.exit(app.exec_())
