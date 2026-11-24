class PCMInput extends AudioWorkletProcessor {
  constructor() { super(); this.samples=[]; this.position=0; }
  process(inputs) {
    const channel=inputs[0]?.[0];
    if(!channel)return true;
    const ratio=sampleRate/16000;
    for(let i=0;i<channel.length;i++){
      this.position+=1;
      if(this.position>=ratio){this.position-=ratio;this.samples.push(Math.max(-1,Math.min(1,channel[i])));}
      if(this.samples.length===320){
        const pcm=new Int16Array(320);
        for(let j=0;j<320;j++)pcm[j]=this.samples[j]<0?this.samples[j]*32768:this.samples[j]*32767;
        this.port.postMessage(pcm.buffer,[pcm.buffer]);this.samples=[];
      }
    }
    return true;
  }
}
registerProcessor('atoms-pcm-input',PCMInput);
