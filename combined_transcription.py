from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
import sys
import json
import time
import asyncio
import os
from langchain_openai import ChatOpenAI
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import re

def chunk_text_with_overlap(text):
    # 定义句子结束的正则模式（支持中文和英文）
    sentence_end_pattern = r'(?<=[。！？!?\.\?!])\s*'
    
    # 按句子分割文本
    sentences = re.split(sentence_end_pattern, text)
    # 过滤掉可能出现的空句子
    sentences = [s for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = []
    current_char_count = 0
    target_chars = 1250
    
    for sentence in sentences:
        # 计算当前句子的字符数
        sentence_char_count = len(sentence)
        
        # 如果添加当前句子会超过目标字符数且当前块已有内容，创建新块
        if current_char_count + sentence_char_count > target_chars and current_chunk:
            chunks.append(''.join(current_chunk))
            current_chunk = [sentence]
            current_char_count = sentence_char_count
        else:
            # 否则将句子添加到当前块
            current_chunk.append(sentence)
            current_char_count += sentence_char_count
    
    # 添加最后一个块（如果有）
    if current_chunk:
        chunks.append(''.join(current_chunk))
    
    return chunks

async def process_chunk(llm, fixed_prompt, chunk, chunk_index, total_chunks):
    start_time = time.time()
    print(f"正在处理第 {chunk_index+1}/{total_chunks} 个文本块...")
    
    input_text = fixed_prompt + chunk
    
    # 使用线程池执行LLM调用，避免阻塞事件循环
    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        r = await loop.run_in_executor(executor, partial(llm.invoke, input_text))
    
    elapsed_time = time.time() - start_time
    print(f"第 {chunk_index+1} 个文本块处理完成，耗时: {elapsed_time:.2f} 秒")
    return r.content

async def process_transcription():
    # 直接在代码中设置API密钥
    api_key = "sk-2b8340a477294b0e84852ba9028fe759"

    # 修改为DeepSeek模型配置
    llm = ChatOpenAI(
        openai_api_key=api_key,
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        temperature=0,
        max_tokens=8192,
    )

    with open("prompt_tra.txt", "r", encoding="utf-8") as f:
        fixed_prompt = f.read()

    with open("transcription_result.txt", "r", encoding="utf-8") as f:
        user_input = f.read()

    chunks = chunk_text_with_overlap(user_input)
    print(f"开始处理 {len(chunks)} 个文本块...")
    start_time = time.time()

    # 创建任务列表
    tasks = []
    for i, chunk in enumerate(chunks):
        tasks.append(process_chunk(llm, fixed_prompt, chunk, i, len(chunks)))

    # 并发执行所有任务
    results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time
    print(f"所有文本块处理完成，总耗时: {total_time:.2f} 秒")

    # 保存第一次调用大模型后多个切片合成的结果
    combined_output = "".join(results)
    with open("combined_output.txt", "w", encoding="utf-8") as f:
        f.write(combined_output)
    print("已保存切片合成结果到 combined_output.txt")

    # 保存中间结果供第二个脚本使用
    with open("intermediate_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("已保存中间结果到 intermediate_results.json")

def main():
    # 接收文件名参数
    if len(sys.argv) < 2:
        print("请提供音频文件名作为参数")
        sys.exit(1)

    input_file = sys.argv[1]

    # 加载模型
    print("正在加载SenseVoice模型...")
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
    print("开始处理音频文件...")
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
    
    # 运行转录处理部分
    print("开始处理转录文本...")
    asyncio.run(process_transcription())

if __name__ == "__main__":
    main()