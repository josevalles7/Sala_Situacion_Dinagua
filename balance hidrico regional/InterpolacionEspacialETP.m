% función que interpola etp por cuenca en base a datos 
% de etp e inversa de la distancia al cuadrado
% cuenca contiene una matriz en la que estan las cuencas en formato raster
% de acuerdo al encabezado segun esri (xll corner yll corner y delta)
% y -1 es fuera de ella
% datos contiene columnas año, mes, día, pluviometros a partir de la
% cuarta fila, en la primera y segunda están las coordenadas X e Y y en la
% tercera el código 
% ncuen vector con los codigos de cada subcuenca

clear
ncuen=load('Cuencas.txt');
cuenca=load('CuencasOrden3.txt');
datos=load('ETP.txt');


tic



xll=255265;  yll=6130196; delta=3000;

ndias=length(datos(:,1))-3;   npluvs=length(datos(1,:))-3;

[nrows ncols]=size(cuenca);

coord=datos(1:2,4:(npluvs+3));
codigos=datos(3,4:(npluvs+3));
yll=yll+delta*(nrows-1);
M=datos(4:ndias+3,4:npluvs+3);
%MAT3=-1*ones(nrows,ncols); % ver esto que esta en mala posición
cont=1;
for i=1:nrows % es la coordenada y
    for j=1:ncols % es la coordenada x
        if cuenca(i,j)>0 %si está dentro de la cuenca determino las distancias desde el punto a los pluvsj
            corx=xll+(j-1)*delta; cory=yll-(i-1)*delta;
            
            cx=coord(1,:)-corx; cx=cx.^2;
            cy=coord(2,:)-cory; cy=cy.^2;
            c=(cx+cy);
            
            dist=[codigos' c'];
            
            MAT(1,cont)=cuenca(i,j); MAT(2,cont)=corx; MAT(3,cont)=cory;

            for k=1:ndias
                y=[dist  M(k,:)']; % les agrego a codigo y dist el valor de p del día k
                y(find(y(:,3)==-1),:)=[];
             
                y=sortrows(y,2); %las ordeno junto a sus codigos
                             
                MAT(k+3,cont)=(y(1,3)/y(1,2)+y(2,3)/y(2,2)+y(3,3)/y(3,2))/(1/y(1,2)+1/y(2,2)+1/y(3,2));
                MATCAL(k+3,cont)=y(1,2)^.5;
               
            end
            cont=cont+1;
        end
    end
end

cont2=1;
MATCAL(1:3,:)=MAT(1:3,:);

for t=1:length(ncuen)
    M2=MAT(4:length(MAT(:,1)),find(MAT(1,:)==ncuen(t)));
    Pcuen(:,cont2)=mean(M2,2);
    cont2=cont2+1;
end
    
                
toc
Pcuen=[ncuen';Pcuen];
Pcuen=[datos(3:length(datos(:,1)),1:2) Pcuen];
                
% save ETPmedias.csv Pcuen -ascii
csvwrite('ETPmedias.csv',Pcuen)                
                
                
                
                
                
                
                
                