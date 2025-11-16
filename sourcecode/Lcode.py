#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xcode-like C IDE in PyQt5 with QSS, file handling, build & run in terminal
"""

import sys, os
from pathlib import Path
from PyQt5.QtCore import Qt, QSize, QRegExp
from PyQt5.QtGui import QColor, QFont, QTextCharFormat, QSyntaxHighlighter
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QTabWidget, QTextEdit, QToolBar, QStatusBar, QLabel, QPlainTextEdit, QWidget, QAction

class CHighlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        self.rules = []
        self.init_formats()
        self.init_rules()

    def fmt(self, color, bold=False, italic=False):
        f = QTextCharFormat()
        f.setForeground(QColor(color))
        if bold: f.setFontWeight(QFont.Bold)
        f.setFontItalic(italic)
        return f

    def init_formats(self):
        self.keywordFmt = self.fmt('#d19a66', bold=True)
        self.typeFmt = self.fmt('#61afef')
        self.numFmt = self.fmt('#d19a66')
        self.strFmt = self.fmt('#98c379')
        self.commentFmt = self.fmt('#7f8c8d', italic=True)
        self.preFmt = self.fmt('#c678dd')

    def init_rules(self):
        kws = ['if','else','for','while','do','switch','case','break','continue','return','goto','sizeof','struct','union','enum','typedef','static','const','volatile','extern','register','inline','restrict']
        types = ['int','long','short','char','float','double','void','signed','unsigned','bool']
        for w in kws: self.rules.append((QRegExp(f'\b{w}\b'), self.keywordFmt))
        for t in types: self.rules.append((QRegExp(f'\b{t}\b'), self.typeFmt))
        self.rules.append((QRegExp(r'\b[0-9]+(\.[0-9]+)?\b'), self.numFmt))
        self.rules.append((QRegExp(r'".*"'), self.strFmt))
        self.rules.append((QRegExp(r"'.*'"), self.strFmt))
        self.rules.append((QRegExp(r'^\s*#.*'), self.preFmt))
        self.rules.append((QRegExp(r'//.*'), self.commentFmt))

    def highlightBlock(self, text):
        for pat, fmt in self.rules:
            i = pat.indexIn(text)
            while i >= 0:
                l = pat.matchedLength()
                self.setFormat(i, l, fmt)
                i = pat.indexIn(text, i + l)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.setFont(QFont('Menlo',12))
        self.setTabStopDistance(self.fontMetrics().width(' ')*4)
        self.setStyleSheet('background:#1e1e1e;color:#d4d4d4;border:none;')
        self.highlighter = CHighlighter(self.document())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Xcode-like C IDE')
        self.resize(1200,800)
        self.setupUI()

    def setupUI(self):
        self.setStyleSheet('''
            QMainWindow{background:#1e1e1e;}
            QTabWidget::pane{border:1px solid #3c3c3c;}
            QTabBar::tab{background:#2d2d2d;color:#d4d4d4;padding:5px;}
            QTabBar::tab:selected{background:#3c3c3c;}
            QToolBar{background:#2d2d2d;border:none;}
            QStatusBar{background:#2d2d2d;color:#d4d4d4;}
            QTextEdit{background:#1e1e1e;color:#d4d4d4;}
        ''')

        c = QWidget()
        l = QVBoxLayout(c)
        self.setCentralWidget(c)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.closeTab)
        l.addWidget(self.tabs)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFixedHeight(220)
        l.addWidget(self.console)

        tb = QToolBar('Main')
        tb.setIconSize(QSize(18,18))
        self.addToolBar(tb)

        sb = QStatusBar()
        self.setStatusBar(sb)
        self.cursorLabel = QLabel('Ln 1, Col 1')
        sb.addPermanentWidget(self.cursorLabel)

        newAct = QAction('New',self); newAct.triggered.connect(self.newFile); tb.addAction(newAct)
        openAct = QAction('Open',self); openAct.triggered.connect(self.openFile); tb.addAction(openAct)
        saveAct = QAction('Save',self); saveAct.triggered.connect(self.saveFile); tb.addAction(saveAct)
        runAct = QAction('Build & Run',self); runAct.triggered.connect(self.buildRun); tb.addAction(runAct)

        self.newFile()

    def currentEditor(self):
        return self.tabs.currentWidget()

    def newFile(self):
        e = CodeEditor()
        self.tabs.addTab(e,'untitled')
        self.tabs.setCurrentWidget(e)

    def openFile(self):
        path,_ = QFileDialog.getOpenFileName(self,'Open File','','C Files (*.c);;All Files (*)')
        if path:
            e = CodeEditor()
            with open(path,'r',encoding='utf-8') as f: e.setPlainText(f.read())
            e.file_path = path
            self.tabs.addTab(e,Path(path).name)
            self.tabs.setCurrentWidget(e)

    def saveFile(self):
        e = self.currentEditor()
        if not e.file_path:
            path,_ = QFileDialog.getSaveFileName(self,'Save File','','C Files (*.c);;All Files (*)')
            if not path: return
            e.file_path = path
            self.tabs.setTabText(self.tabs.currentIndex(),Path(path).name)
        with open(e.file_path,'w',encoding='utf-8') as f: f.write(e.toPlainText())

    def buildRun(self):
        e = self.currentEditor()
        if not e.file_path: self.saveFile()
        src = e.file_path
        exe = str(Path(src).with_suffix(''))
        os.system(f"gcc '{src}' -o '{exe}'")
        if os.path.exists(exe):
            self.console.append(f"Running: {exe}\n")
            os.system(f"x-terminal-emulator -e '{exe}' &")

    def closeTab(self, index):
        self.tabs.removeTab(index)

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__=='__main__': main()
