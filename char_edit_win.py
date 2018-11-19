from PyQt4 import QtCore, QtGui
import sys, os, itertools
import string, random
import unicodedata
import time

loadGUI = False
if loadGUI:
    from PyQt4 import uic
    GUIForm, baseClass = uic.loadUiType('charEditor.ui')
else:
    from ui_charEditor import Ui_digitOrderEditor
    GUIForm, baseClass = Ui_digitOrderEditor, QtGui.QDialog

def _str(string=''):
    "unicode/str for Python 2 and 3"
    try: string = unicode(string)
    except: string = str(string)
    return string

def _chr(i):
    "unichr/chr for Python 2 and 3"
    try: c = unichr(i)
    except: c = chr(i)
    return c

def dedup(lst):
    "http://stackoverflow.com/a/480227"
    seen = set(); add = seen.add
    saw = [x for x in lst if not (x in seen or add(x))]
    return saw

def time_str(secs):
    "70 -> '1 minute, 10 seconds'"
    if not secs: return 'no time at all'
    D, H, M = 86400, 3600, 60
    d = int(secs // D); secs -= d * D
    h = int(secs // H); secs -= h * H
    m = int(secs // M); secs -= m * M

    if int(secs) == secs: ss = str(int(secs))
    else: ss = '{:0.03f}'.format(secs)

    sfx = ['s', '']
    ds = '{} day{}'.format(d, sfx[d == 1]) if d else ''
    hs = '{} hour{}'.format(h, sfx[h == 1]) if h else ''
    ms = '{} minute{}'.format(m, sfx[m == 1]) if m else ''
    ss = '{} second{}'.format(ss, sfx[secs == 1]) if secs else ''
    return ', ' .join(filter(None, (ds, hs, ms, ss)))

# '\u15e6'
class charEditor(baseClass, GUIForm):
    emitNewCharOrder = QtCore.pyqtSignal(list)
    
    def __init__(self, char_list='', parent=None):
        super(charEditor, self).__init__(parent)
        self.setupUi(self)

        self.char_list = char_list
        
        tmp1 = string.printable.swapcase()
        tmp2 = _str().join(map(_chr, range(sys.maxunicode + 1)))
        self._default_char_list = dedup(tmp1 + tmp2)

        if not char_list: self.char_list = self._default_char_list
        self._doOnce = False  # center on screen on first run
        self.eximportDir = '/'  # dir path for export/import funcs

        self.charTable = customTableWidget()
        self.charTable.setMinimumSize(QtCore.QSize(520, 350))
        self.charTableLayout.insertWidget(0, self.charTable)

        self.charTable.setDragDropOverwriteMode(False)
        self.charTable.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.charTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.charTable.setColumnCount(0)
        self.charTable.setRowCount(0)
        self.charTable.setWhatsThis('Character display table')
        
        self.charTable.horizontalHeader().setVisible(False)
        self.charTable.horizontalHeader().setHighlightSections(False)
        self.charTable.verticalHeader().setVisible(False)
        self.charTable.verticalHeader().setHighlightSections(False)

        self.charTable.horizontalHeader().setVisible(False)
        self.charTable.horizontalHeader().setHighlightSections(False)
        self.charTable.verticalHeader().setVisible(False)
        self.charTable.verticalHeader().setHighlightSections(False)

        self.charTable.itemSelectionChanged.connect(self.charInfo)
        self.shuffleButton.clicked.connect(self.shuffle)
        self.closeButton.clicked.connect(self.saveAndClose)
        self.defaultButton.clicked.connect(self.resetChars)
        self.exportButton.clicked.connect(self.exPort)
        self.importButton.clicked.connect(self.imPort)
        self.cancelButton.clicked.connect(self.cancelLoad)

        # sneakrets
        hide_the_secrets = True
        self.numCols = 30; self.itemSze = 30
        self.maxChrs = len(self._default_char_list)
        self.itemSize_input.valueChanged.connect(self.updateItemSze)
        self.numCol_input.valueChanged.connect(self.updateCols)
        self.maxChar_input.valueChanged.connect(self.truncate)
        self.updateTableButton.clicked.connect(self.populateTable)
        self.dev_stuff = [self.itemSize_input, self.numCol_input,
                          self.updateTableButton, self.maxChar_input]
        self.maxChar_input.setMaximum(len(self.char_list))
        self.maxChar_input.setValue(len(self.char_list))
        if hide_the_secrets:
            for i in self.dev_stuff: i.hide(); i.setEnabled(False)

        self.cancelButton.hide()
        self.stopImport = False
        self.cancelButton.setEnabled(False)

        # so ui shows before locking up
        QtCore.QTimer.singleShot(10, self.populateTable)

    def cancelLoad(self):
        "stop the file loading process"
        self.stopImport = True

    def exPort(self):
        "exports character order"
        fd = QtGui.QFileDialog()
        fd.setWindowIcon(self.windowIcon())
        title = 'Export character order...'
        savePath = fd.getSaveFileName(self, title, self.eximportDir, '.txt')
        if not savePath: return

        self.eximportDir = os.path.dirname(_str(savePath))
        with open(_str(savePath), 'wb') as dst:
            dst.write(_str('').join(self.getOrder()).encode('utf-8'))

        line = "Exported digit order to '{}'"
        self.infoLabel.setText(line.format(os.path.basename(_str(savePath))))

    def imPort(self):
        "imports character order"
        fd = QtGui.QFileDialog()
        fd.setWindowIcon(self.windowIcon())
        title = 'Import digit order...'
        openPath = _str(fd.getOpenFileName(self, title, self.eximportDir))
        if not openPath: return

        self.eximportDir = os.path.dirname(_str(openPath))

        locks = [self.exportButton, self.importButton, self.closeButton,
                 self.defaultButton, self.charTable, self.infoLabel,
                 self.shuffleButton, self.posiLabel, self.reprLabel,
                 self.charLabel] + self.dev_stuff
        for l in locks: l.setEnabled(False)
        #self.setEnabled(False)
        
        self.cancelButton.show()
        self.stopImport = False
        self.cancelButton.setEnabled(True)
        
        self.infoLabel.setText('Loading digit order...')
        chars = []; app.processEvents()
        
        fsize, blksize = os.path.getsize(openPath), 2**20
        tmpsize, mxu = 0.0, sys.maxunicode
        line = 'Loading digit order... ({:0.02%})'
        winTitle = self.windowTitle()
            
        t0 = time.clock()
        with open(openPath, 'rb') as src:
            while 1:  # done this way so large files can be used
                block = src.read(blksize)
                if not block: break  # no more file
                if len(chars) > mxu: break  # no more characters
                if self.stopImport: break  # asked to stop

                block = block.decode('utf-8', 'ignore')
                chars.extend(block); chars = dedup(chars)

                tmpsize += blksize
                tmp = line.format(tmpsize / fsize)
                self.infoLabel.setText(tmp)
                self.setWindowTitle(tmp)
                app.processEvents()
        t1 = time.clock()

        app.processEvents()
        self.cancelButton.setEnabled(False)
        self.cancelButton.hide()
        for l in locks: l.setEnabled(True)
        #self.setEnabled(True)
        app.processEvents()
        
        chars = dedup(chars)
        if '' in chars: chars.remove('')  # no empty characters
        
        self.char_list = chars
        self.maxChar_input.setMaximum(len(self.char_list))
        self.maxChar_input.setValue(len(self.char_list))
        line, nme = 'Loaded {} ({:,} characters)', os.path.basename(openPath)
        self.setWindowTitle(winTitle)
        self.populateTable()
        self.infoLabel.setText(line.format(nme, len(self.char_list)))

        
        info = 'Read {:0.3%} of file\nTook {}'
        if self.stopImport:  # amend info and reset 
            info = 'file input canceled\n' + info
            self.stopImport = False
        
        self.infoLabel.setToolTip(info.format(
            tmpsize / fsize if tmpsize <= fsize else 1,
            time_str(t1 - t0)))

    def getOrder(self):
        "returns the ordered digits from the table"
        chars = []
        numRows = self.charTable.rowCount() + 1
        numCols = self.charTable.columnCount() + 1

        for r, c in itertools.product(range(numRows), range(numCols)):
            item = self.charTable.item(r, c)
            if not item: continue
            if item.backgroundColor() == QtCore.Qt.lightGray: continue
            chars.append(item.data[-1])  # actual char stored here

        chars = dedup(chars)
        return chars

    def saveAndClose(self):
        "gather order of characters and return"
        self.setWindowTitle('Saving Order...')
        
        if self.parent() is None: self.exPort()
        else: self.emitNewCharOrder.emit(self.getOrder())

        self.close()

    def resetChars(self):
        "resets the character order to the default"
        self.char_list = self._default_char_list[:]
        self.maxChar_input.setMaximum(len(self.char_list))
        self.maxChar_input.setValue(len(self.char_list))
        self.populateTable()

    def shuffle(self):
        "randomizes the character order"
        self.setEnabled(False)
        lst = list(self.char_list)
        random.shuffle(lst)
        self.char_list = lst
        self.populateTable(lst)
        self.setEnabled(True)
        
    def charInfo(self):
        "populate sidebar info about selected item"
        lst = self.charTable.selectedItems()
        if not lst: return
        item = lst[0]
        dat = item.data
        
        self.charLabel.setText(item.text())
        self.posiLabel.setText(str(dat[0]))
        self.reprLabel.setText(dat[1])
        try:  # this probably isn't accurate due to different encodings
            nme = unicodedata.name(_str(item.text()))
            self.reprLabel.setToolTip(nme)
            self.infoLabel.setText(nme)
            self.infoLabel.setToolTip(nme)
        except:
            self.reprLabel.setToolTip(dat[1])
            self.infoLabel.setText(dat[1])
            self.infoLabel.setToolTip(dat[1])

    def updateCols(self, num):
        "changes the number of columns in display table"
        self.numCols = num

        font = self.maxChar_input.font()
        if not self.maxChrs % num: font.setBold(True)
        else: font.setBold(False)
        self.maxChar_input.setFont(font)

    def updateItemSze(self, num):
        "changes the size of character item box in display table"
        self.itemSze = num

    def truncate(self, num):
        "cuts the number of characters to num"
        self.maxChrs = num
        
        font = self.maxChar_input.font()
        if not num % self.numCols: font.setBold(True)
        else: font.setBold(False)
        self.maxChar_input.setFont(font)
        
    def populateTable(self, char_list=None):
        "fills character table with characters (hilarious ones)"
        self.charTable.setEnabled(False)
        self.setEnabled(False)

        t0 = time.clock()
        winTitle = self.windowTitle()
        self.setWindowTitle('Populating table...')
        self.infoLabel.setText('Populating table...')
        self.charTable.clearContents()

        numCols = self.numCols#30
        item_size = self.itemSze#30

        if char_list in (None, False): char_list = self.char_list
        char_list = char_list[:self.maxChrs]
        numChar = len(char_list)
        numRows = (numChar // numCols + (1 if numChar % numCols else 0)) or 1

        self.charTable.setRowCount(numRows)
        self.charTable.setColumnCount(numCols)
        for r in range(numRows + 1):
            self.charTable.setRowHeight(r, item_size)
        for c in range(numCols + 1):
            self.charTable.setColumnWidth(c, item_size)

        fntSz = item_size * 0.4
        font = QtGui.QFont(); font.setPointSize(fntSz if fntSz > 2 else 2)
        font.setKerning(False)

        flags = QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled
        flags = flags | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        charTip = _str('<html><p align="center">{}</p><p align="center">'
                       '<span style="font-size:50pt;">{}</span></p>'
                       '<p align="center">{}</p>')
        
        maxItems = float(numRows * numCols)
        for r, c in itertools.product(range(numRows), range(numCols)):
            item = QtGui.QTableWidgetItem(); item.setFont(font)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            item.setSizeHint(QtCore.QSize(item_size, item_size))

            posi = r*numCols + c
            if posi >= numChar:
                item.setFlags(QtCore.Qt.NoItemFlags)
                item.setBackgroundColor(QtCore.Qt.lightGray)  # empty item
            else:
                char = char_list[posi]
                rep = repr(char)
                if rep[0] in 'ub': rep = rep[1:]

                item.setFlags(flags)
                item.setText(char)

                item.setToolTip(charTip.format(posi, char, rep[1:-1]))
                item.data = [posi, rep[1:-1], char]  # tracking data for item

            self.charTable.setItem(r, c, item)

            if not r % 250:  # inform population process
                cent = ' ({:.02%})'.format(posi / maxItems)
                self.setWindowTitle('Populating table...' + cent)
                self.infoLabel.setText('Populating table...' + cent)

            app.processEvents()

        self.charTable.setMinimumWidth(self.charTable.sizeHint().width())
        self.charTable.setMaximumWidth(self.charTable.sizeHint().width())
        self.setMaximumWidth(self.sizeHint().width())

        self.setWindowTitle(winTitle)
        self.infoLabel.setText('')
        
        t1 = time.clock()
        #self.infoLabel.setToolTip('time to populate: ' + time_str(t1 - t0))
        
        self.charTable.setEnabled(True)
        self.setEnabled(True)

        if not self._doOnce:
            self.resize(self.sizeHint())
            self.centerOnScreen()
            self.infoLabel.setText('drag a character onto another to swap positions')
            self._doOnce = True

    def centerOnScreen(self):
        "http://bashelton.com/2009/06/pyqt-center-on-screen/"
        res = QtGui.QDesktopWidget().screenGeometry()
        self.move((res.width() / 2) - (self.frameSize().width() / 2),
                  (res.height() / 2) - (self.frameSize().height() / 2))


class customTableWidget(QtGui.QTableWidget):
    def dropEvent(self, dropEvent):
        "http://stackoverflow.com/a/16876995"  # modified from
        item_src = self.selectedItems()[0]
        item_dst = self.itemAt(dropEvent.pos())

        # check for invalid table items
        if item_dst is None: return
        if item_dst.backgroundColor() == QtCore.Qt.lightGray: return
        
        src_txt = item_src.text()
        dat = item_src.data[:]
    
        item_src.setText(item_dst.text())
        item_dst.setText(src_txt)
        
        item_src.data[1:] = item_dst.data[1:]
        item_dst.data[1:] = dat[1:]

        item_dst.setToolTip('\n'.join(map(_str, item_dst.data[:2])))
        item_src.setToolTip('\n'.join(map(_str, item_src.data[:2])))

    def sizeHint(self):
        "http://stackoverflow.com/a/7195443"  # modified from
        width = 0
        for i in range(self.columnCount()):
            width += self.columnWidth(i)
        if self.verticalHeader().isVisible():
            width += self.verticalHeader().sizeHint().width()
        if self.verticalScrollBar().isVisible():
            width += self.verticalScrollBar().sizeHint().width()
        width += self.frameWidth() * 2
        return QtCore.QSize(width, self.height())



if __name__ == '__main__':
    global app
    app = QtGui.QApplication(sys.argv)  # note: app is used within charEditor
    app.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    
    w = charEditor(); w.show()
    ico = w.style().standardIcon(QtGui.QStyle.SP_MessageBoxInformation)
    w.setWindowIcon(ico)
    sys.exit(app.exec_())

