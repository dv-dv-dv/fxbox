audio_sample = 'sjvoicesamp16.wav';
[xtest, fs] = audioread(audio_sample, 'native');
write_audio=1;
%Input signal
x = xtest;
%Time
time = ((1:length(x))/fs)';
%Threshold
T = -30;
%Ratio
R = 7;
%Attack
attack = 0.005;
atk = exp(-1/(attack*fs));
%Release
release = 0.5;
rel = exp(-1/(release*fs));
%Knee width
W = 10;
%Makeup Gain
M=0;

CHUNK = 128;
a = 1;
b = CHUNK;
c = length(x);

go=1;
global ldprevout
ldprevout = 0;
while(go)
    if(b>c)
        b=c;
        go=0;
    end
    bffr = x(a:b,:);
    out(a:b,:) = logdomain(bffr,T,R,W,M,atk,rel);
    a=a+CHUNK;
    b=b+CHUNK;
    

end

figure(1)
plot(time,out)
figure(2)
plot(time,x)

max(out(:,1))
max(x(:,1))

if(write_audio)
    audiowrite('sjvoicesamp16_mlout.wav',out,fs);
end

function out = logdomain(in,T,R,W,M,atk,rel)
    global ldprevout
    inl = abs(in(:,1)+in(:,2));
    outdb=todb(inl);
    outdb2=gaincomp(outdb,T,R,W);
    outdb3=outdb-outdb2;
    outdb4=lvldetect(outdb3,atk,rel);
    gaindb=outdb4-M; 
    gain=10.^(-gaindb/20);
    out(:,1)=int16(double(in(:,1)).*gain);
    out(:,2)=int16(double(in(:,2)).*gain);
end
function [out] = returntozero(in,T,R,W,M,atk,rel)
    inl = abs(in(:,1)+in(:,2));
    outl=lvldetect(inl,atk,rel);
    outdb=todb(outl);
    outdb2=gaincomp(outdb,T,R,W);
    gaindb=outdb-outdb2+M;
    gain=10.^(-gaindb/20);
    out=zeros(length(in),2);
    out(:,1)=in(:,1).*gain;
    out(:,2)=in(:,2).*gain;
end

function [out] = lvldetect(in,atk,rel)
    global ldprevout
    out=zeros(length(in),1);
    outnminus1 = ldprevout;
    for n=1:length(in)
        if(in(n)>outnminus1)
            out(n) = atk*outnminus1+(1-atk)*in(n);
        else
            out(n) = rel*outnminus1+(1-rel)*in(n);
        end
        outnminus1 = out(n);
    end
    ldprevout = out(length(in));
end

function [out] = gaincomp(in,T,R,W)
    out=zeros(length(in),1);
    for n=1:length(in)
        if(2*(in(n)-T)<-W)
            out(n) = in(n);
        elseif(2*abs(in(n)-T)<=W)
            out(n) = in(n)+(1/R-1)*((in(n)-T+W/2)^(2))/(2*W);
        elseif(2*(in(n)-T)>W)
            out(n) = T+(in(n)-T)/R;
        end
    end
end

function [out] = todb(in)
    out=zeros(length(in),1);
    for n=1:length(in)
        if(in(n)==0)
            out(n)=-999;
        else
            infl = double(in(n))/((2^(16))/2);
            out(n)=20*log10(infl);
        end
    end
end

function [out] = tolin(in)
    out=zeros(length(in),1);
    for n=1:length(in)
        out(n) = 10^(-in(n)/20);
    end
end