import whisper

model_path = 'model\\whisper\\large-v3.pt'
model = whisper.load_model(model_path, device="cuda")

result = model.transcribe("example/1.mp3")

print(result["text"])