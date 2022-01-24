audio_sample = 'sjvoicesamp16.wav';
[xtest1, fs] = audioread(audio_sample, 'native');

audio_sample = 'sjvoicesamp16_pyout.wav';
[xtest2, fs] = audioread(audio_sample, 'native');

audio_sample = 'sjvoicesamp16_mlout.wav';
[xtest3, fs] = audioread(audio_sample, 'native');

time = ((1:length(xtest1))/fs)';

% figure(1)
% plot(time,xtest1)
% hold on
% plot(time,xtest2)
% plot(time,xtest3)
% hold off

figure(1)
plot(time,xtest2)
figure(2)
plot(time,xtest3)