#!/bin/octave -f

file="input"

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
printf('There are %i complex samples\n', count);
bits=2;
printf('There are %i bits used for a complex number\n', bits);
values=1024;
printf('There are %i complex numbers required per ms\n', values);
columns = (count/bits)/1024;
printf('Then there are %i columns (and so %i ms) \n', columns, columns)
printf('The default is 512 ms for the Aclys chip\n');

% I only have some vague ideas on how to continue

% According to "Off-Board Positioning Using an Efficient GNSS SNAP Processing Algorithm" by Rosenfeld and Duchovny from
% CellGuide Ltd., the following should happen.


% 1. The GPS L1 C/A signal is apparently represented by these 2-bits complex I+Q samples (one bit real, one bit imag.)

% 2. We need to process N_col columns. It is not indicated how many columns that should be.

% 3. We need to account for Doppler

% 4. We need to account for phase

% The result should now be a matrix with one of the columns a gold-modulated signal

% 5. Now some frequency transforms and we should be done...
