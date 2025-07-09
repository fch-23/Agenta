from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

# 本地模型路径
model_dir = "model/SenseVoiceSmall"

# 加载模型
model = AutoModel(
    model=model_dir,
    trust_remote_code=False,  # 禁用远程代码加载
    vad_model="model/speech_fsmn_vad_zh-cn-16k-common-pytorch",
    vad_kwargs={"max_single_segment_time": 30000},
    device="cuda:0",
    disable_tqdm=True,  # 禁用进度条
    disable_update=True,  # 禁用更新检查
)

# 处理音频文件
res = model.generate(
    input=f"example/json.mp3",
    cache={},
    language="auto",  # 自动检测语言
    use_itn=True,
    batch_size_s=60,
    merge_vad=True,
    merge_length_s=15,
)

# 后处理并输出结果
text = rich_transcription_postprocess(res[0]["text"])

# 将结果保存到 result 文件中
with open("result1.txt", "w", encoding="utf-8") as f:
    f.write(text)