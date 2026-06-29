const TARGET_RATE = 16_000;

export type Result = { source: string; target: string; ms: number };
export type Status =
  | "idle"
  | "connecting"
  | "listening"
  | "stopped"
  | "disconnected"
  | "error";

export class VoiceStream {
  private ctx?: AudioContext;
  private source?: MediaStreamAudioSourceNode;
  private processor?: ScriptProcessorNode;
  private stream?: MediaStream;
  private ws?: WebSocket;
  private playHead = 0;
  private stopping = false;

  constructor(
    private wsUrl: string,
    private onResult: (r: Result) => void,
    private onStatus: (s: Status) => void
  ) {}

  async start() {
    this.stopping = false;
    this.onStatus("connecting");

    this.ws = new WebSocket(this.wsUrl);
    this.ws.binaryType = "arraybuffer";
    this.ws.onerror = () => this.onStatus("error");
    this.ws.onclose = () => this.onStatus(this.stopping ? "stopped" : "disconnected");
    this.ws.onmessage = (e) => this.onMessage(e);
    this.ws.onopen = async () => {
      try {
        await this.openMic();
        this.onStatus("listening");
      } catch {
        this.onStatus("error");
        this.stop();
      }
    };
  }

  private async openMic() {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.ctx = new AudioContext();
    await this.ctx.resume();

    this.source = this.ctx.createMediaStreamSource(this.stream);
    this.processor = this.ctx.createScriptProcessor(4096, 1, 1);

    this.processor.onaudioprocess = (ev) => {
      const input = ev.inputBuffer.getChannelData(0);
      const down = downsample(input, this.ctx!.sampleRate, TARGET_RATE);
      if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(floatToInt16(down));
    };

    this.source.connect(this.processor);
    this.processor.connect(this.ctx.destination);
  }

  stop() {
    this.stopping = true;
    this.processor?.disconnect();
    this.source?.disconnect();
    this.stream?.getTracks().forEach((t) => t.stop());
    this.ws?.close();
    this.ctx?.close();
    this.onStatus("stopped");
  }

  private onMessage(e: MessageEvent) {
    if (typeof e.data === "string") {
      this.onResult(JSON.parse(e.data) as Result);
    } else {
      this.playPcm(new Int16Array(e.data as ArrayBuffer));
    }
  }

  private playPcm(pcm: Int16Array) {
    if (!this.ctx) return;
    const buffer = this.ctx.createBuffer(1, pcm.length, TARGET_RATE);
    const channel = buffer.getChannelData(0);
    for (let i = 0; i < pcm.length; i++) channel[i] = pcm[i] / 32767;

    const node = this.ctx.createBufferSource();
    node.buffer = buffer;
    node.connect(this.ctx.destination);
    const at = Math.max(this.ctx.currentTime, this.playHead);
    node.start(at);
    this.playHead = at + buffer.duration;
  }
}

function downsample(input: Float32Array, from: number, to: number): Float32Array {
  if (to >= from) return input;
  const ratio = from / to;
  const out = new Float32Array(Math.floor(input.length / ratio));
  for (let i = 0; i < out.length; i++) {
    const start = Math.floor(i * ratio);
    const end = Math.floor((i + 1) * ratio);
    let sum = 0;
    for (let j = start; j < end; j++) sum += input[j];
    out[i] = sum / (end - start);
  }
  return out;
}

function floatToInt16(input: Float32Array): ArrayBuffer {
  const out = new Int16Array(input.length);
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]));
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return out.buffer;
}
