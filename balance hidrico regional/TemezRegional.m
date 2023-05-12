function [ETR QC I H V Asup Asub]=TemezRegional(AD,P,ETP) %, P, ETP, QM)
% Modelo INYPSA

Hmax = AD*1.20; 
C = 0.94; 
Imax = 91;
alfa = 0.99 ;

% Modelo pequeñas Presas IMFIA
%{
Hmax = AD*0.92; 
C = 0.30; 
Imax = 386;
alfa = 0.0775;
%}

P=[P(1:12);P];
ETP=[ETP(1:12);ETP];



% condicion inicial
    delta=Hmax-0+ETP(1);
    Po=C*(Hmax-0);

    if P(1)<=Po
        T(1)=0;
    else
        T(1)=((P(1)-Po)^2)/(P(1)+delta-2*Po);
    end

    ETR(1)=min(ETP(1),0+P(1)-T(1));
    H(1)=max(0,0+P(1)-T(1)-ETP(1));


    I(1)=Imax*T(1)/(T(1)+Imax);
    
    Asup(1)=T(1)-I(1);

    Qsub(1)=0*exp(-alfa)+alfa*I(1)*exp(-alfa/2);
    
    V(1)=Qsub(1)/alfa;
    
    Asub(1)=0-V(1)+I(1);

    QC(1)=Asup(1)+Asub(1);

    for t=2:length(P)
        
        
        delta=Hmax-H(t-1)+ETP(t);
        Po=C*(Hmax-H(t-1));
        if P(t)<=Po
            T(t)=0;
        else
            T(t)=((P(t)-Po)^2)/(P(t)+delta-2*Po);
        end

        ETR(t)=min(ETP(t),H(t-1)+P(t)-T(t));
        H(t)=max(0,H(t-1)+P(t)-T(t)-ETP(t));

        I(t)=Imax*T(t)/(T(t)+Imax);

        Asup(t)=T(t)-I(t);
        
        Qsub(t)=Qsub(t-1)*exp(-alfa)+alfa*I(t)*exp(-alfa/2);
        V(t)=Qsub(t)/alfa;
        
        Asub(t)=V(t-1)-V(t)+I(t);

        QC(t)=Asup(t)+Asub(t);
    end





ETR=ETR';
QC=QC';
Asup=Asup';
Asub=Asub';
V=V';
I=I';
H=H';

ETR(1:12)=[];
QC(1:12)=[];
H(1:12)=[];

