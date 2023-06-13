clear


AD=load('AguaDisponible.txt');
P1=load('Pmedias.csv');
ETP1=load('ETPmedias.csv');
codigos=P1(1,:);
fechas=P1(2:length(P1(:,1)),1:2);
P1(1,:)=[];
P1(:,1:2)=[];

ETP1(1,:)=[];
ETP1(:,1:2)=[];

mes_fin = fechas(end,2) + 1 ;
ano_fin = fechas(end,1);

rows = find(fechas(:,2)==mes_fin);

for j = 1:length(rows)
    f = fechas(rows(j,1):rows(j,1)+5,:);
    dif = ano_fin - f(1,1);
    f(:,1) = f(:,1) + dif;
    f_merge = [fechas;f];
    
    P_fcst = P1(rows(j,1):rows(j,1)+5,:);
    P_merge = [P1;P_fcst];
    
    E_fcst = ETP1(rows(j,1):rows(j,1)+5,:);
    E_merge = [ETP1;E_fcst];
    for i=1:length(AD)
        [ETR1(:,i) QC1(:,i) I H(:,i) V Asup Asub]=TemezRegional(AD(i),P_merge(:,i),E_merge(:,i));
    end
    
    ETR1=[f_merge ETR1];
    QC1=[f_merge QC1];
    H=[f_merge H];
    
    ETR1=[codigos ; ETR1];
    QC1=[codigos ; QC1];
    H=[codigos ; H];
    
    csvwrite(['esp/Escorrentia',num2str(fechas(rows(j,1))),'.csv'],QC1)
    clear f P_fcst P_merge E_fcst E_merge ETR1 QC1 H

end