import os
import json
import re
import asyncio
from typing import Dict, List
from chat2llm import async_chat_claude
from prompt_config import pattern1, pattern2, pattern3, pattern4
from typing import Dict, Any
import logging
from get_previous_result import get_record_withReasoning


async def batch_formatCheck(txt_paths: List[str], batch_size: int = 5) -> Dict[str, bool]:
    """
    批量并行检查文件格式并在需要时进行校正
    Batch parallel format checking and correction if needed

    Args:
        txt_paths: 需要检查的文件路径列表 (List of file paths to check)
        batch_size: 每批并行处理的文件数量 (Number of files to process in parallel per batch)

    Returns:
        Dict[str, bool]: 文件路径到格式检查结果的映射 (Mapping of file paths to format check results)
    """
    results = {}

    async def check_single_file(txt_path: str) -> bool:
        print(f"\n开始格式检查 / Starting format check: {txt_path}")
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read().replace(
                    "$$", "$").replace("$$$", "$").replace("<${", "<$[{").replace("}$>", "}]$>").replace(
                    '."},', '."}},').replace("\n", "").replace("$<$", "<$")

            # 尝试直接解析
            try:
                json.loads(content)
                print(f"{txt_path}: 文件格式正确 / File format is correct")
                return True
            except json.JSONDecodeError:
                pass

            # 尝试使用正则表达式
            for pattern in [pattern1, pattern2, pattern3]:
                try:
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        extracted_content = match.group(1)
                        eval(extracted_content)
                        print(f"{txt_path}: 文件格式正确 / File format is correct")
                        return True
                except:
                    continue

            # 如果以上方法都失败，使用LLM校正
            print(f"{txt_path}: 格式检查失败，开始LLM校正 / Format check failed, starting LLM correction")

            # 确保原始文件保存为带_primary的版本
            if not txt_path.endswith("_primary.txt"):
                primary_path = txt_path.replace(".txt", "_primary.txt")
                with open(primary_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"保存原始内容到 / Saving original content to: {primary_path}")

            # 读取格式校正prompt模板
            correction_prompt_path = (".\\prompt\\formatChecker.txt")
            with open(correction_prompt_path, "r", encoding="utf-8") as f:
                correction_prompt_template = f.read()


            # 替换模板中的占位符
            correction_prompt = correction_prompt_template.replace("{%primary_record%}", content)

            # 异步调用LLM进行校正
            corrected_result = await async_chat_claude(
                correction_prompt,
                "gpt-4o-mini"
            )

            corrected_result = corrected_result.replace(
                "$$", "$").replace("$$$", "$").replace("<${", "<$[{").replace("}$>", "}]$>").replace(
                '."},', '."}},').replace("\n", "").replace("$<$", "<$")

            # 将校正后的结果保存到不带_primary的文件中
            corrected_path = txt_path.replace("_primary.txt", ".txt") if "_primary" in txt_path else txt_path
            with open(corrected_path, "w", encoding="utf-8") as f:
                f.write(corrected_result)
                print(f"保存LLM校正后的结果到 / Saving LLM corrected result to: {corrected_path}")

            # 验证校正后的结果格式
            def extract_json_content(text):
                # 1. 尝试直接解析整个文本
                try:
                    json.loads(text)
                    return True
                except json.JSONDecodeError:
                    pass

                # 2. 尝试提取JSON代码块
                json_patterns = [pattern1, pattern2, pattern3, pattern4]
                for pattern in json_patterns:
                    matches = re.finditer(pattern, text, re.DOTALL)
                    for match in matches:
                        try:
                            content = match.group(1).strip()
                            json.loads(content)
                            return True
                        except (json.JSONDecodeError, IndexError):
                            continue
                return False

            # 检查校正后的结果
            is_valid = extract_json_content(corrected_result)
            if is_valid:
                print(f"{txt_path}: LLM校正后格式正确 / Format correct after LLM correction")
                return True
            else:
                print(f"{txt_path}: LLM校正后仍然格式错误 / Format still incorrect after LLM correction")
                return False

        except Exception as e:
            print(f"{txt_path}: 格式检查过程出错 / Error during format check: {str(e)}")
            return False

    # 分批处理文件
    for i in range(0, len(txt_paths), batch_size):
        batch = txt_paths[i:i + batch_size]
        batch_tasks = [check_single_file(path) for path in batch]
        try:
            batch_results = await asyncio.gather(*batch_tasks)
            for path, result in zip(batch, batch_results):
                results[path] = result
        except Exception as e:
            print(f"批处理出错 / Batch processing error: {str(e)}")
            continue

    return results



