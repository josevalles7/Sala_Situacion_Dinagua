import numpy as np

def TemezRegional(AD, P, ETP):
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
    
    P = np.concatenate((P[:12], P))
    ETP = np.concatenate((ETP[:12], ETP))

    T = np.zeros_like(P)
    ETR = np.zeros_like(P)
    H = np.zeros_like(P)
    I = np.zeros_like(P)
    Asup = np.zeros_like(P)
    Qsub = np.zeros_like(P)
    V = np.zeros_like(P)
    Asub = np.zeros_like(P)
    QC = np.zeros_like(P)

    # condicion inicial
    delta = Hmax - 0 + ETP[0]
    Po = C * (Hmax - 0)

    if P[0] <= Po:
        T[0] = 0
    else:
        T[0] = ((P[0] - Po) ** 2) / (P[0] + delta - 2 * Po)

    ETR[0] = min(ETP[0], 0 + P[0] - T[0])
    H[0] = max(0, 0 + P[0] - T[0] - ETP[0])
    I[0] = Imax * T[0] / (T[0] + Imax)
    Asup[0] = T[0] - I[0]
    Qsub[0] = 0 * np.exp(-alfa) + alfa * I[0] * np.exp(-alfa / 2)
    V[0] = Qsub[0] / alfa
    Asub[0] = 0 - V[0] + I[0]
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
    ETR = ETR[12:]
    QC = QC[12:]
    I = I[12:]
    H = H[12:]
    Asup = Asup[12:]
    Asub = Asub[12:]

    return ETR, QC, I, H, V, Asup, Asub

