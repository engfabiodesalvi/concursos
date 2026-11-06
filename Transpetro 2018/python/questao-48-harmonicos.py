b"""
Questão 48 - Transpetro / Cesgranrio
Enunciado: "Uma forma de onda periódica que possui somente o primeiro harmônico
(ou frequência fundamental) é ..."

Este script gera, para cada alternativa (A a E):
  1. A forma de onda no tempo (2 períodos);
  2. O espectro de amplitudes (Série de Fourier via FFT);
  3. A reconstrução da onda com 1, 5 e 21 harmônicos;
  4. Uma tabela no console com amplitudes dos harmônicos e a distorção
     harmônica total (THD);
  5. O fenômeno de Gibbs (condições de Dirichlet): sobressinal de ~9% do salto
     na onda quadrada e valor da série no ponto de descontinuidade;
  6. A envoltória sinc do trem de pulsos (duty 25% e 50%), com a verificação
     da fórmula A_n = 2*A*d*|sinc(n*d)| contra a FFT.

Conclusão esperada: apenas a onda SENOIDAL (E) tem somente o 1º harmônico.

Dependências:
    pip install numpy matplotlib

Execução no VS Code:
    python questao48_harmonicos.py
As figuras também são salvas na pasta "saida/".
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# ----------------------------------------------------------------------------
# Parâmetros
# ----------------------------------------------------------------------------
N = 4096                 # amostras em UM período (FFT exata, sem vazamento)
N_HARM_PLOT = 15         # número de harmônicos exibidos no espectro
DUTY_RETANGULAR = 0.25   # razão cíclica da onda retangular (alternativa B)
PASTA_SAIDA = Path("saida")

# ----------------------------------------------------------------------------
# Formas de onda como função da fase normalizada x (x = t / T, período = 1)
# ----------------------------------------------------------------------------


def onda_triangular(x):
    return (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * x))


def onda_retangular(x):
    # Trem de pulsos 0/1 com razão cíclica diferente de 50%
    return np.where((x % 1) < DUTY_RETANGULAR, 1.0, 0.0)


def onda_dente_de_serra(x):
    return 2 * ((x + 0.5) % 1) - 1


def onda_quadrada(x):
    # Simétrica (50%), valores +1 / -1
    return np.where((x % 1) < 0.5, 1.0, -1.0)


def onda_senoidal(x):
    return np.sin(2 * np.pi * x)


ALTERNATIVAS = {
    "A": ("Onda triangular", onda_triangular),
    "B": (f"Onda retangular (duty {int(DUTY_RETANGULAR * 100)}%)", onda_retangular),
    "C": ("Onda dente de serra", onda_dente_de_serra),
    "D": ("Onda quadrada", onda_quadrada),
    "E": ("Onda senoidal", onda_senoidal),
}

# ----------------------------------------------------------------------------
# Análise de Fourier
# ----------------------------------------------------------------------------


def coeficientes_fourier(funcao):
    """Retorna (X, amplitudes) onde amplitudes[k] é a amplitude do k-ésimo
    harmônico (k=0 é o nível DC)."""
    x = np.arange(N) / N
    y = funcao(x)
    X = np.fft.rfft(y)
    amp = 2 * np.abs(X) / N
    amp[0] = np.abs(X[0]) / N  # DC não é duplicado
    return X, amp


def reconstruir(X, x, k_max):
    """Soma de Fourier truncada com os k_max primeiros harmônicos (+ DC)."""
    y = np.full_like(x, X[0].real / N, dtype=float)
    for k in range(1, k_max + 1):
        y += 2 * np.real(X[k] / N * np.exp(2j * np.pi * k * x))
    return y


def thd(amp):
    """Distorção harmônica total: sqrt(sum(Ak^2, k>=2)) / A1."""
    return np.sqrt(np.sum(amp[2:] ** 2)) / amp[1]


def harmonicos_presentes(amp, limiar=1e-6):
    """Lista de harmônicos (k >= 1) com amplitude relevante."""
    return [k for k in range(1, len(amp)) if amp[k] > limiar * amp[1]]


def descrever_conteudo(amp):
    ks = harmonicos_presentes(amp)
    if ks == [1]:
        return "somente o 1º harmônico"
    pares = [k for k in ks if k % 2 == 0]
    impares = [k for k in ks if k % 2 == 1 and k > 1]
    partes = []
    if impares:
        partes.append("ímpares")
    if pares:
        partes.append("pares")
    return "1º + harmônicos superiores " + " e ".join(partes)


# ----------------------------------------------------------------------------
# Saídas: tabela no console
# ----------------------------------------------------------------------------


def imprimir_tabela(resultados):
    print("=" * 78)
    print("QUESTÃO 48 - Amplitudes dos harmônicos (onda normalizada)")
    print("=" * 78)
    cab = f"{'Alt.':<5}{'Forma de onda':<30}{'THD':>10}   Conteúdo harmônico"
    print(cab)
    print("-" * 78)
    for letra, (nome, _, amp) in resultados.items():
        print(f"({letra})  {nome:<30}{thd(amp):>10.4f}   {descrever_conteudo(amp)}")
    print("-" * 78)

    print("\nAmplitude relativa ao 1º harmônico (A_k / A_1):")
    cab = f"{'k':>3} | " + " | ".join(f"({l})".center(9) for l in resultados)
    print(cab)
    print("-" * len(cab))
    for k in range(1, 11):
        linha = f"{k:>3} | "
        celulas = []
        for _, (_, _, amp) in resultados.items():
            rel = amp[k] / amp[1]
            celulas.append(("0" if rel < 1e-6 else f"{rel:.4f}").center(9))
        print(linha + " | ".join(celulas))
    print()

    com_um = [l for l, (_, _, a) in resultados.items() if harmonicos_presentes(a) == [1]]
    print(f">>> Alternativa(s) com SOMENTE o 1º harmônico: {', '.join(com_um)}")
    assert com_um == ["E"], "Resultado inesperado: a resposta deveria ser (E)."
    print(">>> Gabarito confirmado: (E) Onda senoidal.\n")


# ----------------------------------------------------------------------------
# Saídas: figuras
# ----------------------------------------------------------------------------


def figura_tempo_e_espectro(resultados):
    fig, eixos = plt.subplots(len(resultados), 2, figsize=(12, 13))
    x2 = np.linspace(0, 2, 2000)
    ks = np.arange(0, N_HARM_PLOT + 1)

    for i, (letra, (nome, func, amp)) in enumerate(resultados.items()):
        ax_t, ax_f = eixos[i]
        correta = letra == "E"
        cor = "tab:green" if correta else "tab:blue"

        ax_t.plot(x2, func(x2), color=cor, lw=2)
        ax_t.set_ylabel(f"({letra})\n{nome}", fontsize=9)
        ax_t.grid(alpha=0.3)
        ax_t.set_ylim(-1.4, 1.4)

        ax_f.bar(ks, amp[: N_HARM_PLOT + 1], color=cor, width=0.6)
        ax_f.set_xticks(ks)
        ax_f.grid(alpha=0.3, axis="y")
        ax_f.set_ylim(0, 1.3)
        ax_f.text(
            0.98, 0.85,
            f"THD = {thd(amp):.4f}\n{descrever_conteudo(amp)}",
            transform=ax_f.transAxes, ha="right", va="top", fontsize=8,
            bbox=dict(boxstyle="round", fc="white", ec=cor),
        )

    eixos[0, 0].set_title("Domínio do tempo (2 períodos)")
    eixos[0, 1].set_title("Espectro de amplitudes (k = 0 é o nível DC)")
    eixos[-1, 0].set_xlabel("t / T")
    eixos[-1, 1].set_xlabel("ordem do harmônico (k)")
    fig.suptitle("Questão 48 - Formas de onda e seus espectros de Fourier", fontsize=13)
    fig.tight_layout()
    return fig


def figura_reconstrucao(resultados):
    fig, eixos = plt.subplots(len(resultados), 1, figsize=(10, 13), sharex=True)
    x2 = np.linspace(0, 2, 2000)
    niveis = [(1, "tab:red", "1 harmônico"),
              (5, "tab:orange", "5 harmônicos"),
              (21, "tab:green", "21 harmônicos")]

    for ax, (letra, (nome, func, _)) in zip(eixos, resultados.items()):
        X, _ = coeficientes_fourier(func)
        ax.plot(x2, func(x2), color="black", lw=2.5, alpha=0.35, label="original")
        for k_max, cor, rot in niveis:
            ax.plot(x2, reconstruir(X, x2, k_max), color=cor, lw=1.2, label=rot)
        ax.set_ylabel(f"({letra})\n{nome}", fontsize=9)
        ax.grid(alpha=0.3)
        ax.set_ylim(-1.5, 1.5)
        if letra == "A":
            ax.legend(loc="upper right", ncol=4, fontsize=8)
        if letra == "E":
            ax.text(0.02, 0.1, "Com apenas 1 harmônico a reconstrução já é idêntica!",
                    transform=ax.transAxes, fontsize=9, color="tab:green")

    eixos[-1].set_xlabel("t / T")
    fig.suptitle("Reconstrução por Série de Fourier: só a senoide dispensa harmônicos superiores",
                 fontsize=12)
    fig.tight_layout()
    return fig


def figura_series_teoricas():
    """Ilustra as séries teóricas citadas na justificativa (somas parciais)."""
    x = np.linspace(0, 2, 2000)
    w = 2 * np.pi * x
    fig, eixos = plt.subplots(2, 2, figsize=(11, 7), sharex=True)

    # Quadrada: (4/pi) * sum sin(kw)/k , k ímpar
    quad = sum((4 / np.pi) * np.sin(k * w) / k for k in range(1, 40, 2))
    # Triangular: (8/pi^2) * sum (-1)^((k-1)/2) sin(kw)/k^2 , k ímpar
    tri = sum((8 / np.pi**2) * (-1) ** ((k - 1) // 2) * np.sin(k * w) / k**2
              for k in range(1, 40, 2))
    # Dente de serra: -(2/pi) * sum (-1)^k sin(kw)/k , todo k
    serra = sum(-(2 / np.pi) * (-1) ** k * np.sin(k * w) / k for k in range(1, 40))
    # Senoide: apenas k = 1
    sen = np.sin(w)

    dados = [
        ("Quadrada: ímpares, amplitude 1/k", quad),
        ("Triangular: ímpares, amplitude 1/k²", tri),
        ("Dente de serra: pares e ímpares, amplitude 1/k", serra),
        ("Senoidal: apenas k = 1", sen),
    ]
    for ax, (titulo, y) in zip(eixos.ravel(), dados):
        ax.plot(x, y, lw=1.6, color="tab:green" if "Senoidal" in titulo else "tab:blue")
        ax.set_title(titulo, fontsize=10)
        ax.grid(alpha=0.3)
    fig.suptitle("Séries de Fourier teóricas (somas parciais)", fontsize=12)
    fig.tight_layout()
    return fig


# ----------------------------------------------------------------------------
# Condições de Dirichlet / Fenômeno de Gibbs
# ----------------------------------------------------------------------------


def soma_parcial_quadrada(x, k_max):
    """Soma parcial da série da onda quadrada (+1/-1): (4/pi) * sum sen(2*pi*k*x)/k, k ímpar."""
    y = np.zeros_like(x, dtype=float)
    for k in range(1, k_max + 1, 2):
        y += (4 / np.pi) * np.sin(2 * np.pi * k * x) / k
    return y


def analisar_gibbs(valores_k=(5, 21, 101, 501)):
    """Mede o sobressinal da soma parcial perto da descontinuidade em x = 0,5.
    O salto vale 2 (de +1 para -1), então o sobressinal relativo = (pico - 1) / 2."""
    x = np.linspace(0.0, 0.5, 200001)
    linhas = []
    for k_max in valores_k:
        y = soma_parcial_quadrada(x, k_max)
        pico = y.max()
        linhas.append((k_max, pico, (pico - 1) / 2 * 100))
    return linhas


def imprimir_gibbs(linhas):
    print("=" * 78)
    print("CONDIÇÕES DE DIRICHLET - Fenômeno de Gibbs (onda quadrada, salto = 2)")
    print("=" * 78)
    print(f"{'Harm. (K)':>10} | {'Pico da soma parcial':>22} | {'Sobressinal (% do salto)':>26}")
    print("-" * 66)
    for k_max, pico, pct in linhas:
        print(f"{k_max:>10} | {pico:>22.4f} | {pct:>25.2f}%")
    print("-" * 66)
    print("Limite teórico do sobressinal: ~8,95% do salto (não diminui com K).")

    # Valor da série exatamente no ponto de descontinuidade (x = 0,5)
    v = float(soma_parcial_quadrada(np.array([0.5]), 501)[0])
    print(f"Série em x = 0,5 (descontinuidade): {v:.6f}  "
          "-> média dos limites laterais (+1 e -1) = 0")
    # Verificação automática
    assert abs(v) < 1e-9, "No ponto de descontinuidade a série deveria valer 0."
    assert all(7.5 < pct < 10.0 for k, _, pct in linhas if k >= 21), \
        "Sobressinal de Gibbs fora do esperado (~9%)."
    # O pico NÃO decai: mesma altura para K grande
    assert abs(linhas[-1][2] - linhas[-2][2]) < 0.5, "Gibbs não deveria diminuir com K."
    print(">>> Fenômeno de Gibbs confirmado (sobressinal ~9% independente de K).\n")


def figura_gibbs():
    x_full = np.linspace(0, 1, 4000)
    x_zoom = np.linspace(0.40, 0.60, 4000)
    quadrada_ideal = lambda x: np.where((x % 1) < 0.5, 1.0, -1.0)
    niveis = [(5, "tab:red"), (21, "tab:orange"), (101, "tab:green")]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # Painel 1: período completo
    ax1.plot(x_full, quadrada_ideal(x_full), color="black", lw=2.5, alpha=0.3, label="original")
    for k_max, cor in niveis:
        ax1.plot(x_full, soma_parcial_quadrada(x_full, k_max), color=cor, lw=1.2,
                 label=f"{k_max} harmônicos")
    ax1.set_title("Onda quadrada: somas parciais (1 período)")
    ax1.set_xlabel("t / T")
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=8, loc="upper right")

    # Painel 2: zoom na descontinuidade
    ax2.plot(x_zoom, quadrada_ideal(x_zoom), color="black", lw=2.5, alpha=0.3, label="original")
    for k_max, cor in niveis:
        ax2.plot(x_zoom, soma_parcial_quadrada(x_zoom, k_max), color=cor, lw=1.2,
                 label=f"{k_max} harmônicos")
    ax2.axhline(1.179, color="gray", ls="--", lw=0.8)
    ax2.text(0.402, 1.20, "pico ≈ 1,179 (≈ 9% do salto acima de 1)", fontsize=8, color="gray")
    ax2.plot([0.5], [0], "ko", ms=6)
    ax2.annotate("em t = T/2 a série vale 0\n(média dos limites laterais)",
                 xy=(0.5, 0), xytext=(0.535, 0.45), fontsize=8,
                 arrowprops=dict(arrowstyle="->"))
    ax2.set_title("Zoom na descontinuidade: fenômeno de Gibbs")
    ax2.set_xlabel("t / T")
    ax2.set_ylim(-1.5, 1.5)
    ax2.grid(alpha=0.3)

    fig.suptitle("Condições de Dirichlet: convergência na descontinuidade e fenômeno de Gibbs",
                 fontsize=12)
    fig.tight_layout()
    return fig


# ----------------------------------------------------------------------------
# Função sinc: envoltória do espectro de um trem de pulsos retangulares
# ----------------------------------------------------------------------------


def trem_pulsos_01(duty):
    """Trem de pulsos 0/1 com razão cíclica 'duty' (função da fase x)."""
    return lambda x: np.where((x % 1) < duty, 1.0, 0.0)


def amplitude_teorica_sinc(n, duty, A=1.0):
    """A_n = 2*A*d*|sinc(n*d)|  (np.sinc é a sinc normalizada: sen(pi x)/(pi x))."""
    return 2 * A * duty * np.abs(np.sinc(n * duty))


def verificar_sinc(duties=(0.25, 0.50), n_max=15):
    print("=" * 78)
    print("FUNÇÃO SINC - A_n = 2*A*d*|sinc(n*d)|  versus FFT (trem de pulsos 0/1)")
    print("=" * 78)
    for d in duties:
        _, amp = coeficientes_fourier(trem_pulsos_01(d))
        n = np.arange(1, n_max + 1)
        teorico = amplitude_teorica_sinc(n, d)
        erro = np.max(np.abs(teorico - amp[1 : n_max + 1]))
        nulos = [int(k) for k in n if abs(amp[k]) < 1e-6]
        print(f"\nduty = {int(d * 100)}%  |  CC = {amp[0]:.4f} (esperado A*d = {d:.4f})")
        print(f"  Harmônicos nulos (n*d inteiro): {nulos}")
        print(f"  Erro máximo |teoria - FFT| para n=1..{n_max}: {erro:.2e}")
        print(f"  {'n':>3} | {'FFT':>8} | {'2d|sinc(nd)|':>13} | {'A_n/A_1':>8}")
        for k in range(1, 6):
            print(f"  {k:>3} | {amp[k]:>8.4f} | {teorico[k - 1]:>13.4f} | {amp[k] / amp[1]:>8.4f}")
        assert erro < 1e-3, "Fórmula da sinc não bate com a FFT."
        assert abs(amp[0] - d) < 1e-9, "Nível CC deveria ser A*d."
        esperados = [int(k) for k in n if abs(k * d - round(k * d)) < 1e-9]
        assert nulos == esperados, "Zeros devem ocorrer onde n*d é inteiro."
    print("\n>>> Fórmula com sinc confirmada: zeros em n*d inteiro.\n")


def figura_sinc():
    fig, eixos = plt.subplots(2, 2, figsize=(13, 8))
    n_cont = np.linspace(0, 16, 2000)

    for linha, (d, titulo) in enumerate([(0.25, "(B) Retangular, duty 25%"),
                                          (0.50, "(D) Quadrada 0/1, duty 50%")]):
        ax_t, ax_f = eixos[linha]
        x2 = np.linspace(0, 2, 2000)
        ax_t.plot(x2, trem_pulsos_01(d)(x2), lw=2, color="tab:blue")
        ax_t.set_title(titulo)
        ax_t.set_ylim(-0.2, 1.3)
        ax_t.set_xlabel("t / T")
        ax_t.grid(alpha=0.3)

        _, amp = coeficientes_fourier(trem_pulsos_01(d))
        ks = np.arange(0, 17)
        ax_f.plot(n_cont, 2 * d * np.abs(np.sinc(n_cont * d)), color="tab:red", lw=1.5,
                  label="envoltória  2d·|sinc(n·d)|")
        ax_f.stem(ks[1:], amp[1:17], linefmt="tab:blue", markerfmt="o", basefmt=" ",
                  label="harmônicos (FFT)")
        ax_f.plot([0], [amp[0]], "s", color="tab:green", label=f"CC = {amp[0]:.2f}")

        nulos = [k for k in range(1, 17) if abs(amp[k]) < 1e-6]
        for k in nulos:
            ax_f.plot([k], [0], "x", color="black", ms=9, mew=2)
        if nulos:
            ax_f.annotate(f"zeros em n = {', '.join(map(str, nulos[:4]))}...\n(n·d inteiro)",
                          xy=(nulos[0], 0), xytext=(nulos[0] + 1.5, 0.30 if d < 0.4 else 0.35),
                          fontsize=8, arrowprops=dict(arrowstyle="->"))
        ax_f.set_title("Espectro com envoltória sinc")
        ax_f.set_xlabel("ordem do harmônico (n)")
        ax_f.set_xticks(ks)
        ax_f.set_ylim(0, max(0.75, 2 * d * 1.08))  # envoltória em n=0 vale 2d (o CC vale só d)
        ax_f.grid(alpha=0.3)
        ax_f.legend(fontsize=8, loc="upper right")

    fig.suptitle("Função sinc: envoltória dos harmônicos de um trem de pulsos retangulares",
                 fontsize=12)
    fig.tight_layout()
    return fig


# ----------------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------------


def main():
    resultados = {}
    for letra, (nome, func) in ALTERNATIVAS.items():
        _, amp = coeficientes_fourier(func)
        resultados[letra] = (nome, func, amp)

    imprimir_tabela(resultados)
    imprimir_gibbs(analisar_gibbs())
    verificar_sinc()

    PASTA_SAIDA.mkdir(exist_ok=True)
    figuras = {
        "q48_tempo_espectro.png": figura_tempo_e_espectro(resultados),
        "q48_reconstrucao.png": figura_reconstrucao(resultados),
        "q48_series_teoricas.png": figura_series_teoricas(),
        "q48_gibbs_dirichlet.png": figura_gibbs(),
        "q48_sinc_envoltoria.png": figura_sinc(),
    }
    for nome, fig in figuras.items():
        fig.savefig(PASTA_SAIDA / nome, dpi=150)
    print(f"Figuras salvas em: {PASTA_SAIDA.resolve()}")

    plt.show()


if __name__ == "__main__":
    main()
