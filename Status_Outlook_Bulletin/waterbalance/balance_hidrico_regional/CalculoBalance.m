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

[ETR1(:,i) QC1(:,i) I H(:,i) V Asup(:,i) Asub(:,i)]=TemezRegional(AD(i),P1(:,i),ETP1(:,i));

end

ETR1=[fechas ETR1];
QC1=[fechas QC1];
H=[fechas H];
Asup = [fechas Asup];
Asub = [fechas Asub];

ETR1=[codigos ; ETR1];
QC1=[codigos ; QC1];
H=[codigos ; H];

% Inicio: Agregados verasun
% Crear carpeta de salida si no existe
outdir = 'output_modelo';

if ~exist(outdir, 'dir')
    mkdir(outdir);
end

% Guardar salidas en la carpeta output_modelo
csvwrite(fullfile(outdir, 'ETR.csv'), ETR1)
csvwrite(fullfile(outdir, 'Escorrentia_total.csv'), QC1)
csvwrite(fullfile(outdir, 'HumedadSuelo.csv'), H)
csvwrite(fullfile(outdir, 'Escorrentia_sup.csv'), Asup)
csvwrite(fullfile(outdir, 'Escorrentia_sub.csv'), Asub)

clear