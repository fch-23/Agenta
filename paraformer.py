import json
from funasr import AutoModel

model = AutoModel(model="model/speech_paraformer-large-vad-punc-spk_asr_nat-zh-cn",
                  vad_model="model/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                  punc_model="model/punc_ct-transformer_cn-en-common-vocab471067-large",
                  spk_model="model/speech_campplus_sv_zh-cn_16k-common",
                  disable_update=True,  # 禁用更新检查
                  )
res = model.generate(input=f"example/json.mp3", 
            batch_size_s=300, 
            hotword='json')

with open("result.json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=4)

spk = 0

with open("result2.txt", "w", encoding="utf-8") as f:
    f.write(f"说话人 1:\n")
    for item in res:
        if "sentence_info" in item:
            for sentence in item["sentence_info"]:
                if spk != sentence['spk']:
                    f.write(f"\n\n说话人 {sentence['spk']+1}:\n")
                f.write(f"{sentence['text']}")
                spk = sentence['spk']