async def check_pyramid_file_format(txt_path: str) -> bool:
    """
    专门用于金字塔框架的文件格式检查函数
    Dedicated format checking function for pyramid framework files

    Args:
        txt_path: 需要检查的文件路径 (File path to check)

    Returns:
        bool: 文件格式是否有效 (Whether the file format is valid)
    """
    logging.info(f"[金字塔框架/Pyramid Framework] 开始检查文件格式 / Starting format check: {txt_path}")
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read().replace(
                "$$", "$").replace("$$$", "$").replace("<${", "<$[{").replace("}$>", "}]$>").replace(
                '."},', '."}},').replace("\n", "").replace("$<$", "<$")

        # 尝试直接解析
        try:
            json.loads(content)
            logging.info(f"[金字塔框架] {txt_path}: 文件格式正确")
            return True
        except json.JSONDecodeError:
            pass

        # 尝试使用正则表达式
        for pattern in [pattern1, pattern2, pattern3, pattern4]:
            try:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    extracted_content = match.group(1)
                    eval(extracted_content)
                    logging.info(f"[金字塔框架] {txt_path}: 文件格式正确（通过正则表达式）")
                    return True
            except:
                continue

        # 如果以上方法都失败，使用LLM校正
        logging.warning(f"[金字塔框架] {txt_path}: 格式检查失败，开始LLM校正")

        # 读取格式校正prompt模板
        correction_prompt_path = os.path.join("prompt",
                                              "formatChecker.txt")
        with open(correction_prompt_path, "r", encoding="utf-8") as f:
            correction_prompt_template = f.read()

        # 替换模板中的占位符
        correction_prompt = correction_prompt_template.replace("{%primary_record%}", content)

        # 异步调用LLM进行校正
        corrected_result = await async_chat_claude(
            correction_prompt,
            "gpt-4o-mini"
        )

        # 处理校正后的结果
        corrected_result = corrected_result.replace(
            "$$", "$").replace("$$$", "$").replace("<${", "<$[{").replace("}$>", "}]$>").replace(
            '."},', '."}},').replace("\n", "").replace("$<$", "<$")

        # 将校正后的结果保存到不带_primary的文件中
        corrected_path = txt_path.replace("_primary.txt", ".txt")
        with open(corrected_path, "w", encoding="utf-8") as f:
            f.write(corrected_result)
            logging.info(f"[金字塔框架] 保存LLM校正后的结果到: {corrected_path}")

        # 验证校正后的结果格式
        def extract_json_content(text):
            # 1. 尝试直接解析整个文本
            try:
                json.loads(text)
                return True
            except json.JSONDecodeError:
                pass

            # 2. 尝试提取JSON代码块
            json_patterns = [pattern1, pattern2, pattern3, pattern4]
            for pattern in json_patterns:
                matches = re.finditer(pattern, text, re.DOTALL)
                for match in matches:
                    try:
                        content = match.group(1).strip()
                        json.loads(content)
                        return True
                    except (json.JSONDecodeError, IndexError):
                        continue
            return False

        # 检查校正后的结果
        is_valid = extract_json_content(corrected_result)
        if is_valid:
            logging.info(f"[金字塔框架] {txt_path}: LLM校正后格式正确")
            return True
        else:
            logging.error(f"[金字塔框架] {txt_path}: LLM校正后仍然格式错误")
            return False

    except Exception as e:
        logging.error(f"[金字塔框架/Pyramid Framework] 检查文件时发生错误 / Error checking file {txt_path}: {str(e)}")
        return False


async def verify_layer_completion(module_name: str, layer_name: str, save_dir: str, results: Dict[str, str]):
    """验证层的完成状态"""
    max_retries = 3
    retry_delay = 2

    for retry in range(max_retries):
        missing_files = []

        for llm_key in results.keys():
            if "inputLayer" in layer_name:
                result_file = os.path.join(save_dir, f"{module_name}_{layer_name}_{llm_key}.txt")
            else:
                result_file = os.path.join(save_dir, f"{module_name}_{layer_name}.txt")

            if not os.path.exists(result_file):
                missing_files.append(result_file)

        if not missing_files:
            return True

        if retry < max_retries - 1:
            logging.warning(f"等待文件生成，重试 {retry + 1}/{max_retries}")
            logging.warning(f"缺失文件: {missing_files}")
            await asyncio.sleep(retry_delay)

    raise FileNotFoundError(f"验证失败，以下文件未生成: {missing_files}")


def validate_pyramid_config(config: Dict[str, Dict[str, Any]]) -> bool:
    """
    验证金字塔框架配置的正确性
    Validate the correctness of pyramid framework configuration
    """
    required_keys = {"layerNum", "parallel_num", "model_type", "previousSampling", "prompt_type"}

    for layer_name, layer_config in config.items():
        if not all(key in layer_config for key in required_keys):
            print(f"层 {layer_name} 缺少必要的配置键 / Layer {layer_name} missing required configuration keys")
            return False

        if layer_config["parallel_num"] != len(layer_config["model_type"]):
            print(f"层 {layer_name} 的并行数量与模型类型数量不匹配 / Layer {layer_name} parallel count doesn't match model type count")
            return False

    return True


def validate_layer_completion(layer_name: str, file_list: List[str], expected_count: int):
    """
    验证层是否完全完成
    Validate if the layer is completely finished
    """
    if len(file_list) != expected_count:
        raise RuntimeError(
            f"{layer_name} 未完全完成。预期文件数: {expected_count}, 实际文件数: {len(file_list)}"
        )

    for file_path in file_list:
        if not os.path.exists(file_path):
            raise RuntimeError(f"{layer_name} 文件缺失: {file_path}")