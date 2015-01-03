file='input';

% If someone knows how to open a binary file in matlab where the values are bits, not bytes, please tell me

%fd=fopen(file);
%[val, count] = fread(fd);
%fclose(fd);

% Just load the ascii file instead
val=load(file);

% Show the first 10 bits
val(1:10)

% Count total number of bits
count=size(val,2);
fprintf('There are %i complex samples\n', count);
bits=2;
fprintf('There are %i bits used for a complex number\n', bits);
values=1024;
fprintf('There are %i complex numbers required per ms\n', values);
columns = (count/bits)/1024;
fprintf('Then there are %i columns (and so %i ms) \n', columns, columns)
fprintf('The default is 512 ms for the Aclys chip\n');

% I only have some vague ideas on how to continue

% According to "Off-Board Positioning Using an Efficient GNSS SNAP Processing Algorithm" by Rosenfeld and Duchovny from
% CellGuide Ltd., the following should happen.


% 1. The GPS L1 C/A signal is apparently represented by these 2-bits complex I+Q samples (one bit real, one bit imag.)
I=val(1:2:end-1);
Q=val(2:2:end);
c=complex(I,Q);

rows=values;
sz=[rows columns];
A=reshape(c,sz);

% 2. We need to process N_col columns. It is not indicated how many columns that should be.

%figure('Color','w','Position',[10 10 600 600]);
figure
hold on
for i = 1:4

	N_start=1+64*i;
	N_col=64;
	M_samp=A(:,N_start:N_start+N_col);

	fftA=fft2(M_samp);

	%nr = 1:size(fftA,1);
	%nc = 1:size(fftA,2);
	%[X,Y]=meshgrid(nc,nr);
	B=abs(fftA);
	%X=X';
	%Y=Y';
	%B=B';
	% truncate to T
	T=2000;
	B=min(B,T);
	%plot3(X,Y,B)
	subplot(2,2,i);
	surf(B);
end

%figure, imshow(abs(fftshift(fftA)),[24 100000]), colormap gray

% 3. We need to account for Doppler

% 4. We need to account for phase

% The result should now be a matrix with one of the columns a gold-modulated signal

% 5. Now some frequency transforms and we should be done...
