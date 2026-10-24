# Lasso Fill - plugin para Krita
# Preenche a selecao a mao livre ao soltar a caneta (estilo laco fill do CSP).

__version__ = '1.4'
__author__ = 'JOÃO AGUIAR'
__email__ = 'joao.aguiar.est@gmail.com'
__url__ = 'https://github.com/JoaoAguiarEst'

import os
import time
from krita import Krita, Extension

try:
    import numpy as np
except ImportError:
    np = None

try:
    from PyQt5.QtCore import QObject, QEvent, QTimer, Qt
    from PyQt5.QtWidgets import (QApplication, QToolButton, QLineEdit, QTextEdit,
                                 QPlainTextEdit, QAbstractSpinBox, QComboBox)
    PRESSES = (QEvent.MouseButtonPress, QEvent.TabletPress)
    RELEASES = (QEvent.MouseButtonRelease, QEvent.TabletRelease)
    KEYPRESS = QEvent.KeyPress
    TECLA = Qt.Key_N        # liga/desliga o plugin
    TECLA_MODO = Qt.Key_A   # alterna o modo de sobreposicao
    SEM_MOD = Qt.NoModifier
    ALT = Qt.AltModifier
except ImportError:
    from PyQt6.QtCore import QObject, QEvent, QTimer, Qt
    from PyQt6.QtWidgets import (QApplication, QToolButton, QLineEdit, QTextEdit,
                                 QPlainTextEdit, QAbstractSpinBox, QComboBox)
    PRESSES = (QEvent.Type.MouseButtonPress, QEvent.Type.TabletPress)
    RELEASES = (QEvent.Type.MouseButtonRelease, QEvent.Type.TabletRelease)
    KEYPRESS = QEvent.Type.KeyPress
    TECLA = Qt.Key.Key_N
    TECLA_MODO = Qt.Key.Key_A
    SEM_MOD = Qt.KeyboardModifier.NoModifier
    ALT = Qt.KeyboardModifier.AltModifier

LOG = os.path.join(os.path.expanduser("~"), "lassofill_log.txt")

CAMPOS_TEXTO = (QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox, QComboBox)

# Modos de sobreposicao
MODOS = ["Normal (sem mudança)", "Mais escuro", "Mais claro"]

# Quanto cada nivel escurece/clareia (0.0 a 1.0)
FORCA = 0.25

# False: o modo oposto sobe/desce um nivel por vez (padrao)
# True: o modo oposto devolve a area direto ao normal
OPOSTO_ZERA = False

# Limite interno do mapa de niveis (a cor ja saturou muito antes disso)
LIMITE = 100


