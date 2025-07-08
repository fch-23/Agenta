from vosk import Model, KaldiRecognizer
import wave
import pyaudio
import json
import os

# 1. 加载Vosk模型
model = Model(r"model/vosk-model-cn-0.22")
recognizer = KaldiRecognizer(model, 16000)

# 用于存储所有识别结果
all_results = []

# 检查是否存在音频文件
audio_file = "output.wav"
if os.path.exists(audio_file):
    print("检测到音频文件，使用文件进行识别...")
    wf = wave.open(audio_file, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
        print("音频格式不支持，需转换为16kHz 16bit 单声道PCM")
        exit(1)

    try:
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    all_results.append(text)
                    print("片段结果:", text)

        # 获取最终片段并汇总
        final_result = json.loads(recognizer.FinalResult())
        final_text = final_result.get("text", "").strip()
        if final_text:
            all_results.append(final_text)
    finally:
        wf.close()
else:
    print("未检测到音频文件，使用麦克风进行实时识别...")
    mic = pyaudio.PyAudio()
    stream = mic.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8192
    )
    stream.start_stream()

    try:
        while True:
            data = stream.read(4096, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text_with_punctuation = result.get("text", "").strip()
                if text_with_punctuation:
                    all_results.append(text_with_punctuation)
                    print(text_with_punctuation)
    except KeyboardInterrupt:
        print("\n停止录音")
    finally:
        stream.stop_stream()
        stream.close()
        mic.terminate()

# 输出最终结果
final_result = " ".join(all_results)  # 合并所有结果
print("最终结果:", final_result)