#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, json
from pathlib import Path
from PyQt5.QtCore import Qt, QSize, QRegExp, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QColor, QFont, QTextCharFormat, QSyntaxHighlighter, QPalette
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QTabWidget, QTextEdit,
    QToolBar, QStatusBar, QLabel, QPlainTextEdit, QWidget, QAction,
    QDialog, QListWidget, QVBoxLayout, QGraphicsOpacityEffect, QPushButton, QHBoxLayout
)

LANG = "fr"
TR = {}


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
        self.keywordFmt = self.fmt('#e06c75', bold=True)
        self.typeFmt = self.fmt('#61afef', bold=True)
        self.numFmt = self.fmt('#d19a66')
        self.strFmt = self.fmt('#98c379')
        self.commentFmt = self.fmt('#5c6370', italic=True)
        self.preFmt = self.fmt('#c678dd')
        self.funcFmt = self.fmt('#56b6c2')

    def init_rules(self):
        kws = ['if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 'return', 'goto', 'sizeof',
               'struct', 'union', 'enum', 'typedef', 'static', 'const', 'volatile', 'extern', 'register', 'inline',
               'restrict']
        types = ['int', 'long', 'short', 'char', 'float', 'double', 'void', 'signed', 'unsigned', 'bool']
        for w in kws:
            self.rules.append((QRegExp(f'\\b{w}\\b'), self.keywordFmt))
        for t in types:
            self.rules.append((QRegExp(f'\\b{t}\\b'), self.typeFmt))
        self.rules.append((QRegExp(r'\b[0-9]+(\.[0-9]+)?\b'), self.numFmt))
        self.rules.append((QRegExp(r'"[^"\\]*(\\.[^"\\]*)*"'), self.strFmt))
        self.rules.append((QRegExp(r"'[^'\\]*(\\.[^'\\]*)*'"), self.strFmt))
        self.rules.append((QRegExp(r'^\s*#.*'), self.preFmt))
        self.rules.append((QRegExp(r'//[^\n]*'), self.commentFmt))
        self.rules.append((QRegExp(r'/\*.*?\*/'), self.commentFmt))
        self.rules.append((QRegExp(r'\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\()'), self.funcFmt))

    def highlightBlock(self, text):
        for pat, fmt in self.rules:
            i = pat.indexIn(text)
            while i >= 0:
                l = pat.matchedLength()
                self.setFormat(i, l, fmt)
                i = pat.indexIn(text, i + l)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.setFont(QFont('Consolas', 11))
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        self.setStyleSheet('''
            QPlainTextEdit {
                background: #282c34;
                color: #abb2bf;
                border: none;
                border-radius: 8px;
                padding: 10px;
                selection-background-color: #3e4451;
            }
        ''')
        self.highlighter = CHighlighter(self.document())

        # Line numbers
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())

    def lineNumberAreaPaintEvent(self, event):
        from PyQt5.QtGui import QPainter
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor('#21252b'))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor('#5c6370'))
                painter.setFont(self.font())
                painter.drawText(0, top, self.lineNumberArea.width() - 5,
                                 self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            from PyQt5.QtWidgets import QTextEdit
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor('#2c313c')
            selection.format.setBackground(lineColor)
            selection.format.setProperty(1, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)


class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet('''
            QPushButton {
                background: #61afef;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #528bca;
            }
            QPushButton:pressed {
                background: #4070a0;
            }
        ''')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('✨ Xcode 0.3 - Modern Edition')
        self.resize(1400, 900)
        self.setupUI()

    def setupUI(self):
        self.setStyleSheet('''
            QMainWindow {
                background: #1a1a1a;
            }
            QTabWidget::pane {
                border: 1px solid #2a2a2a;
                background: #1e1e1e;
                top: -1px;
            }
            QTabBar::tab {
                background: #252525;
                color: #cccccc;
                padding: 8px 16px;
                margin-right: 1px;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: #333333;
                color: #ffffff;
                border-bottom: 2px solid #e74c3c;
            }
            QTabBar::tab:hover:!selected {
                background: #2a2a2a;
            }
            QToolBar {
                background: #1a1a1a;
                border: none;
                border-bottom: 1px solid #2a2a2a;
                spacing: 5px;
                padding: 4px;
            }
            QToolBar QToolButton {
                background: #333333;
                color: #cccccc;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                padding: 6px 12px;
                font-size: 12px;
                margin: 1px;
            }
            QToolBar QToolButton:hover {
                background: #3a3a3a;
                border: 1px solid #e74c3c;
                color: #ffffff;
            }
            QToolBar QToolButton:pressed {
                background: #e74c3c;
                border: 1px solid #c0392b;
            }
            QStatusBar {
                background: #1a1a1a;
                color: #999999;
                border-top: 1px solid #2a2a2a;
                font-size: 11px;
            }
            QTextEdit {
                background: #1e1e1e;
                color: #cccccc;
                border: 1px solid #2a2a2a;
                padding: 5px;
                font-family: Consolas;
                font-size: 11pt;
            }
            QListWidget {
                background: #1e1e1e;
                color: #cccccc;
                border: 1px solid #2a2a2a;
                padding: 5px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                margin: 1px;
            }
            QListWidget::item:selected {
                background: #333333;
                color: #ffffff;
                border-left: 2px solid #e74c3c;
            }
            QListWidget::item:hover {
                background: #252525;
            }
            QDialog {
                background: #1e1e1e;
            }
        ''')

        c = QWidget()
        l = QVBoxLayout(c)
        l.setSpacing(10)
        l.setContentsMargins(15, 15, 15, 15)
        self.setCentralWidget(c)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.closeTab)
        l.addWidget(self.tabs)

        # Console avec titre
        consoleWidget = QWidget()
        consoleLayout = QVBoxLayout(consoleWidget)
        consoleLayout.setContentsMargins(0, 0, 0, 0)
        consoleLayout.setSpacing(5)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFixedHeight(200)
        consoleLayout.addWidget(self.console)

        l.addWidget(consoleWidget)

        tb = QToolBar('Main')
        tb.setIconSize(QSize(18, 18))
        tb.setMovable(False)
        self.addToolBar(tb)

        sb = QStatusBar()
        self.setStatusBar(sb)
        self.cursorLabel = QLabel('📍 Ln 1, Col 1')
        self.cursorLabel.setStyleSheet('color: #61afef; font-weight: bold;')
        sb.addPermanentWidget(self.cursorLabel)

        self.newAct = QAction('', self)
        self.newAct.triggered.connect(self.newFile)
        tb.addAction(self.newAct)

        self.openAct = QAction('', self)
        self.openAct.triggered.connect(self.openFile)
        tb.addAction(self.openAct)

        self.saveAct = QAction('', self)
        self.saveAct.triggered.connect(self.saveFile)
        tb.addAction(self.saveAct)

        tb.addSeparator()

        self.runAct = QAction('', self)
        self.runAct.triggered.connect(self.buildRun)
        tb.addAction(self.runAct)

        tb.addSeparator()

        self.changeLangAct = QAction('', self)
        self.changeLangAct.triggered.connect(self.openLanguageDialog)
        tb.addAction(self.changeLangAct)

        self.applyLanguage()
        self.newFile()

    def applyLanguage(self):
        tr = TR.get(LANG, {})
        en = TR.get('en', {})

        self.newAct.setText('📄 ' + tr.get('new', en.get('new', 'New')))
        self.openAct.setText('📂 ' + tr.get('open', en.get('open', 'Open')))
        self.saveAct.setText('💾 ' + tr.get('save', en.get('save', 'Save')))
        self.runAct.setText('▶️ ' + tr.get('run', en.get('run', 'Build & Run')))
        self.changeLangAct.setText('🌍 ' + tr.get('change_language', en.get('change_language', 'Change Language')))

        for i in range(self.tabs.count()):
            name = self.tabs.tabText(i)
            untitled_candidates = {v.get('untitled') for v in TR.values() if isinstance(v, dict)}
            if name in untitled_candidates:
                self.tabs.setTabText(i, tr.get('untitled', en.get('untitled', 'untitled')))

    def openLanguageDialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(
            '🌍 ' + TR.get(LANG, {}).get('select_language', TR.get('en', {}).get('select_language', 'Select Language')))
        dlg.setMinimumSize(400, 500)

        layout = QVBoxLayout(dlg)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel('🗣️ Choose Your Language')
        title.setStyleSheet('''
            QLabel {
                color: #61afef;
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }
        ''')
        layout.addWidget(title)

        lst = QListWidget(dlg)
        for key, val in TR.items():
            display = key
            if isinstance(val, dict) and 'name' in val:
                display = f"🌐 {val['name']} ({key})"
            lst.addItem(display)

        def on_double(item):
            code = item.text().split('(')[-1].rstrip(')')
            self.setLanguage(code, dlg)

        lst.itemDoubleClicked.connect(on_double)
        layout.addWidget(lst)

        btnLayout = QHBoxLayout()
        cancelBtn = AnimatedButton('❌ Cancel')
        cancelBtn.clicked.connect(dlg.close)
        btnLayout.addWidget(cancelBtn)
        layout.addLayout(btnLayout)

        dlg.exec_()

    def setLanguage(self, lang, dlg):
        global LANG
        if lang in TR:
            LANG = lang
        else:
            LANG = 'en'
        dlg.close()
        self.applyLanguage()
        self.console.append(f'✅ Language changed to: {TR.get(LANG, {}).get("name", lang)}\n')

    def currentEditor(self):
        return self.tabs.currentWidget()

    def newFile(self):
        e = CodeEditor()
        e.cursorPositionChanged.connect(self.updateCursorPosition)
        self.tabs.addTab(e, '📝 ' + TR.get(LANG, {}).get('untitled', TR.get('en', {}).get('untitled', 'untitled')))
        self.tabs.setCurrentWidget(e)
        self.console.append(f'✨ New file created\n')

    def openFile(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            TR.get(LANG, {}).get('open_file', TR.get('en', {}).get('open_file', 'Open File')),
            '',
            'C Files (*.c);;All Files (*)'
        )
        if path:
            e = CodeEditor()
            e.cursorPositionChanged.connect(self.updateCursorPosition)
            with open(path, 'r', encoding='utf-8') as f:
                e.setPlainText(f.read())
            e.file_path = path
            self.tabs.addTab(e, '📄 ' + Path(path).name)
            self.tabs.setCurrentWidget(e)
            self.console.append(f'✅ Opened: {Path(path).name}\n')

    def saveFile(self):
        e = self.currentEditor()
        if not e:
            return
        if not getattr(e, 'file_path', None):
            path, _ = QFileDialog.getSaveFileName(
                self,
                TR.get(LANG, {}).get('save_file', TR.get('en', {}).get('save_file', 'Save File')),
                '',
                'C Files (*.c);;All Files (*)'
            )
            if not path:
                return
            e.file_path = path
            self.tabs.setTabText(self.tabs.currentIndex(), '📄 ' + Path(path).name)
        with open(e.file_path, 'w', encoding='utf-8') as f:
            f.write(e.toPlainText())
        self.console.append(f'💾 Saved: {Path(e.file_path).name}\n')

    def buildRun(self):
        e = self.currentEditor()
        if not e:
            return
        if not getattr(e, 'file_path', None):
            self.saveFile()
        src = getattr(e, 'file_path', None)
        if not src:
            return
        exe = str(Path(src).with_suffix(''))
        self.console.append(f'⚙️ Compiling: {Path(src).name}...\n')
        result = os.system(f"gcc '{src}' -o '{exe}' 2>&1")
        if result == 0 and os.path.exists(exe):
            self.console.append(f'✅ Compilation successful!\n')
            self.console.append(f'▶️ Running: {Path(exe).name}\n')
            for term in ("x-terminal-emulator", "gnome-terminal", "konsole", "xterm"):
                if os.system(f"which {term} > /dev/null 2>&1") == 0:
                    os.system(f"{term} -e '{exe}' &")
                    break
        else:
            self.console.append(f'❌ Compilation failed!\n')

    def closeTab(self, index):
        self.tabs.removeTab(index)

    def updateCursorPosition(self):
        e = self.currentEditor()
        if e:
            cursor = e.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            self.cursorLabel.setText(f'📍 Ln {line}, Col {col}')


def main():
    global TR
    try:
        with open('language.json', 'r', encoding='utf-8') as f:
            TR = json.load(f)
    except Exception:
        TR = {
            'en': {
                'new': 'New', 'open': 'Open', 'save': 'Save', 'run': 'Build & Run',
                'untitled': 'untitled', 'open_file': 'Open File', 'save_file': 'Save File',
                'change_language': 'Change Language', 'select_language': 'Select Language'
            }
        }

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Palette sombre personnalisée
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(40, 44, 52))
    palette.setColor(QPalette.WindowText, QColor(171, 178, 191))
    palette.setColor(QPalette.Base, QColor(33, 37, 43))
    palette.setColor(QPalette.AlternateBase, QColor(44, 49, 60))
    palette.setColor(QPalette.Text, QColor(171, 178, 191))
    palette.setColor(QPalette.Button, QColor(97, 175, 239))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    app.setPalette(palette)

    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
