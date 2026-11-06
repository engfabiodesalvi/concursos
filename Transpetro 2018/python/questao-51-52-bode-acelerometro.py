"""
Diagramas de Bode do acelerometro (Transpetro 2018 - Eng. Junior Automacao,
Prova 21, questoes 51 e 52).

Modelo ajustado a figura da prova:

    G(s) = K * (s/wc)/(1 + s/wc) * wn^2 / (s^2 + 2*zeta*wn*s + wn^2)

  - (s/wc)/(1 + s/wc): passa-alta (acoplamento / eletronica de condicionamento)
  - wn^2/(s^2 + ...) : 2a ordem subamortecida (massa-mola-amortecedor)
  - K                : sensibilidade no patamar (-92 dB)

Uso:
    python bode_acelerometro.py            # mostra a janela e salva o PNG
    python bode_acelerometro.py --no-show  # apenas salva o PNG

Dependencias: numpy, matplotlib
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np

# ----------------------------------------------------------------------------
# Parametros ajustados a figura (valores lidos do grafico, nao da banca)
# ----------------------------------------------------------------------------
K_DB = -92.0       # ganho do patamar [dB]
WC = 10.0          # frequencia de canto do passa-alta [rad/s]
WN = 6300.0        # frequencia natural / ressonancia [rad/s]
ZETA = 0.01        # fator de amortecimento (Q = 1/(2*zeta) = 50)

W_MIN, W_MAX = 0.1, 1e5   # faixa de frequencia do grafico [rad/s]
N_PONTOS = 20000          # densidade alta para resolver o pico


def resposta_em_frequencia(w, k_db=K_DB, wc=WC, wn=WN, zeta=ZETA):
    """Retorna G(jw) complexo para o vetor de frequencias w [rad/s]."""
    s = 1j * w
    k = 10 ** (k_db / 20)
    passa_alta = (s / wc) / (1 + s / wc)
    segunda_ordem = wn**2 / (s**2 + 2 * zeta * wn * s + wn**2)
    return k * passa_alta * segunda_ordem


def modulo_db(g):
    return 20 * np.log10(np.abs(g))


def fase_graus(g):
    # np.angle fica em (-180, 180]; a figura da prova vai de +90 a -180,
    # entao nao ha necessidade de desenrolar a fase.
    return np.degrees(np.angle(g))


def plotar(mostrar=True, arquivo="bode_acelerometro.png"):
    w = np.logspace(np.log10(W_MIN), np.log10(W_MAX), N_PONTOS)
    g = resposta_em_frequencia(w)
    mag = modulo_db(g)
    fase = fase_graus(g)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

    # --- Modulo ---------------------------------------------------------
    ax1.semilogx(w, mag, color="black", lw=1.6)
    ax1.set_ylabel("Módulo (dB)")
    ax1.set_ylim(-140, -40)
    ax1.set_yticks(range(-140, -39, 10))
    ax1.grid(True, which="both", alpha=0.3)

    i_pico = int(np.argmax(mag))
    ax1.plot(w[i_pico], mag[i_pico], "o", color="tab:red", ms=6)
    ax1.annotate(
        f"Ressonância\n{w[i_pico]:.0f} rad/s | {mag[i_pico]:.1f} dB",
        xy=(w[i_pico], mag[i_pico]),
        xytext=(w[i_pico] * 0.04, mag[i_pico] + 2),
        arrowprops=dict(arrowstyle="->", color="tab:red"),
        color="tab:red",
    )
    ax1.axhline(K_DB, color="tab:blue", ls="--", lw=0.8)
    ax1.text(1.2e1, K_DB + 2, f"patamar ≈ {K_DB:.0f} dB",
             color="tab:blue", fontsize=9)
    ax1.axvspan(100, 1000, color="tab:green", alpha=0.12)
    ax1.text(105, -135, "faixa útil\n100–1000 rad/s", fontsize=8,
             color="tab:green", va="bottom")

    # --- Fase -----------------------------------------------------------
    ax2.semilogx(w, fase, color="black", lw=1.6)
    ax2.set_ylabel("Fase (graus)")
    ax2.set_xlabel("Frequência (rad/s)")
    ax2.set_ylim(-185, 95)
    ax2.set_yticks([-180, -90, 0, 90])
    ax2.grid(True, which="both", alpha=0.3)
    ax2.axvspan(100, 1000, color="tab:green", alpha=0.12)

    for ax in (ax1, ax2):
        ax.set_xlim(W_MIN, W_MAX)

    fig.suptitle("Acelerômetro: Diagramas de Bode (tensão de saída / aceleração)")
    fig.tight_layout()
    fig.savefig(arquivo, dpi=150)
    print(f"Figura salva em: {arquivo}")

    if mostrar:
        plt.show()
    plt.close(fig)


def relatorio():
    """Imprime valores-chave para conferir com a figura da prova."""
    pontos = [0.1, 1, 10, 100, 1000, 3000, WN, 1e4, 1e5]
    g = resposta_em_frequencia(np.array(pontos))
    print(f"{'w [rad/s]':>12} {'modulo [dB]':>13} {'fase [graus]':>14}")
    for wi, m, f in zip(pontos, modulo_db(g), fase_graus(g)):
        print(f"{wi:12.1f} {m:13.1f} {f:14.1f}")

    # Questao 52: ganho do amplificador para a faixa util (100 a 1000 rad/s)
    w_uteis = np.logspace(2, 3, 200)
    m_uteis = modulo_db(resposta_em_frequencia(w_uteis))
    print(f"\nFaixa util 100-1000 rad/s: modulo medio = {m_uteis.mean():.1f} dB")
    print(f"Ganho aproximado do amplificador: {-m_uteis.mean():.0f} dB")

    # Verificacao da questao 51: algum ponto com modulo >= 0 dB?
    w_all = np.logspace(np.log10(W_MIN), np.log10(W_MAX), N_PONTOS)
    pico = modulo_db(resposta_em_frequencia(w_all)).max()
    print(f"Maior valor de modulo em todo o espectro: {pico:.1f} dB (< 0 dB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--no-show", action="store_true",
                        help="não abre a janela, só salva o PNG")
    parser.add_argument("--saida", default="bode_acelerometro.png",
                        help="nome do arquivo PNG de saída")
    args = parser.parse_args()

    relatorio()
    plotar(mostrar=not args.no_show, arquivo=args.saida)
