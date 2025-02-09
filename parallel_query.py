import asyncio
import os
import json
from typing import Dict, Any
from get_previous_result import get_record_withReasoning
from check_function import check_pyramid_file_format
from chat2llm import async_chat_claude
import logging
from model_structure import modules
from prompt_config import prompt_record_repace_list


async def check_existing_result(result_path: str, primary_result_path: str) -> bool:
    """检查是否存在有效的结果文件
    Check if valid result files exist
    """
    # 检查正式结果文件
    # Check formal result file
    if os.path.exists(result_path):
        is_valid = await check_pyramid_file_format(result_path)
        if is_valid:
            logging.info(f"发现有效的已存在结果: {result_path}")
            logging.info(f"Found valid existing result: {result_path}")
            return True
    
    # 检查原始结果文件
    # Check primary result file
    if os.path.exists(primary_result_path):
        is_valid = await check_pyramid_file_format(primary_result_path)
        if is_valid:
            logging.info(f"发现有效的已存在原始结果: {primary_result_path}")
            logging.info(f"Found valid existing primary result: {primary_result_path}")
            # 将验证通过的原始结果复制到正式结果文件
            # Copy validated primary result to formal result file
            with open(primary_result_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    
    return False


async def process_parallel_requests(module_name: str, layer_name: str, input_data: Dict[str, Any],
                                    previous_results: Dict[str, str] = None) -> Dict[str, str]:
    logging.info(f"\n=== 开始处理模块 {module_name} 的 {layer_name} 层 ===")
    logging.info(f"\n=== Start processing module {module_name} layer {layer_name} ===")
    print(f"input_Data{input_data}")

    module_config = modules[module_name]
    module_type = module_config["module_type"]
    llms_dict = module_config["LLMs_dict"]

    layer_config = module_type[layer_name]
    parallel_num = layer_config["parallel_num"]
    model_types = layer_config["model_type"]
    prompt_type = layer_config["prompt_type"]
    previous_sampling = layer_config.get("previousSampling", None)
    prompt_path = input_data["path_query"]
    print(f"开始读取{prompt_path}")
    print(f"Start reading {prompt_path}")
    # 读取病历信息
    # Read medical record information
    with open(prompt_path, "r", encoding="utf-8") as f:
        dict_content = dict(json.load(f))
        primary_content = dict_content["Primary Symptom"]
        presentation_content = dict_content["Presentation of Case"]
    # print(primary_content,presentation_content)
    results = {}
    tasks = []
    for i in range(parallel_num):
        if i < len(model_types):
            llm_key = model_types[i]
            model_name = llms_dict[llm_key]
            prompt_path = input_data["prompt_path"] + "\\" + prompt_type + ".txt"
            prompt_primary = open(prompt_path, "r", encoding="utf-8").read()

            # 构建基础提示词
            # Build base prompt
            prompt = prompt_primary.replace(
                "{$Primary Symptom$}", primary_content).replace(
                "{$Presentation of Case$}", presentation_content).replace(
                "{$question$}", input_data["question"])
            print("primary_content:",primary_content, "\n提问内容:",prompt)
            print("primary_content:",primary_content, "\nQuestion content:",prompt)
            # 处理前轮对话结果
            if previous_sampling and previous_results:
                print(f"\n=== 处理层 {layer_name} 的前轮对话结果 ===")
                print(f"\n=== Processing previous round results for layer {layer_name} ===")
                print(f"Previous sampling paths: {previous_sampling}")

                formatted_answers = []
                for prev_paths in previous_sampling:
                    print(f"\n处理路径组: {prev_paths}")
                    print(f"\nProcessing path group: {prev_paths}")
                    paths = [prev_paths] if not isinstance(prev_paths, (tuple, list)) else prev_paths
                    print(f"转换后的路径: {paths}")
                    print(f"Converted paths: {paths}")

                    for p in paths:
                        if "Multiple" in module_name:
                            result_path = os.path.join(input_data["save_dir"], f"Multiple_{p}.txt")
                        else:
                            result_path = os.path.join(input_data["save_dir"], f"Single_{p}.txt")

                        print(f"尝试读取文件: {result_path}")
                        print(f"Attempting to read file: {result_path}")
                        if os.path.exists(result_path):
                            formatted_answer = get_record_withReasoning(result_path)
                            formatted_answers.append(formatted_answer)
                            print(f"成功读取答案，长度: {len(formatted_answer)} 字符")
                            print(f"Successfully read answer, length: {len(formatted_answer)} characters")
                            print(f"答案前100字符: {formatted_answer[:100]}...")
                            print(f"First 100 characters of answer: {formatted_answer[:100]}...")
                        else:
                            print(f"文件不存在: {result_path}")
                            print(f"File does not exist: {result_path}")

                print(f"\n收集到的答案数量: {len(formatted_answers)}")
                print(f"\nNumber of collected answers: {len(formatted_answers)}")
                print(f"待替换的占位符: {prompt_record_repace_list[:len(formatted_answers)]}")
                print(f"Placeholders to be replaced: {prompt_record_repace_list[:len(formatted_answers)]}")

                # 一次性完成所有替换
                # Complete all replacements at once
                print("\n开始替换过程:")
                print("\nStarting replacement process:")
                print(f"替换前的prompt片段: ...{prompt[-200:] if len(prompt) > 200 else prompt}")
                print(f"Prompt fragment before replacement: ...{prompt[-200:] if len(prompt) > 200 else prompt}")
                for idx, answer in enumerate(formatted_answers):
                    if idx < len(prompt_record_repace_list):
                        old_prompt = prompt
                        prompt = prompt.replace(prompt_record_repace_list[idx], answer)
                        if old_prompt == prompt:
                            print(f"警告: 占位符 {prompt_record_repace_list[idx]} 未能成功替换")
                            print(f"Warning: Placeholder {prompt_record_repace_list[idx]} was not successfully replaced")
                        else:
                            print(f"成功替换占位符 {prompt_record_repace_list[idx]}")
                            print(f"Successfully replaced placeholder {prompt_record_repace_list[idx]}")

                print(f"\n最终prompt片段: ...{prompt[-200:] if len(prompt) > 200 else prompt}")
                print(f"\nFinal prompt fragment: ...{prompt[-200:] if len(prompt) > 200 else prompt}")

            # 确定结果文件路径
            save_dir = input_data.get("save_dir", "results")
            if "inputLayer" in layer_name:
                base_filename = f"{module_name}_{layer_name}_{llm_key}"
            else:
                base_filename = f"{module_name}_{layer_name}"
            
            result_path = os.path.join(save_dir, f"{base_filename}.txt")
            primary_result_path = os.path.join(save_dir, f"{base_filename}_primary.txt")

            # 检查是否存在有效结果
            # Check if valid result exists
            has_valid_result = await check_existing_result(result_path, primary_result_path)
            if has_valid_result:
                # 如果存在有效结果，读取现有文件
                # If valid result exists, read existing file
                with open(result_path, "r", encoding="utf-8") as f:
                    result = f.read()
                results[llm_key] = result
                logging.info(f"使用现有的有效结果: {result_path}")
                logging.info(f"Using existing valid result: {result_path}")
                continue

            # 如果不存在有效结果，创建新的任务
            # If no valid result exists, create new task
            task = asyncio.create_task(async_chat_claude(prompt, model_name))
            tasks.append((llm_key, task))

    # 保存结果路径
    # Save result path
    save_dir = input_data.get("save_dir", "results")
    os.makedirs(save_dir, exist_ok=True)

    for llm_key, task in tasks:
        try:
            # 确定结果文件名
            # Determine result filename
            if "inputLayer" in layer_name:
                base_filename = f"{module_name}_{layer_name}_{llm_key}"
            else:
                base_filename = f"{module_name}_{layer_name}"
            
            # 检查是否已存在有效结果
            # Check if valid result already exists
            result_path = os.path.join(save_dir, f"{base_filename}.txt")
            if os.path.exists(result_path):
                # 验证现有文件的格式
                # Validate existing file format
                is_valid = await check_pyramid_file_format(result_path)
                if is_valid:
                    # 如果存在且格式正确，直接读取现有结果
                    # If exists and format is correct, read existing result directly
                    with open(result_path, "r", encoding="utf-8") as f:
                        result = f.read()
                    logging.info(f"使用现有的有效结果: {result_path}")
                    logging.info(f"Using existing valid result: {result_path}")
                    results[llm_key] = result
                    # 取消未执行的任务
                    # Cancel unexecuted task
                    task.cancel()
                    continue
            
            # 如果不存在有效结果，执行LLM调用
            # If no valid result exists, execute LLM call
            result = await task
            if not result or not isinstance(result, str):
                raise ValueError(f"任务 {llm_key} 返回了无效的结果")
                raise ValueError(f"Task {llm_key} returned invalid result")
            results[llm_key] = result

            # 首先保存LLM的直接回答结果（带_primary）
            # First save LLM's direct response result (with _primary)
            primary_result_path = os.path.join(save_dir, f"{base_filename}_primary.txt")
            with open(primary_result_path, "w", encoding="utf-8") as f:
                f.write(result)
                logging.info(f"保存原始结果到: {primary_result_path}")
                logging.info(f"Saved primary result to: {primary_result_path}")

            # 进行格式校验
            # Perform format validation
            is_valid = await check_pyramid_file_format(primary_result_path)
            if is_valid:
                # 如果校验通过，将校验后的内容保存到正式文件（不带_primary）
                # If validation passes, save validated content to formal file (without _primary)
                result_path = os.path.join(save_dir, f"{base_filename}.txt")
                with open(result_path, "w", encoding="utf-8") as f:
                    f.write(result)
                    logging.info(f"保存校验后的结果到: {result_path}")
                    logging.info(f"Saved validated result to: {result_path}")
            else:
                logging.warning(f"警告: {primary_result_path} 的格式校验失败")
                logging.warning(f"Warning: Format validation failed for {primary_result_path}")

            # 保存prompt
            prompt_path = os.path.join(save_dir, f"{base_filename}_prompt.txt")
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt)

        except Exception as e:
            logging.error(f"处理任务 {llm_key} 时发生错误: {str(e)}")
            logging.error(f"Error occurred while processing task {llm_key}: {str(e)}")
            continue

    return results