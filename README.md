Lasso Fill:

Plugin que imita o Lasso Fill do Clip Studio Paint. Você desenha o contorno com a Seleção a Mão Livre e, ao soltar a caneta, a área é preenchida automaticamente com a cor selecionada.

Como usar:
1. Escolha a cor de selecionada que quer usar no preenchimento.
2. Selecione a camada onde quer pintar.
3. Escolha a ferramenta Seleção a Mão Livre (Freehand Selection).
4. Desenhe o contorno. A linha pontilhada aparece enquanto você desenha, sem pintar nada ainda.
5. Solte a caneta: a área é preenchida e a seleção é removida.
6. Você pode usar a tecla Alt junto pra subtrair a região pintada.

Ligar e desligar:
1. Aperte a tecla N para ligar ou desligar.
2. Uma mensagem aparece na barra de status: Lasso Fill: LIGADO ou DESLIGADO.
3. Também dá pelo menu Ferramentas -> Scripts -> Lasso Fill (liga/desliga).
4. O plugin sempre começa ligado quando o Krita abre.

Dicas:  
1. A tecla N é ignorada enquanto você digita em um campo de texto.
2. Para desfazer um preenchimento, use Ctrl+Z.
3. Para trocar a tecla, edite a linha TECLA = Qt.Key_N no arquivo __init__.py.

Solução de problemas:  
1. Não preenche: confira se o plugin está ligado (aperte N e veja a mensagem) e se a ferramenta ativa é a Seleção a Mão Livre.
2. Plugin não carrega: veja o arquivo lassofill_log.txt na sua pasta de usuário.

NOTA:  
1. Eu queria muito ter uma ferramenta igual a do lasso fill do CSP, tentei muitas vezes usar o Shapes Fill do Krita e tmbm tentei o Enclose and Fill Tool, mas não estava satisfeito, pesquisei em varios lugares pra mas sem sucesso, então decidi criar um eu mesmo, espero que quem for usar aproveite.
