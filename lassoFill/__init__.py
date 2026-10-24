# Lasso Fill - plugin para Krita
# Preenche a selecao a mao livre ao soltar a caneta (estilo laco fill do CSP).

__version__ = '1.0'
__author__ = 'JOÃO AGUIAR'
__email__ = 'joao.aguiar.est@gmail.com'
__url__ = 'https://github.com/JoaoAguiarEst'

import os
import time
from krita import Krita, Extension

try:
    from PyQt5.QtCore import QObject, QEvent, QTimer, Qt
    from PyQt5.QtWidgets import (QApplication, QToolButton, QLineEdit, QTextEdit,
                                 QPlainTextEdit, QAbstractSpinBox, QComboBox)
    PRESSES = (QEvent.MouseButtonPress, QEvent.TabletPress)
    RELEASES = (QEvent.MouseButtonRelease, QEvent.TabletRelease)
    KEYPRESS = QEvent.KeyPress
    TECLA = Qt.Key_N ############## LOCAL DE MUDAR O ATALHO A SUA PREFERENCIA -------------------------------------------------------
    SEM_MOD = Qt.NoModifier
except ImportError:
    from PyQt6.QtCore import QObject, QEvent, QTimer, Qt
    from PyQt6.QtWidgets import (QApplication, QToolButton, QLineEdit, QTextEdit,
                                 QPlainTextEdit, QAbstractSpinBox, QComboBox)
    PRESSES = (QEvent.Type.MouseButtonPress, QEvent.Type.TabletPress)
    RELEASES = (QEvent.Type.MouseButtonRelease, QEvent.Type.TabletRelease)
    KEYPRESS = QEvent.Type.KeyPress
    TECLA = Qt.Key.Key_N
    SEM_MOD = Qt.KeyboardModifier.NoModifier

LOG = os.path.join(os.path.expanduser("~"), "lassofill_log.txt")

CAMPOS_TEXTO = (QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox, QComboBox)


def log(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S ") + str(msg) + "\n")
    except Exception:
        pass


def assinatura(doc):
    """Resume a selecao atual pelo retangulo; None se nao ha selecao."""
    try:
        sel = doc.selection()
        if sel is None:
            return None
        x, y, w, h = sel.x(), sel.y(), sel.width(), sel.height()
        if w <= 0 or h <= 0:
            return None
        return (x, y, w, h)
    except Exception as e:
        log("erro assinatura: %r" % e)
        return None


def ferramenta_toolbox():
    """Nome do botao de ferramenta marcado na caixa de ferramentas, se achar."""
    try:
        win = Krita.instance().activeWindow()
        if win is None:
            return None
        for b in win.qwindow().findChildren(QToolButton):
            if b.isChecked() and b.isVisible() and b.objectName().startswith("KisTool"):
                return b.objectName()
    except Exception as e:
        log("erro toolbox: %r" % e)
    return None


def digitando_texto():
    """True se o foco esta num campo de texto (para nao roubar a tecla N)."""
    w = QApplication.focusWidget()
    return w is not None and isinstance(w, CAMPOS_TEXTO)


class Filtro(QObject):
    def __init__(self):
        super().__init__()
        self.ativo = True
        self.pendente = False
        self.antes = None
        self.tentativas = 0
        self.acao = None  # acao liga/desliga, definida pela extensao

    def eventFilter(self, obj, ev):
        try:
            t = ev.type()

            # LOCAL DO EVENTO DE ATALHO: tecla N liga/desliga -----------------------------------
            if t == KEYPRESS:
                if (ev.key() == TECLA and ev.modifiers() == SEM_MOD
                        and not ev.isAutoRepeat() and not digitando_texto()):
                    if self.acao is not None:
                        self.acao.toggle()
                    return True
                return False

            if not self.ativo or self.pendente:
                return False

            if t in PRESSES or t in RELEASES:
                if "Canvas" not in obj.metaObject().className():
                    return False
                doc = Krita.instance().activeDocument()
                if doc is None:
                    return False
                if t in PRESSES:
                    self.antes = assinatura(doc)
                else:
                    ferr = ferramenta_toolbox()
                    if ferr is not None and "SelectOutline" not in ferr:
                        return False
                    self.pendente = True
                    self.tentativas = 0
                    QTimer.singleShot(0, self.verificar) ### ------------- PODE-SE MODIFICAR PRA AUMENTAR O TEMPO DE RESPOSTA, TIPO: QTimer.singleShot(2000, self.verificar), QTimer.singleShot(100, self.verificar), QTimer.singleShot(50, self.verificar)
        except Exception as e:
            log("erro no filtro: %r" % e)
        return False

    def verificar(self):
        try:
            app = Krita.instance()
            doc = app.activeDocument()
            atual = assinatura(doc) if doc else None
            self.tentativas += 1
            if atual is not None and atual != self.antes:
                a = app.action("fill_selection_foreground_color")
                d = app.action("deselect")
                if a:
                    a.trigger()
                if d:
                    d.trigger()
                self.antes = None
                self.pendente = False
                return
            if self.tentativas < 75:
                QTimer.singleShot(20, self.verificar) ### ------------- PODE-SE MODIFICAR PRA AUMENTAR O TEMPO DE RESPOSTA, TIPO: QTimer.singleShot(2000, self.verificar), QTimer.singleShot(100, self.verificar), QTimer.singleShot(50, self.verificar)

                return
        except Exception as e:
            log("erro em verificar: %r" % e)
        self.pendente = False


class LassoFillExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.filtro = Filtro()

    def setup(self):
        QApplication.instance().installEventFilter(self.filtro)
        log("plugin carregado (v4)")

    def createActions(self, window):
        a = window.createAction("lasso_fill_toggle", "Lasso Fill (liga/desliga)", "tools/scripts")
        a.setCheckable(True)
        a.setChecked(True)
        a.toggled.connect(self.alternar)
        self.filtro.acao = a

    def alternar(self, v):
        self.filtro.ativo = v
        log("plugin %s" % ("ligado" if v else "desligado"))
        try:
            win = Krita.instance().activeWindow()
            if win:
                win.qwindow().statusBar().showMessage(
                    "Lasso Fill: " + ("LIGADO" if v else "DESLIGADO"), 2000)
        except Exception as e:
            log("erro mensagem: %r" % e)


Krita.instance().addExtension(LassoFillExtension(Krita.instance()))