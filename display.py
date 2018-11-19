from PyQt4 import QtCore, QtGui
import sys, os, math
import string, re

import char_edit_win

import numsys

loadGUI = False
if loadGUI:
    from PyQt4 import uic
    GUIForm, baseClass = uic.loadUiType('base.ui')
else:
    from ui_base import Ui_baseConverter
    GUIForm, baseClass = Ui_baseConverter, QtGui.QWidget

class rebaserProg(baseClass, GUIForm):
    def __init__(self, parent=None):
        super(rebaserProg, self).__init__(parent)
        self.setupUi(self)

        self.leftRealBaseInput.valueChanged.connect(self.checkBaseValue)
        self.leftImagBaseInput.valueChanged.connect(self.checkBaseValue)
        self.rightRealBaseInput.valueChanged.connect(self.checkBaseValue)
        self.rightImagBaseInput.valueChanged.connect(self.checkBaseValue)

        self.leftRealTextInput.textChanged.connect(self.checkInputText)
        self.leftImagTextInput.textChanged.connect(self.checkInputText)
        self.rightRealTextInput.textChanged.connect(self.checkInputText)
        self.rightImagTextInput.textChanged.connect(self.checkInputText)

        self.sgnInput.textEdited.connect(self.setSgn)
        self.sepInput.textEdited.connect(self.setSep)
        self.precInput.valueChanged.connect(self.setPrec)
        
        self.useRealCB.clicked.connect(self.setBaseClass)
        self.useImagCB.clicked.connect(self.setBaseClass)
        self.useCmpxCB.clicked.connect(self.setBaseClass)
        
        self.forceIntegerCB.toggled.connect(self.useInts)
        self.optionButton.toggled.connect(self.showOpts)
        self.invertButton.toggled.connect(self.flipInputs)
        self.orderButton.clicked.connect(self.editCharOrder)
        self.rebaseButton.toggled.connect(self.convertText)
        
        self._prec = 1000  # number of (base two) digits to be accurate to
        self._deci = 4  # number of decimals for base inputs
        self._sep = '.'
        self._sgn = '-'
        self._leftBase = 10   # set by checkBaseValue
        self._rightBase = 10  # - only use these for converting
        self._validBase = True  # if selected bases are valid
        self._charSet = string.printable.swapcase()  # ordered characters set
        self._leftAllowed = self._charSet[:10]  # characters allowed for input
        self._rightAllowed = self._charSet[:10]
        self._leftValidator = QtCore.QRegExp()
        self._rightValidator = QtCore.QRegExp()
        
        self._inputSide = 'left'
        self._realInput = self.leftRealTextInput
        self._imagInput = self.leftImagTextInput
        self._realOutput = self.rightRealTextInput
        self._imagOutput = self.rightImagTextInput

        self.useInts(True)
        self.showOpts(False)
        self.setBaseClass('real')
        self.rightRealTextInput.setReadOnly(True)
        self.rightImagTextInput.setReadOnly(True)
        self.setAllowedChars()

        self.topOverviewLabel.hide()  # labels not currently used
        self.bottomOverviewLabel.hide()

        self.useCmpxCB.hide()  # complex bases unknown right now
        
        #self.statusBar = QtGui.QStatusBar(self)  # bottom label instead is
        #self.statusBar.setMaximumHeight(22)      # a status bar
        #self.statusBar.setMinimumHeight(22)
        #self.verticalLayout.addWidget(self.statusBar, 4)
        #self.statusBar.showMessage('I am a test', 5000)  # str, msec
        #self.statusBar()
        #self.centerBottomLabel.hide()
        numsys.setPrec(self._prec)

        self._iconGen = iconGen()  # for fun
        ch = '0123456789A'[hash(os.urandom(9))%11]
        self.setWindowIcon(self._iconGen(ch))
         

    def convertText(self):
        "converts input text"

        if not self.rebaseButton.isChecked(): return
        if not self._validBase:
            self._realOutput.blockSignals(True); self._realOutput.setText('')
            self._imagOutput.blockSignals(True); self._imagOutput.setText('')
            self._realOutput.blockSignals(False)
            self._imagOutput.blockSignals(False)
            return

        inputs = [self.rightRealTextInput, self.rightImagTextInput,
                  self.leftRealTextInput, self.leftImagTextInput, ]

        # get bases
        if self._inputSide == 'left':
            in_base = self._leftBase
            out_base = self._rightBase
        elif self._inputSide == 'right':
            in_base = self._rightBase
            out_base = self._leftBase
        else: return
        
        # get text
        real_text = self._realInput.document().toPlainText()
        try: rtxt = unicode(real_text)
        except: rtxt = str(real_text)

        imag_text = self._imagInput.document().toPlainText()
        try: itxt = unicode(imag_text)
        except: itxt = str(imag_text)

        if not itxt: text = rtxt
        else: text = (rtxt, itxt)

        err = style = ''
        real = imag = ''
        
        try:
            converted = numsys.rebase(text, in_base, out_base,
                                      self._sgn, self._sep)
            if type(converted) in (tuple, numsys.numStor, ):
                real = converted[0]
                imag = converted[1]
            else:
                real = converted
        except Exception as err:
            style = 'background-color: rgb(218, 165, 32);'  # yellow
            style = 'background-color: rgb(192, 0, 0);'  # red
            
        self.centerTopLabel.setStyleSheet(style)
        self.centerTopLabel.setText(str(err))
        self.centerTopLabel.setToolTip(str(err))

