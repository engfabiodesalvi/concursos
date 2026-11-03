import control as ctl
import matplotlib.pyplot as plt
import numpy as np

num = [1, 6]
den = [1, 1, -6]          # (s-2)(s+3)
G = ctl.TransferFunction(num, den)

print("Polos de G :", ctl.poles(G))   # [ 2, -3]
print("Zeros de G :", ctl.zeros(G))   # [-6]

k_gains = np.logspace(-2, 3, 1000)

ctl.root_locus_plot(G, gains=k_gains, grid=False)
ax = plt.gca()
ax.axvline(0, color='red', ls='--', alpha=0.5, label='Eixo imaginário')
ax.set_title("LGR - Transpetro 2018")
ax.set_xlabel("Eixo real (σ)")
ax.set_ylabel("Eixo imaginário (jω)")
ax.legend()
plt.show()

for K in (0.1, 1.0, 1.5, 50.0):
    p = ctl.poles(ctl.feedback(K * G, 1))
    estavel = np.all(p.real < 0)
    print(f"K={K:>5}: polos={np.round(p, 3)}  -> {'estável' if estavel else 'instável/marginal'}")