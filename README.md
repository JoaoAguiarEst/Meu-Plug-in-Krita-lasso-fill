# Lasso Fill

Plugin para Krita que imita o **Lasso Fill do Clip Studio Paint**. Você desenha o contorno com a Seleção a Mão Livre e, ao soltar a caneta, a área é preenchida automaticamente com a cor de frente.

## Como usar

1. Escolha a cor de frente que quer usar no preenchimento.
2. Selecione a camada onde quer pintar.
3. Escolha a ferramenta **Seleção a Mão Livre** (Freehand Selection).
4. Desenhe o contorno. A linha pontilhada aparece enquanto você desenha, sem pintar nada ainda.
5. Solte a caneta: a área é preenchida e a seleção é removida.
6. Segure **Alt** ao desenhar o laço para **apagar** o que estiver dentro dele (na camada ativa).

## Ligar e desligar

1. Aperte a tecla **N** para ligar ou desligar o plugin.
2. Uma mensagem aparece na barra de status: *Lasso Fill: LIGADO* ou *DESLIGADO*.
3. Também dá pelo menu **Ferramentas → Scripts → Lasso Fill (liga/desliga)**.
4. O plugin sempre começa ligado quando o Krita abre.

## Modos de sobreposição

Quando um laço novo cruza uma área que já foi preenchida pelo plugin, você pode escolher o que acontece na região de encontro. Aperte **M** para alternar entre:

- **Normal (sem mudança):** a área fica com a cor normal.
- **Mais escuro:** a região de encontro escurece. Repetir soma, até chegar ao preto.
- **Mais claro:** a região de encontro clareia. Repetir soma, até chegar ao branco.

O modo atual aparece na barra de status. Usar o modo oposto sobre uma área já ajustada desce ou sobe um nível por vez, passando pelo normal.

Para limpar o que o plugin lembra das áreas pintadas, use **Ferramentas → Scripts → Lasso Fill: limpar memória**.

### Ajustes no topo do `__init__.py`

| Variável | O que faz |
|---|---|
| `FORCA` | Intensidade de cada passada (`0.1` sutil, `0.5` forte). Padrão `0.25`. |
| `OPOSTO_ZERA` | `True`: o modo oposto devolve a área direto ao normal. `False` (padrão): muda um nível por vez. |
| `TECLA` | Tecla de liga/desliga (padrão `N`). |
| `TECLA_MODO` | Tecla de troca de modo (padrão `A`). |

## Dicas

1. As teclas N e M são ignoradas enquanto você digita em um campo de texto.
2. Para desfazer um preenchimento, use **Ctrl+Z**. O plugin não percebe o desfazer, então, se os tons ficarem confusos, use **Limpar memória**.
3. Para trocar uma tecla, edite a linha correspondente (`TECLA = Qt.Key_N`) no arquivo `__init__.py`.
4. A sobreposição funciona em camadas de pintura RGBA de 8 bits (o padrão do Krita).
5. Com numpy disponível, o cálculo é rápido. Sem ele, o plugin usa um método de reserva mais lento em laços grandes.

## Solução de problemas

1. **Não preenche:** confira se o plugin está ligado (aperte N e veja a mensagem) e se a ferramenta ativa é a Seleção a Mão Livre.
2. **Escuro/claro não muda nada:** abra o `lassofill_log.txt` e veja a linha `plugin carregado ... | numpy: ...`. Se não houver erros, confira o modo na barra de status (tecla M).
3. **Plugin não carrega:** veja o arquivo `lassofill_log.txt` na sua pasta de usuário.

## Nota

Eu queria muito ter uma ferramenta igual ao Lasso Fill do CSP. Tentei muitas vezes usar o Shapes Fill do Krita e também a Enclose and Fill Tool, mas não fiquei satisfeito. Pesquisei em vários lugares, sem sucesso, então decidi criar um eu mesmo. Espero que quem for usar aproveite.
