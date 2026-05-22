const TARGET_SAMPLE_RATE = 16000;
const callButton = document.getElementById("callButton");
const statusEl = document.getElementById("status");

let audioContext = null;
let mediaStream = null;
let mediaSource = null;
let inputProcessor = null;
let muteGain = null;
let socket = null;
let isActive = false;
let isStopping = false;
let nextPlaybackTime = 0;

function setStatus(message) {
    statusEl.textContent = message;
}

function updateButton(active, disabled = false) {
    callButton.textContent = active ? "Put" : "Call";
    callButton.dataset.active = String(active);
    callButton.setAttribute("aria-pressed", String(active));
    callButton.disabled = disabled;
}

function buildSocketUrl() {
    const params = new URLSearchParams(window.location.search);
    const override = params.get("ws");

    if (override) {
        return override;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.hostname || "127.0.0.1";
    return `${protocol}//${host}:8000/ws`;
}

function resampleAudio(input, fromSampleRate, toSampleRate) {
    if (fromSampleRate === toSampleRate) {
        return new Float32Array(input);
    }

    const ratio = fromSampleRate / toSampleRate;
    const outputLength = Math.max(1, Math.round(input.length / ratio));
    const output = new Float32Array(outputLength);

    for (let index = 0; index < outputLength; index += 1) {
        const position = index * ratio;
        const before = Math.floor(position);
        const after = Math.min(before + 1, input.length - 1);
        const blend = position - before;
        output[index] = input[before] + (input[after] - input[before]) * blend;
    }

    return output;
}

function floatToPcm16(floatSamples) {
    const pcm16 = new Int16Array(floatSamples.length);

    for (let index = 0; index < floatSamples.length; index += 1) {
        const sample = Math.max(-1, Math.min(1, floatSamples[index]));
        pcm16[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
    }

    return pcm16.buffer;
}

function pcm16ToFloat32(buffer) {
    const pcm16 = new Int16Array(buffer);
    const float32 = new Float32Array(pcm16.length);

    for (let index = 0; index < pcm16.length; index += 1) {
        float32[index] = pcm16[index] / 0x8000;
    }

    return float32;
}

function playIncomingChunk(arrayBuffer) {
    if (!audioContext) {
        return;
    }

    const pcmFloat = pcm16ToFloat32(arrayBuffer);
    const outputRate = audioContext.sampleRate;
    const resampled = resampleAudio(pcmFloat, TARGET_SAMPLE_RATE, outputRate);
    const audioBuffer = audioContext.createBuffer(1, resampled.length, outputRate);

    audioBuffer.copyToChannel(resampled, 0);

    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);

    const startAt = Math.max(audioContext.currentTime + 0.03, nextPlaybackTime);
    source.start(startAt);
    nextPlaybackTime = startAt + audioBuffer.duration;
}

async function createSocket(url) {
    return await new Promise((resolve, reject) => {
        const ws = new WebSocket(url);
        ws.binaryType = "arraybuffer";

        const handleOpen = () => {
            cleanup();
            resolve(ws);
        };

        const handleError = () => {
            cleanup();
            reject(new Error("WebSocket connection failed."));
        };

        const cleanup = () => {
            ws.removeEventListener("open", handleOpen);
            ws.removeEventListener("error", handleError);
        };

        ws.addEventListener("open", handleOpen);
        ws.addEventListener("error", handleError);
    });
}

async function startCall() {
    updateButton(false, true);
    setStatus("Connecting...");

    try {
        const socketUrl = buildSocketUrl();
        console.log("Opening WebSocket:", socketUrl);
        setStatus(`Connecting to ${socketUrl}`);
        socket = await createSocket(socketUrl);
        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
            },
        });

        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        await audioContext.resume();

        mediaSource = audioContext.createMediaStreamSource(mediaStream);
        inputProcessor = audioContext.createScriptProcessor(4096, 1, 1);
        muteGain = audioContext.createGain();
        muteGain.gain.value = 0;

        mediaSource.connect(inputProcessor);
        inputProcessor.connect(muteGain);
        muteGain.connect(audioContext.destination);

        inputProcessor.onaudioprocess = (event) => {
            if (!socket || socket.readyState !== WebSocket.OPEN) {
                return;
            }

            const inputChannel = event.inputBuffer.getChannelData(0);
            const resampled = resampleAudio(inputChannel, audioContext.sampleRate, TARGET_SAMPLE_RATE);
            socket.send(floatToPcm16(resampled));
        };

        socket.addEventListener("message", async (event) => {
            const payload = event.data instanceof Blob ? await event.data.arrayBuffer() : event.data;
            playIncomingChunk(payload);
        });

        socket.addEventListener("close", () => {
            if (!isStopping) {
                stopCall("Disconnected");
            }
        });

        socket.addEventListener("error", () => {
            if (!isStopping) {
                stopCall("Connection error");
            }
        });

        isActive = true;
        nextPlaybackTime = audioContext.currentTime;
        updateButton(true, false);
        setStatus("Live");
    } catch (error) {
        console.error(error);
        await stopCall("Unable to start");
    }
}

async function stopCall(message = "Ready") {
    isStopping = true;
    isActive = false;
    updateButton(false, true);

    if (inputProcessor) {
        inputProcessor.onaudioprocess = null;
        inputProcessor.disconnect();
        inputProcessor = null;
    }

    if (mediaSource) {
        mediaSource.disconnect();
        mediaSource = null;
    }

    if (muteGain) {
        muteGain.disconnect();
        muteGain = null;
    }

    if (mediaStream) {
        mediaStream.getTracks().forEach((track) => track.stop());
        mediaStream = null;
    }

    if (socket && socket.readyState < WebSocket.CLOSING) {
        socket.close();
    }
    socket = null;

    if (audioContext) {
        await audioContext.close();
        audioContext = null;
    }

    nextPlaybackTime = 0;
    updateButton(false, false);
    setStatus(message);
    isStopping = false;
}

callButton.addEventListener("click", async () => {
    if (isActive) {
        await stopCall("Ready");
        return;
    }

    await startCall();
});
