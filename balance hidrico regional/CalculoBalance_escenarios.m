clear

for j = 1:12
	AD=load('AguaDisponible.txt');

    filename_P = sprintf('escenarios/Pmedias_E_%d.csv', j);
    P1 = load(filename_P);
	filename_ETP = sprintf('escenarios/ETPmedias_E_%d.csv', j);
	ETP1=load(filename_ETP);
    
	
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

	% Inicio: Agregados jvalles
	Asup = [codigos; Asup];
	Asub = [codigos;Asub];
	% fin: Agregados jvalles

	% save ETR.csv ETR1 -ascii
	%csvwrite('escenarios/ETR_E_1.csv',ETR1)
	csvwrite(sprintf('escenarios/ETR_E_%d.csv', j),ETR1)
	
	% save Escorrentia.csv QC1 -ascii
	csvwrite(sprintf('escenarios/Escorrentia_total_E_%d.csv', j),QC1)
	% save HumedadSuelo.csv H -ascii
	csvwrite(sprintf('escenarios/HumedadSuelo_E_%d.csv', j),H)

	% Inicio: Agregados jvalles
	csvwrite(sprintf('escenarios/Escorrentia_sup_E_%d.csv', j),Asup)
	csvwrite(sprintf('escenarios/Escorrentia_sub_E_%d.csv', j),Asub)
	% fin: Agregados jvalles


	clear all
end

