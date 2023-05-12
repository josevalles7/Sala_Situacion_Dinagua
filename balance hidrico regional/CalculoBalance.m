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



for i=1:length(AD)

[ETR1(:,i) QC1(:,i) I H(:,i) V Asup Asub]=TemezRegional(AD(i),P1(:,i),ETP1(:,i));

end

ETR1=[fechas ETR1];
QC1=[fechas QC1];
H=[fechas H];

ETR1=[codigos ; ETR1];
QC1=[codigos ; QC1];
H=[codigos ; H];

% save ETR.csv ETR1 -ascii
csvwrite('ETR.csv',ETR1)
% save Escorrentia.csv QC1 -ascii
csvwrite('Escorrentia.csv',QC1)
% save HumedadSuelo.csv H -ascii
csvwrite('HumedadSuelo.csv',H)


%clear