def log(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S ") + str(msg) + "\n")
    except Exception:
        pass


def status(msg):
    try:
        win = Krita.instance().activeWindow()
        if win:
            win.qwindow().statusBar().showMessage(msg, 2000)
    except Exception as e:
        log("erro mensagem: %r" % e)


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


_botoes = {"win": None, "lista": []}


def ferramenta_toolbox():
    """Nome do botao de ferramenta marcado na caixa de ferramentas, se achar."""
    try:
        win = Krita.instance().activeWindow()
        if win is None:
            return None
        qwin = win.qwindow()
        if _botoes["win"] is not qwin or not _botoes["lista"]:
            _botoes["win"] = qwin
            _botoes["lista"] = [b for b in qwin.findChildren(QToolButton)
                                if b.objectName().startswith("KisTool")]
        for b in _botoes["lista"]:
            if b.isChecked() and b.isVisible():
                return b.objectName()
    except Exception as e:
        log("erro toolbox: %r" % e)
        _botoes["lista"] = []
    return None


def digitando_texto():
    """True se o foco esta num campo de texto (para nao roubar a tecla)."""
    w = QApplication.focusWidget()
    return w is not None and isinstance(w, CAMPOS_TEXTO)


def chave_camada(doc):
    """Identificador da camada ativa (a memoria e separada por camada)."""
    try:
        return doc.activeNode().uniqueId().toString()
    except Exception:
        return None


def ler_mascara(doc, sel):
    """Le a selecao so na caixa que ela ocupa (versao numpy).
    Retorna (x0, y0, mascara 2D uint8) ou None."""
    if sel is None:
        return None
    W, H = doc.width(), doc.height()
    x0 = max(0, sel.x())
    y0 = max(0, sel.y())
    x1 = min(W, sel.x() + sel.width())
    y1 = min(H, sel.y() + sel.height())
    if x1 <= x0 or y1 <= y0:
        return None
    w, h = x1 - x0, y1 - y0
    raw = bytes(sel.pixelData(x0, y0, w, h))
    if len(raw) != w * h:
        return None
    return x0, y0, np.frombuffer(raw, dtype=np.uint8).reshape(h, w)


def ajustar_pixels(doc, node, x0, y0, mask, niveis, adj):
    """Escurece (nivel<0) ou clareia (nivel>0) os pixels marcados em 'adj'."""
    if not adj.any():
        return
    # recorta para a menor caixa que contem o que precisa mudar
    linhas = np.flatnonzero(adj.any(axis=1))
    colunas = np.flatnonzero(adj.any(axis=0))
    ya, yb = linhas[0], linhas[-1] + 1
    xa, xb = colunas[0], colunas[-1] + 1
    mask = mask[ya:yb, xa:xb]
    niveis = niveis[ya:yb, xa:xb]
    adj = adj[ya:yb, xa:xb]
    x0 += int(xa)
    y0 += int(ya)
    h, w = mask.shape

    if node.colorModel() != "RGBA" or node.colorDepth() != "U8":
        log("sobreposicao ignorada: camada nao e RGBA 8 bits (%s %s)"
            % (node.colorModel(), node.colorDepth()))
        return
    raw = bytes(node.pixelData(x0, y0, w, h))
    if len(raw) != w * h * 4:
        log("sobreposicao ignorada: tamanhos inesperados")
        return

    d = np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 4).astype(np.float32)
    m = np.where(adj, mask.astype(np.float32) * (FORCA / 255.0), 0.0)
    k = np.abs(niveis).astype(np.float32)
    f = np.power(1.0 - m, k)[..., None]
    escuro = (niveis < 0)[..., None]
    rgb = d[..., :3]
    d[..., :3] = np.where(escuro, rgb * f, 255.0 - (255.0 - rgb) * f)
    saida = np.clip(d + 0.5, 0, 255).astype(np.uint8)
    node.setPixelData(saida.tobytes(), x0, y0, w, h)
    doc.refreshProjection()


