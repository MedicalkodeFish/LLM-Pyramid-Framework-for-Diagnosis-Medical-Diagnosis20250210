import os
import logging
from typing import Dict, Any
from check_function import batch_formatCheck, verify_layer_completion
from parallel_query import process_parallel_requests
from model_structure import modules



async def process_module_layer(module_name: str, layer_name: str, input_data: Dict[str, Any],
                               previous_results: Dict[str, str] = None) -> Dict[str, str]:
    try:
        # print(f"\n开始处理模块 {module_name} 的 {layer_name} 层")
        # print(f"\nStart processing module {module_name} layer {layer_name}")
        results = await process_parallel_requests(module_name, layer_name, input_data, previous_results)

        # 收集需要检查格式的文件路径
        # Collect file paths that need format checking
        files_to_check = []
        save_dir = input_data.get("save_dir", "results")
        for llm_key in results.keys():
            if "inputLayer" in layer_name:
                result_file = os.path.join(save_dir, f"{module_name}_{layer_name}_{llm_key}.txt")
            else:
                result_file = os.path.join(save_dir, f"{module_name}_{layer_name}.txt")

            if os.path.exists(result_file):
                files_to_check.append(result_file)

        # 批量检查文件格式
        # Batch check file formats
        if files_to_check:
            format_results = await batch_formatCheck(files_to_check)
            for file_path, is_valid in format_results.items():
                if not is_valid:
                    print(f"警告: 文件格式检查失败: {file_path}")
                    print(f"Warning: File format check failed: {file_path}")

        return results
    except Exception as e:
        logging.error(f"层 {layer_name} 在模块 {module_name} 中执行失败: {str(e)}")
        return {}



async def run_module(module_name: str, input_data: Dict[str, Any]):
    """
    运行完整模块的所有层
    Run all layers of the complete module
    """
    module_config = modules[module_name]
    module_type = module_config["module_type"]
    all_results = {}

    # 确保保存目录存在
    # Ensure save directory exists
    save_dir = input_data.get("save_dir", "results")
    os.makedirs(save_dir, exist_ok=True)

    # 按照层次顺序处理，并添加同步等待
    # Process in layer order and add synchronous waiting
    for layer_name in module_type.keys():
        try:
            layer_results = await process_module_layer(
                module_name,
                layer_name,
                input_data,
                all_results
            )

            # 添加验证机制
            await verify_layer_completion(module_name, layer_name, save_dir, layer_results)

            # 将当前层结果添加到总结果中
            # Add current layer results to total results
            for key, value in layer_results.items():
                result_key = f"{module_name}_{layer_name}_{key}"
                all_results[result_key] = value

        except Exception as e:
            logging.error(f"处理层 {layer_name} 失败: {str(e)}")
            logging.error(f"Failed to process layer {layer_name}: {str(e)}")
            raise

    return all_results