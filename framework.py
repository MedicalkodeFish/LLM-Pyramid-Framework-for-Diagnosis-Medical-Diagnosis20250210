import os
import logging
from typing import Dict, Any, List
from check_function import check_pyramid_file_format, validate_layer_completion
from build_prompt import build_prompt
from parallel_query import async_chat_claude
from model_structure import pyramid_framework
from model_config import mergeLayer_LLMs_dict
from get_previous_result import get_record_withReasoning
import asyncio

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

async def run_pyramid_framework(input_data: Dict[str, Any], round_results: List[Dict[str, str]]):

    logging.info("\n=== 开始运行金字塔框架 ===")
    logging.info("\n=== Starting Pyramid Framework ===")
    all_results = {}

    # 添加layer_files_to_check字典初始化
    layer_files_to_check = {
        "mergelayer1": [],
        "mergelayer2": [],
        "mergelayer3": [],
        "output": []
    }



    for layer_name, layer_config in pyramid_framework.items():
        logging.info(f"\n处理金字塔层: {layer_name}")
        logging.info(f"\n Processing pyramid layer: {layer_name}")
        try:
            parallel_results = {}

            if layer_name == "mergelayer1":
                # 创建所有轮次的任务
                tasks = []
                for round_idx, round_result in enumerate(round_results):
                    for branch_idx, previous_paths in enumerate(layer_config["previousSampling"]):
                        parallel_idx = round_idx * len(layer_config["previousSampling"]) + branch_idx
                        model_type = layer_config["model_type"][parallel_idx]
                        branch_prefix = "Multiple" if branch_idx == 0 else "Single"

                        async def process_round(r_idx, b_idx, b_prefix, prev_paths, m_type):
                            result_key = f"{b_prefix}_{layer_name}_round_{r_idx + 1}"
                            result_path = os.path.join(input_data["save_dir"], f"{result_key}.txt")
                            primary_result_path = os.path.join(input_data["save_dir"], f"{result_key}_primary.txt")
                            
                            # 检查是否存在有效的结果文件
                            if await check_existing_result(result_path, primary_result_path):
                                with open(result_path, 'r', encoding='utf-8') as f:
                                    result = f.read()
                                return result_key, result, result_path
                            
                            # 如果没有有效结果，继续原有的处理逻辑
                            prev_results = []
                            for path in prev_paths:
                                # 构建正确的路径：在轮次子目录中查找模块结果
                                result_path = os.path.join(
                                    input_data["save_dir"],
                                    f"round_{r_idx + 1}",
                                    f"{path}.txt"
                                )

                                print(f"尝试读取文件: {result_path}")
                                print(f"Attempting to read file: {result_path}")
                                if os.path.exists(result_path):
                                    prev_results.append(get_record_withReasoning(result_path))
                                else:
                                    print(f"警告: 文件不存在: {result_path}")
                                    print(f"Warning: File does not exist: {result_path}")

                            prompt = await build_prompt(
                                input_data,
                                layer_config["prompt_type"],
                                prev_results
                            )
                            # print(input_data[])
                            result = await async_chat_claude(prompt, mergeLayer_LLMs_dict[m_type])

                            # 修正：先保存原始结果（带_primary）
                            # Fix: First save original result (with _primary)
                            result_key = f"{b_prefix}_{layer_name}_round_{r_idx + 1}"
                            primary_result_path = os.path.join(input_data["save_dir"], f"{result_key}_primary.txt")
                            with open(primary_result_path, "w", encoding="utf-8") as f:
                                f.write(result)
                                logging.info(f"保存原始金字塔层结果到: {primary_result_path}")
                                logging.info(f"Saved original pyramid layer result to: {primary_result_path}")

                            # 进行格式校验
                            # Perform format validation
                            is_valid = await check_pyramid_file_format(primary_result_path)
                            if is_valid:
                                # 校验通过后保存到正式文件（不带_primary）
                                # After validation, save to formal file (without _primary)
                                result_path = os.path.join(input_data["save_dir"], f"{result_key}.txt")
                                with open(result_path, "w", encoding="utf-8") as f:
                                    f.write(result)
                                    logging.info(f"保存校验后的金字塔层结果到: {result_path}")
                                    logging.info(f"Saved validated pyramid layer result to: {result_path}")
                            else:
                                logging.warning(f"警告: {primary_result_path} 的格式校验失败")
                                logging.warning(f"Warning: Format validation failed for {primary_result_path}")

                            # 立即进行格式校验
                            is_valid = await check_pyramid_file_format(result_path)
                            if not is_valid:
                                logging.warning(f"警告: {result_path} 的格式校验失败")

                            # 修正：保存prompt到对应的文件
                            prompt_path = os.path.join(input_data["save_dir"], f"{result_key}_prompt.txt")
                            with open(prompt_path, "w", encoding="utf-8") as f:
                                f.write(prompt)

                            return result_key, result, result_path

                        # 添加任务到列表
                        task = process_round(round_idx, branch_idx, branch_prefix, previous_paths, model_type)
                        tasks.append(task)

                # 并行执行所有任务
                results = await asyncio.gather(*tasks)

                # 处理任务结果
                for result_key, result, result_path in results:
                    parallel_results[result_key] = result
                    if layer_name in layer_files_to_check:  # 添加检查
                        layer_files_to_check[layer_name].append(result_path)
                    else:
                        logging.warning(f"未找到层 {layer_name} 的文件检查列表")

                # 在mergelayer1完成后添加验证
                validate_layer_completion("mergelayer1", layer_files_to_check["mergelayer1"],
                                          len(round_results) * len(layer_config["previousSampling"]))

            elif layer_name == "mergelayer2":
                # 创建所有轮次的任务
                tasks = []
                for round_idx, round_result in enumerate(round_results):
                    for branch_idx, previous_paths in enumerate(layer_config["previousSampling"]):
                        parallel_idx = round_idx * len(layer_config["previousSampling"]) + branch_idx
                        model_type = layer_config["model_type"][parallel_idx]
                        branch_prefix = "Multiple" if branch_idx == 0 else "Single"

                        async def process_round(r_idx, b_idx, b_prefix, prev_paths, m_type):
                            result_key = f"{b_prefix}_{layer_name}_round_{r_idx + 1}"
                            result_path = os.path.join(input_data["save_dir"], f"{result_key}.txt")
                            primary_result_path = os.path.join(input_data["save_dir"], f"{result_key}_primary.txt")
                            
                            if await check_existing_result(result_path, primary_result_path):
                                with open(result_path, 'r', encoding='utf-8') as f:
                                    result = f.read()
                                return result_key, result, result_path
                            
                            # 收集前轮结果
                            prev_results = []
                            for path in prev_paths:
                                if "mergelayer1" in path:
                                    # 修正：使用正确的mergelayer1结果路径
                                    result_path = os.path.join(
                                        input_data["save_dir"],
                                        f"{b_prefix}_mergelayer1_round_{r_idx + 1}.txt"
                                    )
                                else:
                                    # 其他路径保持不变
                                    result_path = os.path.join(
                                        input_data["save_dir"],
                                        f"round_{r_idx + 1}",
                                        f"{path}.txt"
                                    )

                                print(f"尝试读取文件: {result_path}")
                                print(f"Attempting to read file: {result_path}")
                                if os.path.exists(result_path):
                                    prev_results.append(get_record_withReasoning(result_path))
                                else:
                                    print(f"警告: 文件不存在: {result_path}")
                                    print(f"Warning: File does not exist: {result_path}")

                            prompt = await build_prompt(
                                input_data,
                                layer_config["prompt_type"],
                                prev_results
                            )

                            result = await async_chat_claude(prompt, mergeLayer_LLMs_dict[m_type])

                            # 修正：先保存原始结果（带_primary）
                            # Fix: First save original result (with _primary)
                            result_key = f"{b_prefix}_{layer_name}_round_{r_idx + 1}"
                            primary_result_path = os.path.join(input_data["save_dir"], f"{result_key}_primary.txt")
                            with open(primary_result_path, "w", encoding="utf-8") as f:
                                f.write(result)
                                logging.info(f"保存原始金字塔层结果到: {primary_result_path}")
                                logging.info(f"Saved original pyramid layer result to: {primary_result_path}")

                            # 进行格式校验
                            # Perform format validation
                            is_valid = await check_pyramid_file_format(primary_result_path)
                            if is_valid:
                                # 校验通过后保存到正式文件（不带_primary）
                                # After validation, save to formal file (without _primary)
                                result_path = os.path.join(input_data["save_dir"], f"{result_key}.txt")
                                with open(result_path, "w", encoding="utf-8") as f:
                                    f.write(result)
                                    logging.info(f"保存校验后的金字塔层结果到: {result_path}")
                                    logging.info(f"Saved validated pyramid layer result to: {result_path}")
                            else:
                                logging.warning(f"警告: {primary_result_path} 的格式校验失败")
                                logging.warning(f"Warning: Format validation failed for {primary_result_path}")

                            # 修正：保存prompt到对应的文件
                            prompt_path = os.path.join(input_data["save_dir"], f"{result_key}_prompt.txt")
                            with open(prompt_path, "w", encoding="utf-8") as f:
                                f.write(prompt)

                            return result_key, result, result_path

                        # 添加任务到列表
                        task = process_round(round_idx, branch_idx, branch_prefix, previous_paths, model_type)
                        tasks.append(task)

                # 并行执行所有任务
                results = await asyncio.gather(*tasks)

                # 处理任务结果
                for result_key, result, result_path in results:
                    parallel_results[result_key] = result
                    if layer_name in layer_files_to_check:  # 添加检查
                        layer_files_to_check[layer_name].append(result_path)
                    else:
                        logging.warning(f"未找到层 {layer_name} 的文件检查列表")

                # 验证mergelayer1是否完成
                expected_mergelayer1_count = len(round_results) * len(
                    pyramid_framework["mergelayer1"]["previousSampling"])
                validate_layer_completion("mergelayer1", layer_files_to_check["mergelayer1"],
                                          expected_mergelayer1_count)

                expected_file_count = len(round_results) * len(layer_config["previousSampling"])

                # 在mergelayer2完成后添加验证
                validate_layer_completion("mergelayer2", layer_files_to_check["mergelayer2"], expected_file_count)

            elif layer_name == "mergelayer3":
                # 创建两个分支的任务
                tasks = []
                for branch_idx, previous_paths in enumerate(layer_config["previousSampling"]):
                    branch_prefix = "Multiple" if branch_idx == 0 else "Single"
                    model_type = layer_config["model_type"][branch_idx]

                    async def process_branch(b_prefix, prev_paths, m_type):
                        result_key = f"{b_prefix}_{layer_name}"
                        result_path = os.path.join(input_data["save_dir"], f"{result_key}.txt")
                        primary_result_path = os.path.join(input_data["save_dir"], f"{result_key}_primary.txt")
                        
                        if await check_existing_result(result_path, primary_result_path):
                            with open(result_path, 'r', encoding='utf-8') as f:
                                result = f.read()
                            return result_key, result, result_path
                        
                        previous_results = []
                        for round_idx in range(len(round_results)):
                            # 修正：从主目录读取mergelayer2的结果
                            prev_layer_key = f"{b_prefix}_mergelayer2_round_{round_idx + 1}"
                            result_path = os.path.join(input_data["save_dir"], f"{prev_layer_key}.txt")
                            if os.path.exists(result_path):
                                previous_results.append(get_record_withReasoning(result_path))
                            else:
                                print(f"警告: 文件不存在: {result_path}")

                        prompt = await build_prompt(
                            input_data,
                            layer_config["prompt_type"],
                            previous_results
                        )

                        result = await async_chat_claude(prompt, mergeLayer_LLMs_dict[m_type])

                        # 修正：先保存原始结果
                        result_key = f"{b_prefix}_{layer_name}"
                        primary_result_path = os.path.join(input_data["save_dir"], f"{result_key}_primary.txt")
                        with open(primary_result_path, "w", encoding="utf-8") as f:
                            f.write(result)
                            logging.info(f"保存原始金字塔层结果到: {primary_result_path}")

                        # 进行格式校验
                        is_valid = await check_pyramid_file_format(primary_result_path)
                        if is_valid:
                            # 校验通过后保存到正式文件
                            result_path = os.path.join(input_data["save_dir"], f"{result_key}.txt")
                            with open(result_path, "w", encoding="utf-8") as f:
                                f.write(result)
                            logging.info(f"保存校验后的金字塔层结果到: {result_path}")
                        else:
                            logging.warning(f"警告: {primary_result_path} 的格式校验失败")

                        result_key = f"{b_prefix}_{layer_name}"
                        result_path = os.path.join(input_data["save_dir"], f"{result_key}.txt")
                        prompt_path = os.path.join(input_data["save_dir"], f"{result_key}_prompt.txt")

                        with open(prompt_path, "w", encoding="utf-8") as f:
                            f.write(prompt)

                        return result_key, result, result_path

                    tasks.append(process_branch(branch_prefix, previous_paths, model_type))

                # 并行执行两个分支
                results = await asyncio.gather(*tasks)

                # 处理任务结果
                for result_key, result, result_path in results:
                    parallel_results[result_key] = result
                    if layer_name in layer_files_to_check:  # 添加检查
                        layer_files_to_check[layer_name].append(result_path)
                    else:
                        logging.warning(f"未找到层 {layer_name} 的文件检查列表")

                # 验证mergelayer2是否完成
                expected_mergelayer2_count = len(round_results) * len(
                    pyramid_framework["mergelayer2"]["previousSampling"])
                validate_layer_completion("mergelayer2", layer_files_to_check["mergelayer2"],
                                          expected_mergelayer2_count)

                expected_file_count = len(layer_config["previousSampling"])

                # 在mergelayer3完成后添加验证
                validate_layer_completion("mergelayer3", layer_files_to_check["mergelayer3"], expected_file_count)

            elif layer_name == "output":
                result_path = os.path.join(input_data["save_dir"], "final_output.txt")
                primary_result_path = os.path.join(input_data["save_dir"], "final_output_primary.txt")
                
                if await check_existing_result(result_path, primary_result_path):
                    with open(result_path, 'r', encoding='utf-8') as f:
                        final_result = f.read()
                else:
                    previous_results = []
                    for branch_prefix in ["Multiple", "Single"]:
                        result_path = os.path.join(input_data["save_dir"], f"{branch_prefix}_mergelayer3.txt")
                        if os.path.exists(result_path):
                            previous_results.append(get_record_withReasoning(result_path))
                        else:
                            print(f"警告: 文件不存在: {result_path}")

                    prompt = await build_prompt(
                        input_data,
                        layer_config["prompt_type"],
                        previous_results
                    )

                    final_result = await async_chat_claude(
                        prompt,
                        mergeLayer_LLMs_dict[layer_config["model_type"][0]]
                    )

                    result_path = os.path.join(input_data["save_dir"], "final_output.txt")
                    prompt_path = os.path.join(input_data["save_dir"], "final_output_prompt.txt")

                    # 修正：先保存原始结果（带_primary）
                    # Fix: First save original result (with _primary)
                    primary_result_path = os.path.join(input_data["save_dir"], "final_output_primary.txt")
                    with open(primary_result_path, "w", encoding="utf-8") as f:
                        f.write(final_result)
                        logging.info(f"保存原始最终结果到: {primary_result_path}")

                    # 进行格式校验
                    # Perform format validation
                    is_valid = await check_pyramid_file_format(primary_result_path)
                    if is_valid:
                        # 校验通过后保存到正式文件（不带_primary）
                        # After validation, save to formal file (without _primary)
                        result_path = os.path.join(input_data["save_dir"], "final_output.txt")
                        with open(result_path, "w", encoding="utf-8") as f:
                            f.write(final_result)
                            logging.info(f"保存校验后的最终结果到: {result_path}")
                    else:
                        logging.warning(f"警告: final_output_primary.txt 的格式校验失败")

                    layer_files_to_check["output"].append(result_path)

                    with open(prompt_path, "w", encoding="utf-8") as f:
                        f.write(prompt)

                parallel_results["final"] = final_result

                # 验证mergelayer3是否完成
                expected_mergelayer3_count = len(pyramid_framework["mergelayer3"]["previousSampling"])
                validate_layer_completion("mergelayer3", layer_files_to_check["mergelayer3"],
                                          expected_mergelayer3_count)

            all_results[layer_name] = parallel_results

        except Exception as e:
            logging.error(f"处理金字塔层 {layer_name} 时发生错误: {str(e)}")
            logging.error(f"Error processing pyramid layer {layer_name}: {str(e)}")
            raise  # 重新抛出异常，确保错误时停止执行

    return all_results