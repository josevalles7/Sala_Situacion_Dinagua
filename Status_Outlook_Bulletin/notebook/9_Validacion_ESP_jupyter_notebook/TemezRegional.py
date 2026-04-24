import numpy as np

def TemezRegional(AD, P, ETP, H0=0.0, V0=0.0):
    # Modelo INYPSA
    Hmax = AD * 1.20
    C = 0.94
    Imax = 91
    alfa = 0.99

    # Modelo pequeñas Presas IMFIA
    """
    Hmax = AD * 0.92
    C = 0.30
    Imax = 386
    alfa = 0.0775
    """
    T = np.zeros_like(P)
    ETR = np.zeros_like(P)
    H = np.zeros_like(P)
    I = np.zeros_like(P)
    Asup = np.zeros_like(P)
    Qsub = np.zeros_like(P)
    V = np.zeros_like(P)
    Asub = np.zeros_like(P)
    QC = np.zeros_like(P)


    H[0] = H0
    V[0] = V0
    Qsub[0] = alfa * V0

    # condicion inicial
    delta = Hmax - H[0] + ETP[0]
    Po = C * (Hmax - H[0])

    if P[0] <= Po:
        T[0] = 0
    else:
        T[0] = ((P[0] - Po) ** 2) / (P[0] + delta - 2 * Po)

    ETR[0] = min(ETP[0], H[0] + P[0] - T[0])
    H[0] = max(0, H[0] + P[0] - T[0] - ETP[0])

    I[0] = Imax * T[0] / (T[0] + Imax)
    Asup[0] = T[0] - I[0]

    Qsub[0] = Qsub[0] * np.exp(-alfa) + alfa * I[0] * np.exp(-alfa / 2)
    V[0] = Qsub[0] / alfa
    Asub[0] = I[0] - V[0] + V0
    QC[0] = Asup[0] + Asub[0]
    
    for t in range(1, len(P)):
        delta = Hmax - H[t - 1] + ETP[t]
        Po = C * (Hmax - H[t - 1])

        if P[t] <= Po:
            T[t] = 0
        else:
            T[t] = ((P[t] - Po) ** 2) / (P[t] + delta - 2 * Po)

        ETR[t] = min(ETP[t], H[t - 1] + P[t] - T[t])
        H[t] = max(0, H[t - 1] + P[t] - T[t] - ETP[t])
        I[t] = Imax * T[t] / (T[t] + Imax)
        Asup[t] = T[t] - I[t]
        Qsub[t] = Qsub[t - 1] * np.exp(-alfa) + alfa * I[t] * np.exp(-alfa / 2)
        V[t] = Qsub[t] / alfa
        Asub[t] = V[t - 1] - V[t] + I[t]
        QC[t] = Asup[t] + Asub[t]

    # ETR = np.array(ETR)
    # QC = np.array(QC)
    # Asup = np.array(Asup)
    # Asub = np.array(Asub)
    # V = np.array(V)
    # I = np.array(I)
    # H = np.array(H)
    # print(H)
    states = {
        "H": H,
        "V": V,
        "I": I,
        "Asub": Asub
    }

    fluxes = {
        "QC": QC,
        "ETR": ETR,
        "Asup": Asup
    }

    return fluxes, states

