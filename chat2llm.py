import aiohttp
import time
import requests
import json
import os
from model_config import api_config

async def async_chat_claude(prompt: str, model: str, api_key: str = None, url: str = None) -> str:

    print(f"向{model}通讯\n内容为{prompt}")
    print(f"Communicating with {model}\nContent: {prompt}")

    # 获取模型配置
    # Get model configuration
    model_config = api_config.get(model.lower())
    if not model_config:
        raise ValueError(f"未找到模型 {model} 的配置")
        raise ValueError(f"Configuration not found for model {model}")

    # 使用配置中的值
    # Use values from configuration
    headers = {
        "Authorization": model_config["api_key"],  # 直接使用配置中的api_key / Use api_key directly from config
        "Content-Type": "application/json"
    }

    data = {
        "messages": [{"role": "user", "content": prompt}],
        "model": model_config["model_id"],  # 使用配置中的model_id
        "max_tokens_to_sample": 4090,
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(model_config["url"], headers=headers, json=data) as response:  # 使用配置中的url
            if response.status == 200:
                result = await response.json()
                # time.sleep(3)
                return result['choices'][0]['message']['content']
            else:
                error_text = await response.text()
                raise Exception(f"API调用失败: {response.status}, {error_text}")



def chat_claude(prompt, path_record, log_record, model="claude-3-5-sonnet"):
    start_time = time.time()

    # 获取模型配置
    # Get model configuration
    model_config = api_config.get(model.lower())
    if not model_config:
        raise ValueError(f"未找到模型 {model} 的配置")

    headers = {
        "Authorization": model_config["api_key"],
        "Content-Type": "application/json"
    }

    data = {
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "model": model_config["model_id"],
        "max_tokens_to_sample": 4090,
        "stream": True
    }

    result = ""
    log_string = ""

    try:
        with requests.post(model_config["url"], headers=headers, json=data, stream=True) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        log_string += decoded_line + "\n"
                        if decoded_line.startswith('data: '):
                            try:
                                json_data = json.loads(decoded_line[6:])
                                if 'choices' in json_data and len(json_data['choices']) > 0:
                                    delta = json_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        result += content
                                        print(content, end='', flush=True)
                            except json.JSONDecodeError:
                                pass
                print("\n")

                end_time = time.time()
                total_time = "总耗时: {:.2f}秒".format(end_time - start_time)
                total_time_en = "Total time: {:.2f} seconds".format(end_time - start_time)
                print(total_time)
                print(total_time_en)

                # 保存日志
                # Save logs
                try:
                    with open(log_record, "w", encoding="utf-8") as f:
                        f.write(log_string)
                except Exception as e:
                    print(f"保存日志文件失败: {str(e)}")
                    print(f"Failed to save log file: {str(e)}")

                # 保存结果
                # Save results
                try:
                    os.makedirs(os.path.dirname(path_record), exist_ok=True)
                    with open(path_record, "w", encoding="utf-8") as f:
                        f.write(result)
                        print("txt回答 已保存")
                        print("txt response saved")
                except Exception as e:
                    print(f"保存结果文件失败: {str(e)}")
                    print(f"Failed to save result file: {str(e)}")

                # 保存prompt
                # Save prompt
                try:
                    prompt_path = path_record.replace(".txt","format_prompt.txt")
                    with open(prompt_path, "w", encoding="utf-8") as f:
                        f.write(prompt)
                except Exception as e:
                    print(f"保存prompt文件失败: {str(e)}")
                    print(f"Failed to save prompt file: {str(e)}")

            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                result = f"Error: {response.status_code}\n{response.text}"

    except Exception as e:
        print(f"请求过程中发生错误: {str(e)}")
        result = f"Error: Request failed - {str(e)}"

    return result
