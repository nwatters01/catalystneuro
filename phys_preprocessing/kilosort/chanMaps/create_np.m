%  create a channel map file

Nchannels = 384;
connected = true(Nchannels, 1);

chanMap   = 1:Nchannels;
chanMap0ind = chanMap - 1;
xcoords   = repmat([43 11], 1, 192)';
ycoords   = repelem([20 : 20 : 3840], 2)';

kcoords   = ones(Nchannels, 1); % grouping of channels (i.e. tetrode groups)

fs = 30000; % sampling frequency
save('np.mat', ...
    'chanMap','connected', 'xcoords', 'ycoords', 'kcoords', 'chanMap0ind', 'fs')

% kcoords is used to forcefully restrict templates to channels in the same
% channel group. An option can be set in the master_file to allow a fraction 
% of all templates to span more channel groups, so that they can capture shared 
% noise across all channels. This option is

% ops.criterionNoiseChannels = 0.2; 

% if this number is less than 1, it will be treated as a fraction of the total number of clusters

% if this number is larger than 1, it will be treated as the "effective
% number" of channel groups at which to set the threshold. So if a template
% occupies more than this many channel groups, it will not be restricted to
% a single channel group. 