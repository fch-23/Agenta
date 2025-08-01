from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
import sys

# 接收文件名参数
if len(sys.argv) < 2:
    print("请提供音频文件名作为参数")
    sys.exit(1)

input_file = sys.argv[1]

# 加载模型
model = AutoModel(
    model="model/SenseVoiceSmall",
    trust_remote_code=False,
    vad_model="model/speech_fsmn_vad_zh-cn-16k-common-pytorch",
    vad_kwargs={"max_single_segment_time": 30000},
    device="cuda:0",
    disable_tqdm=True,
    disable_update=True,
)

# 处理音频文件
res = model.generate(
    input=input_file,
    cache={},
    language="auto",
    use_itn=True,
    batch_size_s=60,
    merge_vad=True,
    merge_length_s=15,
)

text = rich_transcription_postprocess(res[0]["text"])

# 保存结果到文件
output_file = "transcription_result.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(text)

print(f"转写结果已保存到 {output_file}")