import os
import logging
from typing import Dict, Any, List
from prompt_config import prompt_record_repace_list


async def build_prompt(input_data: Dict[str, Any], prompt_type: str, previous_results: List[str]) -> str:
    logging.info(f"\n=== 开始构建 {prompt_type} 提示词 === \n=== Start building {prompt_type} prompt ===")

    prompt_path = os.path.join(input_data["prompt_path"], f"{prompt_type}.txt")
    print(f"prompt_path: {prompt_path}")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read()
            logging.info(f"成功读取提示词模板 | Successfully loaded prompt template: {prompt_path}")
    except Exception as e:
        logging.error(f"读取提示词模板失败 | Failed to read prompt template: {str(e)}")
        raise

    # 替换基础信息前记录原始长度 | Record original length before replacing basic information
    original_length = len(prompt)
    logging.info("开始替换基础信息... | Start replacing basic information...")

    # 替换基础信息并记录过程 | Replace basic information and record the process
    try:
        # 替换Primary Symptom | Replace Primary Symptom
        if "{$Primary Symptom$}" in prompt:
            prompt = prompt.replace("{$Primary Symptom$}", input_data["primary_content"])
            logging.info("成功替换 Primary Symptom | Successfully replaced Primary Symptom")
        else:
            logging.warning("未找到 Primary Symptom 占位符 | Primary Symptom placeholder not found")

        # 替换Presentation of Case | Replace Presentation of Case
        if "{$Presentation of Case$}" in prompt:
            prompt = prompt.replace("{$Presentation of Case$}", input_data["presentation_content"])
            logging.info("成功替换 Presentation of Case | Successfully replaced Presentation of Case")
        else:
            logging.warning("未找到 Presentation of Case 占位符 | Presentation of Case placeholder not found")

        # 替换question | Replace question
        if "{$question$}" in prompt:
            prompt = prompt.replace("{$question$}", input_data["question"])
            logging.info("成功替换 question | Successfully replaced question")
        else:
            logging.warning("未找到 question 占位符 | Question placeholder not found")

    except KeyError as e:
        logging.error(f"基础信息替换失败，缺少必要的键: {str(e)} | Failed to replace basic information, missing required key: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"基础信息替换过程中发生错误: {str(e)} | Error occurred during basic information replacement: {str(e)}")
        raise

    # 替换前轮结果 | Replace previous round results
    logging.info(f"\n开始替换前轮结果，共有 {len(previous_results)} 个结果待替换... \nStart replacing previous results, {len(previous_results)} results to be replaced...")

    for idx, prev_result in enumerate(previous_results):
        if idx < len(prompt_record_repace_list):
            placeholder = prompt_record_repace_list[idx]
            if placeholder in prompt:
                old_prompt = prompt
                prompt = prompt.replace(placeholder, prev_result)
                if old_prompt == prompt:
                    logging.warning(f"占位符 {placeholder} 替换可能失败，内容未发生变化 | Placeholder {placeholder} replacement may have failed, content unchanged")
                else:
                    logging.info(f"成功替换第 {idx + 1} 个结果的占位符 {placeholder} | Successfully replaced placeholder {placeholder} for result {idx + 1}")
            else:
                logging.warning(f"未找到第 {idx + 1} 个结果的占位符 {placeholder} | Placeholder {placeholder} not found for result {idx + 1}")
        else:
            logging.warning(f"结果数量 ({idx + 1}) 超过可用占位符数量 ({len(prompt_record_repace_list)}) | Number of results ({idx + 1}) exceeds available placeholders ({len(prompt_record_repace_list)})")

    # 检查最终提示词的变化 | Check final prompt changes
    final_length = len(prompt)
    logging.info(f"提示词构建完成 | Prompt construction completed:")
    logging.info(f"- 原始长度 | Original length: {original_length}")
    logging.info(f"- 最终长度 | Final length: {final_length}")
    logging.info(f"- 净增长 | Net growth: {final_length - original_length}")

    # 验证最终提示词不为空 | Verify the final prompt is not empty
    if not prompt.strip():
        logging.error("警告: 生成的提示词为空! | Warning: Generated prompt is empty!")
        raise ValueError("生成的提示词为空 | Generated prompt is empty")

    return prompt