##        self.centerBottomLabel.setStyleSheet(style)
##        self.centerBottomLabel.setText(str(err))
##        self.centerBottomLabel.setToolTip(str(err))
##

        # show output
        for i in inputs: i.blockSignals(True)
        self._realOutput.setText(real)
        self._imagOutput.setText(imag)
        for i in inputs: i.blockSignals(False)

    def editCharOrder(self):
        "opens a window to edit the character set"
        edit = char_edit_win.charEditor(self._charSet, parent=self)
        char_edit_win.app = app  # global app is used in charEditor
        edit.emitNewCharOrder.connect(self.newCharOrder)

        edit.setWindowIcon(self._iconGen('0'))
        edit.exec_()

    def checkInputText(self):
        "verifiy input text"
        try:
            editor = self.sender()
            name = str(editor.objectName()).lower()
        except AttributeError: return

        text = editor.document().toPlainText()
        try: text = unicode(text)
        except: text = str(text)

        if 'left' in name:
            validator = self._leftValidator
            base = self._leftBase
            allowed = self._leftAllowed
        elif 'right' in name:
            validator = self._rightValidator
            base = self._rightBase
            allowed = self._rightAllowed
        else: return
        

        if validator.exactMatch(text):  # valid characters
            # valid, but too many characters
            csep = text.count(self._sep)
            csgn = text.count(self._sgn)
            
            if csep > 1:
                tip = ('Radix point ({})'.format(self._sep) +
                       ' can not appear more than once')
                text = text[::-1].replace(self._sep, '', csep - 1)[::-1]
            elif csgn > 1:
                tip = ('Negative sign ({}) can not'.format(self._sgn) +
                       ' appear more than once')
                text = text[::-1].replace(self._sgn, '', csgn - 1)[::-1]
            elif self._sgn in text and text[0] != self._sgn:
                tip = ('Negative sign ({})'.format(self._sgn) +
                       ' must be leading the number')
                text = self._sgn + text.replace(self._sgn, '')

            # all clear
            else:
                self.convertText()
                return
        
        else:  # invalid character, put up tooltip
            if base == 0: extra = ''
            elif round(abs(base), self._deci) == 1: extra = self._sgn
            elif base.real < 0: extra = self._sep
            elif base.imag and base.real <= 0: extra = self._sep
            else: extra = self._sep + self._sgn
            
            allAllowed = set(''.join(allowed) + extra)
            notAllowed = set(text).difference(allAllowed)
            for i in notAllowed: text = text.replace(i, '')

            chars = repr(''.join(allowed))
            if chars[0] in 'ub': chars = chars[1:]
            chars = chars[1: -1]
            if len(chars) > 100:
                trim, cut = ' ...({} characters truncated)... ', 30
                trim = trim.format(len(allowed) - cut*2)
                chars = chars[:cut] + trim + chars[-cut:]

            txt = 'can only have the following characters'
            real, imag = base.real, base.imag
            real = int(real) if int(real) == real else real
            imag = int(imag) if int(imag) == imag else imag
            basename = str(real) if not imag else (
                        str(imag) + 'i' if not real else (
                         str(real) + (' + ' if imag > 0 else ' - ') +
                          str(abs(imag)) + 'i'))
            tip = 'Base {} {}:\n{}'.format(basename, txt, chars)

            if base == 0:
                tip = 'Base zero does not use any characters'

        editor.blockSignals(True)
        editor.setPlainText(text)
        editor.moveCursor(11)  # end of document
        editor.blockSignals(False)

        pos = editor.cursorRect().topRight()
        globPos = editor.mapToGlobal(pos)
        QtGui.QToolTip.showText(globPos, tip)

    def newCharOrder(self, lst):
        "sets the character set order to lst"
        seen = set(); add = seen.add
        saw = [x for x in lst if not (x in seen or add(x))]
        self._charSet = saw

        # update left and right sides for valid characters
        self.checkBaseValue('left'); self.checkBaseValue('right')
        numsys.setDigitSet(self._charSet)

    def setAllowedChars(self, base=3):
        "sets the validators with correct characters"
        def spec(chars):
            "formats special characters for regex"
            specials = '\\^$.|?*+(){}[]/'
            for i in specials:
                chars = chars.replace(i, '\\' + i)
            return chars

        if base == 0 or round(abs(base), self._deci) == 1:
            extra = self._sgn  # these two bases are incapable of fractions
        elif base.real < 0:  # uses no negative sign
            extra = self._sep
        elif base.imag and base.real <= 0:
            extra = self._sep
        else:
            extra = self._sep + self._sgn

        left = spec(''.join(self._leftAllowed) + extra)
        right = spec(''.join(self._rightAllowed) + extra)
        self._leftValidator.setPattern('^[' + left + ']*')
        self._rightValidator.setPattern('^[' + right + ']*')

    def checkBaseValue(self, value):
        "checks if base value input is valid and other related checks"
        # invalid bases are 1, 0, -1
        if value in ('left', 'right'): name = value
        else:
            try: name = str(self.sender().objectName()).lower()  # checkbox
            except AttributeError: name = 'left' # anything else

        # which side called 
        if 'left' in name:
            realInput = self.leftRealBaseInput
            imagInput = self.leftImagBaseInput
            baseLabel = self.leftTopLabel
            #self._leftBase
        elif 'right' in name:
            realInput = self.rightRealBaseInput
            imagInput = self.rightImagBaseInput
            baseLabel = self.rightTopLabel
            #self._rightBase
        else: return

        # disallow real and imag together when imaginary only bases
        if 'real' in name and self.useImagCB.isChecked():
            imagInput.blockSignals(True)
            imagInput.setValue(0)
            imagInput.blockSignals(False)
        elif 'imag' in name and self.useImagCB.isChecked():
            realInput.blockSignals(True)
            realInput.setValue(0)
            realInput.blockSignals(False)
        else: pass

        # parse base value
        real, imag = realInput.value(), imagInput.value()
        real, imag = round(real, self._deci), round(imag, self._deci)
        if self.forceIntegerCB.isChecked():
            real, imag = int(real), int(imag)
        base = real + (imag * 1j if imag else 0)

        # max base allowed and max characters that can be used
        maxChar = maxBase = len(self._charSet)
        if imag: maxChar = int(math.ceil(math.sqrt(maxBase)))
        realInput.setMaximum(maxChar);  imagInput.setMaximum(maxChar)
        realInput.setMinimum(-maxChar); imagInput.setMinimum(-maxChar)

        uses = base  # actual number of characters used by base

        if base.imag: uses = base * numsys.cmplx(base.real, -base.imag)  # can't use .conjugate(), gmpy2 2.0.8 crashes
        uses = abs(uses)
        if 0 < uses < 1: uses = int(round(math.ceil(1. / uses), self._deci))
        else: uses = int(math.ceil(round(uses, self._deci)))

        # set base
        if 'left' in name:
            self._leftBase = base
            self._leftAllowed = self._charSet[:uses]
        elif 'right' in name:
            self._rightBase = base
            self._rightAllowed = self._charSet[:uses]
        else: return

        # imaginary and complex bases where real <= 0
        # do not have imaginary parts - so do not show imag text input
        if 'left' in name:
            if self.useRealCB.isChecked() or (imag and real <= 0):
                self.leftImagTextInput.blockSignals(True)
                self.leftImagTextInput.setText('')
                self.leftImagTextInput.hide()
            else:
                self.leftImagTextInput.blockSignals(False)
                self.leftImagTextInput.show()
        if 'right' in name:
            if self.useRealCB.isChecked() or (imag and real <= 0):
                self.rightImagTextInput.blockSignals(True)
                self.rightImagTextInput.setText('')
                self.rightImagTextInput.hide()
            else:
                self.rightImagTextInput.blockSignals(False)
                self.rightImagTextInput.show()

        text = 'Base ' + (str(real) if not imag else (
                          str(imag) + 'i' if not real else (
                           str(real) + (' + ' if imag > 0 else ' - ') +
                            (str(abs(imag)) + 'i'))))
        extra = 'uses {:,} character{}'.format(uses, '' if uses == 1 else 's')
        
        valid_base = False  # various base checks and text update
        if base == 0 or round(abs(base), self._deci) == 1:
            text = 'Invalid ' + text
            style = 'background-color: rgb(192, 0, 0);'
        elif imag and uses > maxBase: 
            # base exceeds number of characters available
            style = 'background-color: rgb(218, 165, 32);'
            extra = extra.replace('uses', 'needs')
            extra = 'base exceeds available characters\n' + extra
        else:
            valid_base = True
            style = ''
            
        baseLabel.setStyleSheet(style)
        realInput.setStyleSheet(style)
        imagInput.setStyleSheet(style)
        baseLabel.setText(text + ' ')
        baseLabel.setToolTip(text + '\n' + extra)
        realInput.setToolTip(text)
        imagInput.setToolTip(text)

        self.setAllowedChars(base)
        if valid_base: self._validBase = True
        else: self._validBase = False
        self.convertText()
        return

    def setBaseClass(self, state):
        "set what kind of number to use in base inputs"
        try:  # called by checkboxes
            state = str(self.sender().text()).lower()
        except AttributeError:  # called by anything else
            state = str(state).lower()

        if state == 'real':
            self.leftImagBaseInput.hide()
            self.rightImagBaseInput.hide()
            self.leftImagBaseInput.blockSignals(True)
            self.rightImagBaseInput.blockSignals(True)
            self.leftImagBaseInput.setValue(0)
            self.rightImagBaseInput.setValue(0)

            self.leftImagTextInput.hide()
            self.rightImagTextInput.hide()
            self.leftImagTextInput.blockSignals(True)
            self.rightImagTextInput.blockSignals(True)
            self.leftImagTextInput.setText('')
            self.rightImagTextInput.setText('')
            
        elif state in ('imaginary', 'imag', 'complex', 'cmpx'):
            self.leftImagBaseInput.show()
            self.rightImagBaseInput.show()
            self.leftImagBaseInput.blockSignals(False)
            self.rightImagBaseInput.blockSignals(False)

            real = self.leftRealBaseInput.value()
            imag = self.leftImagBaseInput.value()
            if not (imag and real <= 0) or real:
                self.leftImagTextInput.show()
                self.leftImagTextInput.blockSignals(False)
            real = self.rightRealBaseInput.value()
            imag = self.rightImagBaseInput.value()
            if not (imag and real <= 0) or real:
                self.rightImagTextInput.show()
                self.rightImagTextInput.blockSignals(False)
        else:
            pass

    def flipInputs(self, state):
        "flips the input and output editors"
        flag = QtCore.Qt.TextInteractionFlag
        fl_19, fl_03 = flag(19), flag(3)
        in_style  = ''#background-color: rgb(255, 255, 255);'  # input color
        out_style = ''#background-color: rgb(200, 230, 240);'  # output color
        #Qt.NoTextInteraction    	0 	No interaction with the text is possible.
        #Qt.TextSelectableByMouse 	1 	Text can be selected with the mouse and copied to the clipboard using a context menu or standard keyboard shortcuts.
        #Qt.TextSelectableByKeyboard 	2 	Text can be selected with the cursor keys on the keyboard. A text cursor is shown.
        #Qt.LinksAccessibleByMouse 	4 	Links can be highlighted and activated with the mouse.
        #Qt.LinksAccessibleByKeyboard 	8 	Links can be focused using tab and activated with enter.
        #Qt.TextEditable         	16      The text is fully editable.

        if state:
            self._inputSide = 'right'
            self._realInput = self.rightRealTextInput
            self._imagInput = self.rightImagTextInput
            self._realOutput = self.leftRealTextInput
            self._imagOutput = self.leftImagTextInput

            self.rightRealTextInput.blockSignals(False)
            self.rightImagTextInput.blockSignals(False)
            self.leftRealTextInput.blockSignals(True)
            self.leftImagTextInput.blockSignals(True)

            self.rightRealTextInput.setReadOnly(False)
            self.rightImagTextInput.setReadOnly(False)
            self.leftRealTextInput.setReadOnly(True)
            self.leftImagTextInput.setReadOnly(True)

            self.rightRealTextInput.setStyleSheet(in_style)
            self.rightImagTextInput.setStyleSheet(in_style)
            self.leftRealTextInput.setStyleSheet(out_style)
            self.leftImagTextInput.setStyleSheet(out_style)

            self.rightRealTextInput.setTextInteractionFlags(fl_19)
            self.rightImagTextInput.setTextInteractionFlags(fl_19)
            self.leftRealTextInput.setTextInteractionFlags(fl_03)
            self.leftImagTextInput.setTextInteractionFlags(fl_03)
                        
            self.leftBottomLabel.setText('Output')
            self.rightBottomLabel.setText('Input')
            self.rebaseButton.setText('<< Rebase')
        else:
            self._inputSide = 'left'
            self._realInput = self.leftRealTextInput
            self._imagInput = self.leftImagTextInput
            self._realOutput = self.rightRealTextInput
            self._imagOutput = self.rightImagTextInput

            self.leftRealTextInput.blockSignals(False)
            self.leftImagTextInput.blockSignals(False)
            self.rightRealTextInput.blockSignals(True)
            self.rightImagTextInput.blockSignals(True)

            self.leftRealTextInput.setReadOnly(False)
            self.leftImagTextInput.setReadOnly(False)
            self.rightRealTextInput.setReadOnly(True)
            self.rightImagTextInput.setReadOnly(True)
            
            self.leftRealTextInput.setStyleSheet(in_style)
            self.leftImagTextInput.setStyleSheet(in_style)
            self.rightRealTextInput.setStyleSheet(out_style)
            self.rightImagTextInput.setStyleSheet(out_style)

            self.leftRealTextInput.setTextInteractionFlags(fl_19)
            self.leftImagTextInput.setTextInteractionFlags(fl_19)
            self.rightRealTextInput.setTextInteractionFlags(fl_03)
            self.rightImagTextInput.setTextInteractionFlags(fl_03)

            self.leftBottomLabel.setText('Input')
            self.rightBottomLabel.setText('Output')
            self.rebaseButton.setText('Rebase >>')
        self.convertText()

    def useInts(self, state):
        "settings for forcing integers in base inputs"
        if state:
            self.precInput.setEnabled(False)
            self.precInput.blockSignals(True)
            self.precInput.setValue(30)
            self.precInput.setSpecialValueText('Exact')
            self.sepInput.setEnabled(True)
            self.sepInput.blockSignals(False)
            
            self.leftRealBaseInput.setDecimals(0)
            self.leftImagBaseInput.setDecimals(0)
            self.rightRealBaseInput.setDecimals(0)
            self.rightImagBaseInput.setDecimals(0)

            step = pow(10, -self._deci)
            self.leftRealBaseInput.setSingleStep(1)
            self.leftImagBaseInput.setSingleStep(1)
            self.rightRealBaseInput.setSingleStep(1)
            self.rightImagBaseInput.setSingleStep(1)

        else:
            self.precInput.setEnabled(True)
            self.precInput.blockSignals(False)
            self.precInput.setValue(self._prec)
            self.precInput.setSpecialValueText('')
            self.sepInput.setEnabled(True)
            self.sepInput.blockSignals(False)
            
            self.leftRealBaseInput.setDecimals(self._deci)
            self.leftImagBaseInput.setDecimals(self._deci)
            self.rightRealBaseInput.setDecimals(self._deci)
            self.rightImagBaseInput.setDecimals(self._deci)

            step = pow(10, -self._deci)
            self.leftRealBaseInput.setSingleStep(step)
            self.leftImagBaseInput.setSingleStep(step)
            self.rightRealBaseInput.setSingleStep(step)
            self.rightImagBaseInput.setSingleStep(step)

    def showOpts(self, state):
        "hide/show the options"
        if state:
            self.classGroupBox.show()
            self.forceIntegerCB.show()
            
            self.precInput.show()
            self.sepInput.show()
            self.sgnInput.show()
            self.orderButton.show()
        else:
            self.classGroupBox.hide()
            self.forceIntegerCB.hide()
            
            self.precInput.hide()
            self.sepInput.hide()
            self.sgnInput.hide()
            self.orderButton.hide()

    def setSgn(self, sgn):
        try: sgn = unicode(sgn)
        except: sgn = str(sgn)
        if sgn: self._sgn = sgn
        self.checkBaseValue('left')  # update valid characters
        self.checkBaseValue('right')

    def setSep(self, sep):
        try: sep = unicode(sep)
        except: sep = str(sep)
        if sep: self._sep = sep
        self.checkBaseValue('left')
        self.checkBaseValue('right')

    def setPrec(self, prec):
        if prec: self._prec = prec
        numsys.setPrec(prec)


