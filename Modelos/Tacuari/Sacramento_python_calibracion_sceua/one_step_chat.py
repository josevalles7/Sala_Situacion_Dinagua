def one_step(estados, pxv, edmnd, parametros):
    dt = 3 / 24  # Intervalo de tiempo base (3 horas expresadas en días)

    # Descomposición de parámetros
    uztwm = parametros['uztwm']
    uzfwm = parametros['uzfwm']
    uzk = parametros['uzk']
    pctim = parametros['pctim']
    adimp = parametros['adimp']
    zperc = parametros['zperc']
    rexp = parametros['rexp']
    lztwm = parametros['lztwm']
    lzfsm = parametros['lzfsm']
    lzfpm = parametros['lzfpm']
    lzsk = parametros['lzsk']
    lzpk = parametros['lzpk']
    pfree = parametros['pfree']
    side = parametros['side']
    rserv = parametros['rserv']
    
    EPS = 0.0001  # Tolerancia numérica
    riva = 0.01   # Constante interna
    
    # Estados iniciales
    uztwc = estados['uztwc']
    uzfwc = estados['uzfwc']
    lztwc = estados['lztwc']
    lzfsc = estados['lzfsc']
    lzfpc = estados['lzfpc']
    adimc = estados['adimc']
    
    zp = max(zperc, 0)  # Asegura valores no negativos
    e2 = 0  # Inicialización para evitar referencias no definidas
    e3 = 0
    
    # Evapotranspiración en la zona superior (Tensión)
    e1 = edmnd * uztwc / uztwm
    red = edmnd - e1
    uztwc -= e1
    
    if abs(uztwc) < EPS:
        uztwc = 0
    
    if uztwc < 0:
        e1 += uztwc
        uztwc = 0
        red = edmnd - e1
        if uzfwc >= red:
            e2 = red
            uzfwc -= e2
            red = 0
            if (uztwc / uztwm) < (uzfwc / uzfwm):
                uzrat = (uztwc + uzfwc) / (uztwm + uzfwm)
                uztwc = uztwm * uzrat
                uzfwc = uzfwm * uzrat
        else:
            e2 = uzfwc
            uzfwc = 0
            red -= e2
    
    # Evapotranspiración en la zona inferior (Tensión)
    e3 = red * lztwc / (uztwm + lztwm)
    lztwc -= e3
    
    if abs(lztwc) < EPS:
        lztwc = 0
    
    if lztwc < 0:
        e3 += lztwc
        lztwc = 0
    
    # Cálculo de proporciones
    ratlzt = lztwc / lztwm
    saved = rserv * (lzfpm + lzfsm)
    ratlz = (lztwc + lzfpc + lzfsc - saved) / (lztwm + lzfpm + lzfsm - saved)
    
    # Redistribución en la zona inferior
    if ratlzt < ratlz:
        del_ = (ratlz - ratlzt) * lztwm
        lztwc += del_
        lzfsc -= del_
        if lzfsc < 0:
            lzfpc += lzfsc
            lzfsc = 0
    
    # Evapotranspiración en el área adicional impermeable
    e5 = e1 + (red + e2) * (adimc - e1 - uztwc) / (uztwm + lztwm)
    adimc -= e5
    if abs(adimc) < EPS:
        adimc = 0
    if adimc < 0:
        e5 += adimc
        adimc = 0
    e5 *= adimp
    
    # Cálculo del exceso de humedad
    twx = pxv + uztwc - uztwm
    if twx < 0:
        uztwc += pxv
        twx = 0
    else:
        uztwc = uztwm
    
    adimc += (pxv - twx)
    roimp = pxv * pctim
    
    sbf = 0
    ssur = 0
    sif = 0
    sperc = 0
    sdro = 0
    spbf = 0.0
    
    ninc = int(1 + 0.2 * (uzfwc + twx))
    dinc = dt / ninc
    pinc = twx / ninc
    
    duz = 1 - (1 - uzk) ** dinc
    dlzp = 1 - (1 - lzpk) ** dinc
    dlzs = 1 - (1 - lzsk) ** dinc
    
    parea = 1 - adimp - pctim
    
    for _ in range(ninc):
        adsur = 0
        ratio = (adimc - uztwc) / lztwm
        addro = pinc * (ratio ** 2)
        sdro += addro * adimp
        
        bf = lzfpc * dlzp
        lzfpc -= bf
        if lzfpc <= 1e-4:
            bf += lzfpc
            lzfpc = 0
        sbf += bf
        spbf += bf
        
        bf = lzfsc * dlzs
        lzfsc -= bf
        if lzfsc <= 1e-4:
            bf += lzfsc
            lzfsc = 0
        sbf += bf
        
        if (pinc + uzfwc) > 1e-2:
            percm = lzfpm * dlzp + lzfsm * dlzs
            perc = percm * uzfwc / uzfwm
            defr = max(1 - (lztwc + lzfpc + lzfsc) / (lztwm + lzfpm + lzfsm), 0.01)
            perc *= (1 + zp * (defr ** rexp))
            
            perc = min(perc, uzfwc)
            uzfwc -= perc
            
            check = lztwc + lzfpc + lzfsc + perc - lztwm - lzfpm - lzfsm
            if check > 0:
                perc -= check
                uzfwc += check
            
            sperc += perc
            
            del_ = uzfwc * duz
            sif += del_
            uzfwc -= del_
            
            perct = perc * (1.0 - pfree)
            if (perct + lztwc) <= lztwm:
                lztwc += perct
                percf = 0.0
            else:
                percf = perct + lztwc - lztwm
                lztwc = lztwm
            
            percf += perc * pfree
            if percf > 0:
                hpl = lzfpm / (lzfpm + lzfsm)
                ratlp = lzfpc / lzfpm
                ratls = lzfsc / lzfsm
                fracp = min(hpl * 2.0 * (1.0 - ratlp) / (1.0 - ratlp + 1.0 - ratls), 1.0)
                
                percp = percf * fracp
                percs = percf - percp
                lzfsc += percs
                if lzfsc > lzfsm:
                    percs -= (lzfsc - lzfsm)
                    lzfsc = lzfsm
                lzfpc += (percf - percs)
                if lzfpc > lzfpm:
                    excess = lzfpc - lzfpm
                    lztwc += excess
                    lzfpc = lzfpm
        
        if pinc > 0:
            if (pinc + uzfwc) <= uzfwm:
                uzfwc += pinc
            else:
                sur = pinc + uzfwc - uzfwm
                uzfwc = uzfwm
                ssur += sur * parea
                adsur = sur * (1.0 - addro / pinc)
                ssur += adsur * adimp
        
        adimc += (pinc - addro - adsur)
        if adimc > (uztwm + lztwm):
            addro += (adimc - (uztwm + lztwm))
            adimc = uztwm + lztwm
    
    eused = (e1 + e2 + e3) * parea
    sif *= parea
    tbf = sbf * parea
    bfcc = tbf / (1.0 + side)
    bfp = (spbf * parea) / (1.0 + side)
    bfs = max(bfcc - bfp, 0)
    bfncc = tbf - bfcc
    tlci = roimp + sdro + ssur + sif + bfcc
    
    e4 = (edmnd - eused) * riva
    tlci -= e4
    if tlci < 0:
        e4 += tlci
        tlci = 0
    
    tet = eused + e5 + e4
    if adimc < uztwc:
        adimc = uztwc
    
    estados.update({
        'uztwc': uztwc,
        'uzfwc': uzfwc,
        'lztwc': lztwc,
        'lzfsc': lzfsc,
        'lzfpc': lzfpc,
        'adimc': adimc
    })
    
    return estados, tlci, roimp, sdro, ssur, sif, bfcc
