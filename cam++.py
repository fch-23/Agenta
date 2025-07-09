from modelscope.pipelines import pipeline

# 1. 加载预训练模型（指定模型ID）
sv_pipeline = pipeline(
    task='speaker-verification',  # 任务类型：说话人验证
    model='model/speech_campplus_sv_zh-cn_16k-common',  # 预训练模型ID
    model_revision='v1.0.0'  # 模型版本（默认使用最新版）
)

# 2. 定义本地音频路径（支持绝对路径或相对路径）
audio1 = 'example/来自天堂的魔鬼.wav'  # 本地音频1
audio2 = 'example/回忆的沙漏.wav'  # 本地音频2


# # 3. 分析任务1：判断两段本地音频是否为同一说话人
# # 输出结果包含得分（score）和判定结果（text，True表示同一人，False表示不同）
# result = sv_pipeline([audio1, audio2])
# print("是否为同一说话人：", result['text'])
# print("匹配得分：", result['score'])


# 4. 分析任务2：自定义判定阈值（阈值越高，判定越严格）
result = sv_pipeline([audio1, audio2], thr=0.65)
print("匹配得分：", result['score'])
print("自定义阈值后的判定结果：", result['text'])


# # 5. 分析任务3：提取本地音频的说话人特征（embedding）
# # 输出特征向量，可用于后续说话人聚类、建模等
# result_with_emb = sv_pipeline([audio1, audio2], output_emb=True)
# print("说话人1的特征向量：", result_with_emb['embs'][0])  # 对应audio1的特征
# print("说话人2的特征向量：", result_with_emb['embs'][1])  # 对应audio2的特征


# # 6. 分析任务4：将提取的特征保存到本地目录
# # 特征会以文件形式存储在指定路径（如'./speaker_embeddings/'）
# sv_pipeline([audio1, audio2], save_dir='./speaker_embeddings/')
# print("特征已保存至：./speaker_embeddings/")