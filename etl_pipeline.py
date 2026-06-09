import pandas as pd
import base64
import requests
import os
import time
import random
from dotenv import load_dotenv

# ==========================================
# 0. 架构初始化：安全解耦与环境变量加载
# ==========================================
print("🔧 正在初始化工业级 ETL 自动化管线...")
load_dotenv() # 自动读取本地 .env 文件

# 从系统环境变量提取机密凭证，彻底杜绝硬编码 (Hardcoding)
ENCRYPTED_CONN = os.getenv("CREDIBLE_API_KEY")
IMPORT_URL = os.getenv("CREDIBLE_IMPORT_URL")

if not ENCRYPTED_CONN or not IMPORT_URL:
    raise ValueError("🚨 致命错误：环境变量未加载！请检查 .env 文件是否存在并配置正确。")

print("🔥 终极荣耀：高吞吐量 CSV 直连引擎启动 (挂载指数退避护盾)...\n")

# ==========================================
# 1. 数据抽取 (Extract)：模拟上游数据源
# ==========================================
# 真实生产环境中，这里可能是通过 SQLAlchemy 从 SQL Server 提取的数万条历史记录
mock_client_data = [
    {"Internal_ID": f"{100000 + i}", "Target_DOB": "12/20/2010"} 
    for i in range(1250)
]
df_total = pd.DataFrame(mock_client_data)
total_rows = len(df_total)

# ==========================================
# 2. 核心工程参数配置
# ==========================================
CHUNK_SIZE = 500       # 内存切片大小：单批次最大吞吐量
MAX_RETRIES = 3        # 韧性机制：最大允许网络重试次数
BASE_DELAY = 2.0       # 韧性机制：基础退避时间 (秒)

print(f"📊 任务清点：捕获总计 {total_rows} 条记录。")
print(f"⚙️  管线配置：单批吞吐 {CHUNK_SIZE} 条 | 最大重试 {MAX_RETRIES} 次。\n")

# ==========================================
# 3. 数据转换与加载引擎 (Transform & Load)
# ==========================================
batch_count = 0

for i in range(0, total_rows, CHUNK_SIZE):
    batch_count += 1
    
    # [3.1 数据切片]
    df_chunk = df_total.iloc[i : i + CHUNK_SIZE]
    current_chunk_size = len(df_chunk)
    
    print(f"📦 [Batch {batch_count}] 开始处理数据区间: 行 {i} 至 {i + current_chunk_size}...")

    # [3.2 内存级清洗与序列化]
    # header=False 极其重要，确保只传输纯数据，避免下游 EHR 系统解析表头崩溃
    csv_raw_string = df_chunk.to_csv(index=False, header=False, lineterminator='\r\n')
    encoded_file_string = base64.b64encode(csv_raw_string.encode('utf-8')).decode('utf-8')

    # [3.3 动态构建 SOAP Payload]
    xml_payload = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Import xmlns="https://www.crediblebh.com/">
      <connection>{ENCRYPTED_CONN}</connection>
      <encodedfile>{encoded_file_string}</encodedfile>
    </Import>
  </soap:Body>
</soap:Envelope>"""

    HEADERS = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": '"https://www.crediblebh.com/Import"' 
    }

    # [3.4 挂载指数退避重试护盾发射]
    for attempt in range(MAX_RETRIES):
        try:
            # 保护性限频：正常请求间的微小延迟，防止触发 API 速率限制
            if batch_count > 1 and attempt == 0:
                time.sleep(0.5) 
                
            # timeout=15 防止服务器僵死导致脚本永久挂起
            response = requests.post(IMPORT_URL, data=xml_payload, headers=HEADERS, timeout=15)
            result_text = response.text
            
            # [3.5 战报解析与深层异常拦截]
            if "<ImportResult>" in result_text:
                start_idx = result_text.find("<ImportResult>") + len("<ImportResult>")
                end_idx = result_text.find("</ImportResult>")
                core_message = result_text[start_idx:end_idx]
                
                print(f"  ✅ 吞吐成功！响应条数: {current_chunk_size} 条 | 战报: {core_message.strip()}")
                break # 💥 成功突围，跳出重试循环，直接进入下一个 Batch
            else:
                # 触发业务级异常，被下方的 except 捕获并进入重试逻辑
                raise ValueError(f"API 返回异常报文或假 200: {result_text[:100]}")

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                # 核心算法：指数退避 + 随机抖动 (Jitter)
                wait_time = BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
                
                print(f"  ⚠️ 遭遇网络乱流 (Attempt {attempt+1}/{MAX_RETRIES}): {e}")
                print(f"  ⏳ 启动指数退避，静默等待 {wait_time:.2f} 秒后发起重组冲击...")
                time.sleep(wait_time)
            else:
                # 重试耗尽，记录错误但不中断整个循环，确保不影响后续健康批次的发送
                print(f"  ❌ 终极崩溃！重试 {MAX_RETRIES} 次均告失败，该批次流产。死因: {e}")
                # 生产环境扩展点：可在此处将失败的 df_chunk 写入 error_log.csv 以备人工修复

print(f"\n🏁 战役结束！全案 {total_rows} 条数据已分 {batch_count} 个批次全自动化处理完毕。")