class Filtro(QObject):
    def __init__(self):
        super().__init__()
        self.ativo = True
        self.pendente = False
        self.antes = None
        self.alt = False
        self.tentativas = 0
        self.acao = None      # acao liga/desliga, definida pela extensao
        self.modo = 0         # 0 normal, 1 escuro, 2 claro
        # memoria por camada (numpy: mapas L e P; sem numpy: bytearrays)
        self.memoria = {}
        self.avisou_numpy = False

    def alternar_modo(self):
        self.modo = (self.modo + 1) % len(MODOS)
        log("modo: %s" % MODOS[self.modo])
        status("Lasso Fill sobreposição: " + MODOS[self.modo])

    def limpar_memoria(self):
        self.memoria = {}
        log("memoria limpa")
        status("Lasso Fill: memória limpa")

    # ---------------- versao com numpy ----------------

    def mapas(self, doc, chave, criar=True):
        W, H = doc.width(), doc.height()
        est = self.memoria.get(chave)
        if est is not None and est["L"].shape != (H, W):
            est = None  # o documento mudou de tamanho
        if est is None and criar and chave is not None:
            est = {"L": np.zeros((H, W), dtype=np.int8),
                   "P": np.zeros((H, W), dtype=bool)}
            self.memoria[chave] = est
        return est

    # ---------------- versao sem numpy ----------------

    def mapas_py(self, doc, chave, criar=True):
        W, H = doc.width(), doc.height()
        est = self.memoria.get(chave)
        if est is not None and (est.get("W"), est.get("H")) != (W, H):
            est = None
        if est is None and criar and chave is not None:
            est = {"W": W, "H": H,
                   "L": bytearray([128]) * (W * H),   # 128 = nivel 0
                   "P": bytearray(W * H)}
            self.memoria[chave] = est
        return est

    def caixa_py(self, doc, sel):
        if sel is None:
            return None
        W, H = doc.width(), doc.height()
        x0, y0 = max(0, sel.x()), max(0, sel.y())
        x1 = min(W, sel.x() + sel.width())
        y1 = min(H, sel.y() + sel.height())
        if x1 <= x0 or y1 <= y0:
            return None
        w, h = x1 - x0, y1 - y0
        raw = bytes(sel.pixelData(x0, y0, w, h))
        if len(raw) != w * h:
            return None
        return x0, y0, w, h, raw

    def apagar_py(self, doc):
        est = self.mapas_py(doc, chave_camada(doc), criar=False)
        c = self.caixa_py(doc, doc.selection())
        if est is None or c is None:
            return
        x0, y0, w, h, raw = c
        W = est["W"]
        for yy in range(h):
            base = (y0 + yy) * W + x0
            for xx in range(w):
                if raw[yy * w + xx] >= 128:
                    est["P"][base + xx] = 0
                    est["L"][base + xx] = 128

    def preencher_py(self, app, doc):
        node = doc.activeNode()
        est = self.mapas_py(doc, chave_camada(doc))
        c = self.caixa_py(doc, doc.selection())
        ajustes = []
        x0 = y0 = w = h = 0
        if est is not None and c is not None:
            x0, y0, w, h, raw = c
            W = est["W"]
            L, P = est["L"], est["P"]
            delta = -1 if self.modo == 1 else 1
            for yy in range(h):
                base = (y0 + yy) * W + x0
                for xx in range(w):
                    m = raw[yy * w + xx]
                    if m < 128:
                        continue
                    i = base + xx
                    if self.modo == 0 or not P[i]:
                        L[i] = 128
                    else:
                        atual = L[i] - 128
                        if OPOSTO_ZERA and atual * delta < 0:
                            novo = 0
                        else:
                            novo = max(-LIMITE, min(LIMITE, atual + delta))
                        L[i] = novo + 128
                    P[i] = 1
                    if L[i] != 128:
                        ajustes.append((xx, yy, m, L[i] - 128))

        app.action("fill_selection_foreground_color").trigger()

        if ajustes and node is not None:
            doc.waitForDone()
            try:
                if node.colorModel() == "RGBA" and node.colorDepth() == "U8":
                    buf = bytearray(bytes(node.pixelData(x0, y0, w, h)))
                    for xx, yy, m, nv in ajustes:
                        f = (1.0 - m * FORCA / 255.0) ** abs(nv)
                        j = (yy * w + xx) * 4
                        for k in range(3):
                            v = buf[j + k]
                            if nv < 0:
                                buf[j + k] = int(v * f + 0.5)
                            else:
                                buf[j + k] = int(255 - (255 - v) * f + 0.5)
                    node.setPixelData(bytes(buf), x0, y0, w, h)
                    doc.refreshProjection()
            except Exception as e:
                log("erro ao ajustar (py): %r" % e)

        app.action("deselect").trigger()

    # ---------------- eventos ----------------

    def eventFilter(self, obj, ev):
        try:
            t = ev.type()

            if t == KEYPRESS:
                if (ev.modifiers() == SEM_MOD and not ev.isAutoRepeat()
                        and not digitando_texto()):
                    if ev.key() == TECLA:
                        if self.acao is not None:
                            self.acao.toggle()
                        return True
                    if ev.key() == TECLA_MODO:
                        self.alternar_modo()
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
                    self.alt = bool(ev.modifiers() & ALT)
                else:
                    ferr = ferramenta_toolbox()
                    if ferr is not None and "SelectOutline" not in ferr:
                        return False
                    self.pendente = True
                    self.tentativas = 0
                    QTimer.singleShot(0, self.verificar)
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
                if self.alt:
                    self.apagar(app, doc)
                else:
                    self.preencher(app, doc)
                self.antes = None
                self.pendente = False
                return
            if self.tentativas < 75:
                QTimer.singleShot(20, self.verificar)
                return
        except Exception as e:
            log("erro em verificar: %r" % e)
        self.pendente = False

    def apagar(self, app, doc):
        if self.antes is None:
            # Alt sem selecao previa: o Krita inverteu.
            # Inverte de volta, apaga a area do laco e limpa.
            app.action("invert_selection").trigger()
            doc.waitForDone()
            if np is None:
                self.apagar_py(doc)
            else:
                est = self.mapas(doc, chave_camada(doc), criar=False)
                if est is not None:
                    r = ler_mascara(doc, doc.selection())
                    if r is not None:
                        x0, y0, mask = r
                        h, w = mask.shape
                        dentro = mask >= 128
                        est["P"][y0:y0 + h, x0:x0 + w][dentro] = False
                        est["L"][y0:y0 + h, x0:x0 + w][dentro] = 0
            app.action("clear").trigger()
            app.action("deselect").trigger()
        # Se ja havia selecao, deixa o Krita subtrair normalmente.

    def preencher(self, app, doc):
        if np is None:
            if not self.avisou_numpy:
                log("numpy nao encontrado: usando metodo lento (sem numpy)")
                self.avisou_numpy = True
            self.preencher_py(app, doc)
            return

        node = doc.activeNode()
        chave = chave_camada(doc)
        est = self.mapas(doc, chave)
        r = ler_mascara(doc, doc.selection())

        niveis = None
        adj = None
        if r is not None and est is not None:
            x0, y0, mask = r
            h, w = mask.shape
            caixa = (slice(y0, y0 + h), slice(x0, x0 + w))
            dentro = mask >= 128
            Lb = est["L"][caixa].astype(np.int16)
            Pb = est["P"][caixa]

            if self.modo == 0:
                novo = np.where(dentro, 0, Lb)
            else:
                delta = -1 if self.modo == 1 else 1
                passo = Lb + delta
                if OPOSTO_ZERA:
                    passo = np.where(Lb * delta < 0, 0, passo)
                # area ja pintada: muda de nivel; area nova: fica normal
                novo = np.where(dentro & Pb, passo, np.where(dentro, 0, Lb))
            novo = np.clip(novo, -LIMITE, LIMITE)

            est["L"][caixa] = novo.astype(np.int8)
            est["P"][caixa] = Pb | dentro

            adj = dentro & (novo != 0)
            niveis = novo

        app.action("fill_selection_foreground_color").trigger()

        if adj is not None and node is not None and adj.any():
            doc.waitForDone()
            try:
                ajustar_pixels(doc, node, x0, y0, mask, niveis, adj)
            except Exception as e:
                log("erro ao ajustar nivel: %r" % e)

        app.action("deselect").trigger()


class LassoFillExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.filtro = Filtro()

    def setup(self):
        QApplication.instance().installEventFilter(self.filtro)
        log("plugin carregado (v8) | numpy: %s" % (np is not None))

    def createActions(self, window):
        a = window.createAction("lasso_fill_toggle", "Lasso Fill (liga/desliga)", "tools/scripts")
        a.setCheckable(True)
        a.setChecked(True)
        a.toggled.connect(self.alternar)
        self.filtro.acao = a

        m = window.createAction("lasso_fill_modo", "Lasso Fill: modo de sobreposição", "tools/scripts")
        m.triggered.connect(self.filtro.alternar_modo)

        c = window.createAction("lasso_fill_limpar", "Lasso Fill: limpar memória", "tools/scripts")
        c.triggered.connect(self.filtro.limpar_memoria)

    def alternar(self, v):
        self.filtro.ativo = v
        log("plugin %s" % ("ligado" if v else "desligado"))
        status("Lasso Fill: " + ("LIGADO" if v else "DESLIGADO"))


Krita.instance().addExtension(LassoFillExtension(Krita.instance()))