class iconGen(QtGui.QPixmap):
    "icon generator for program"
    def __init__(self):
        QtGui.QPixmap.__init__(self)

    def __call__(self, Chr):
        X, Y = 256, 256
        img = self.draw(QtGui.QPixmap(X, Y), X, Y, Chr)
        #img.save('testing%s.png' % Chr)
        return QtGui.QIcon(img)

    def draw(self, img, X, Y, Chr):
        p = QtGui.QPainter(img); p.translate(X // 2, Y // 2)
        p.setRenderHint(QtGui.QPainter.Antialiasing)

        font = QtGui.QFont("Times New Roman", X * 0.90)
        rect = QtCore.QRectF(); COL = QtCore.Qt.white
    
        rect.setTop(-Y / 2.0); rect.setLeft(-X / 2.0)
        rect.setBottom(Y / 2.0); rect.setRight(X / 2.0)

        bg = QtGui.QLinearGradient(0, -Y // 2, 0, Y // 2)
        bg.setColorAt(0.0, QtCore.Qt.gray); bg.setColorAt(0.35, QtCore.Qt.black)
        bg.setColorAt(0.65, QtCore.Qt.black)
        bg.setColorAt(1.0, QtCore.Qt.darkGray); p.setBrush(QtGui.QBrush(bg))
        
        p.setPen(QtCore.Qt.NoPen); p.drawRect(rect); p.setFont(font)
        bsh = QtGui.QBrush(COL,QtCore.Qt.SolidPattern); pen = QtGui.QPen()
        bsh.setColor(COL); pen.setColor(COL); p.setPen(pen); p.setBrush(bsh)
        p.drawText(rect, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter, Chr)
        
        return img


if __name__ == '__main__':
    global app
    app = QtGui.QApplication(sys.argv)  # note: app is used within Control
    app.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    w = rebaserProg(); w.show()

    w.resize(QtCore.QSize(355, 186))
    sys.exit(app.exec_())
