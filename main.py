import asyncio
import os
import time
import json
import logging
from checkpoint import load_checkpoint, save_checkpoint
from logger import setup_logger
from framework import run_pyramid_framework
from modules import run_module
from check_function import validate_pyramid_config
from load_question import question_list, json_name_list
from model_config import backBone
from model_structure import pyramid_framework
from checkpoint import CHECKPOINT_FILE

async def main():

    logging.info(f"开始处理总共 {len(json_name_list)} 个病例")  # Start processing total cases
    logging.info(f"Start processing {len(json_name_list)} cases in total")

    # 加载断点 (Load checkpoint)
    last_completed_file, last_round, last_layer = load_checkpoint()

    # 根据完整文件名（包含.json）确定起始索引
    # Determine start index based on complete filename (including .json)
    if last_completed_file:
        try:
            start_index = json_name_list.index(last_completed_file) + 1
        except ValueError:
            start_index = 0
            logging.warning(f"未找到上次处理的文件 {last_completed_file}，从头开始处理")  # Previous file not found, starting from beginning
            logging.warning(f"Previous file {last_completed_file} not found, starting from beginning")
    else:
        start_index = 0

    logging.info(f"从病例 {json_name_list[start_index] if start_index < len(json_name_list) else '结束'} 开始处理")  # Starting from case or end
    logging.info(f"Starting from case {json_name_list[start_index] if start_index < len(json_name_list) else 'end'}")

    for json_num in range(start_index, len(json_name_list)):
        # 为每个病例设置独立的日志记录器
        logger = setup_logger(json_num)
        case_start_time = time.time()

        try:
            logger.info(f"\n{'=' * 50}")
            logger.info(f"开始处理第 {json_num + 1}/{len(json_name_list)} 个病例")
            logger.info(f"Processing case {json_num + 1}/{len(json_name_list)}")
            json_name = json_name_list[json_num]
            question = question_list[json_num]

            logger.info(f"病例文件: {json_name}")
            logger.info(f"Case file: {json_name}")
            logger.info(f"问题: {question}")
            logger.info(f"Question: {question}")
            logger.info(f"{'=' * 50}")

            # 创建该病例的保存目录 (Create save directory for this case)
            case_dir = os.path.join(
                f"results\\{backBone}",
                str(json_name).split(".json")[0]
            )
            os.makedirs(case_dir, exist_ok=True)

            # 创建三轮的目录 (Create directories for three rounds)
            round_dirs = []
            for round_num in range(3):
                round_dir = os.path.join(case_dir, f"round_{round_num + 1}")
                os.makedirs(round_dir, exist_ok=True)
                round_dirs.append(round_dir)

            # 基础输入数据 (Base input data)
            base_input_data = {
                "path_query": os.path.join(
                    "dataset\\dataset_nejm_filtered",
                    json_name
                ),
                "question": question,
                "prompt_path": "prompt",
            }

            # 记录模块执行开始时间 (Record module execution start time)
            modules_start_time = time.time()

            # 创建所有轮次的所有任务 (Create tasks for all rounds)
            all_round_tasks = []
            for round_dir in round_dirs:
                round_input_data = base_input_data.copy()
                round_input_data["save_dir"] = round_dir

                round_tasks = []
                for module_name in [
                    "Multiple_AR_chain",
                    "Single_AR_chain",
                    "Multiple_AR_tree",
                    "Single_AR_tree",
                    "Multiple_CoT_tree",
                    "Single_CoT_tree"
                ]:
                    task = run_module(module_name, round_input_data)
                    round_tasks.append(task)

                all_round_tasks.append(asyncio.gather(*round_tasks))

            # 并行执行所有轮次
            try:
                round_results = await asyncio.gather(*all_round_tasks)
                modules_end_time = time.time()
                modules_duration = modules_end_time - modules_start_time
                logger.info(f"\n模块执行总时间: {modules_duration:.2f} 秒 ({modules_duration / 60:.2f} 分钟)")  # Total module execution time in seconds and minutes
                logger.info(f"\nTotal module execution time: {modules_duration:.2f} seconds ({modules_duration / 60:.2f} minutes)")

                # 记录金字塔框架开始时间 (Record pyramid framework start time)
                pyramid_start_time = time.time()

                # 读取病例内容 (Read case content)
                with open(base_input_data["path_query"], "r", encoding="utf-8") as f:
                    dict_content = json.load(f)
                    primary_content = dict_content["Primary Symptom"]
                    presentation_content = dict_content["Presentation of Case"]

                # 准备金字塔框架的输入 (Prepare pyramid framework input)
                pyramid_input = {
                    **base_input_data,
                    "save_dir": case_dir,
                    "primary_content": primary_content,
                    "presentation_content": presentation_content
                }

                # 将轮次结果转换为金字塔框架所需的格式 (Convert round results to pyramid framework format)
                formatted_round_results = [
                    {
                        "dir": round_dirs[i],
                        "results": round_results[i]
                    }
                    for i in range(len(round_results))
                ]

                # 运行金字塔框架 (Run pyramid framework)
                pyramid_results = await run_pyramid_framework(pyramid_input, formatted_round_results)

                # 记录金字塔框架执行时间
                pyramid_end_time = time.time()
                pyramid_duration = pyramid_end_time - pyramid_start_time
                logger.info(f"\n金字塔框架执行总时间: {pyramid_duration:.2f} 秒 ({pyramid_duration / 60:.2f} 分钟)")
                logger.info(f"\nTotal pyramid framework execution time: {pyramid_duration:.2f} seconds ({pyramid_duration / 60:.2f} minutes)")

                # 记录病例总执行时间
                # Record total case execution time
                case_end_time = time.time()
                case_duration = case_end_time - case_start_time
                logger.info(f"\n病例总执行时间: {case_duration:.2f} 秒 ({case_duration / 60:.2f} 分钟)")
                logger.info(f"\nTotal case execution time: {case_duration:.2f} seconds ({case_duration / 60:.2f} minutes)")
                logger.info(f"最终结果保存在: {os.path.join(case_dir, 'final_output.txt')}")
                logger.info(f"Final results saved at: {os.path.join(case_dir, 'final_output.txt')}")

            except Exception as e:
                logger.error(f"并行执行轮次时出错: {str(e)}")
                logger.error(f"Error during parallel round execution: {str(e)}")
                continue

            # 在每个关键步骤后保存更详细的断点信息（使用完整文件名）
            # Save detailed checkpoint information after each key step (using complete filename)
            for round_idx, round_dir in enumerate(round_dirs):
                save_checkpoint(json_name, round_idx, "round_complete")

            # 金字塔框架处理 (Pyramid framework processing)
            for layer_name in pyramid_framework.keys():
                save_checkpoint(json_name, None, layer_name)

            # 完成整个病例处理后的断点保存（使用完整文件名）
            # Save checkpoint after completing the entire case (using complete filename)
            save_checkpoint(json_name)
            # time.sleep(5)

        except Exception as e:
            logger.error(f"处理病例 {json_name} 时发生错误: {str(e)}")
            logger.error(f"Error processing case {json_name}: {str(e)}")
            # 保存出错时的断点，使用完整文件名
            save_checkpoint(json_name_list[max(0, json_num - 1)])
            continue

        await asyncio.sleep(6)  # 在处理下一个病例前短暂暂停

    # 处理完所有病例后删除断点文件 (Delete checkpoint file after processing all cases)
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logging.info("所有病例处理完成，删除断点文件")  # All cases processed, checkpoint file deleted
        logging.info("All cases processed, checkpoint file deleted")

    logging.info("\n所有病例处理完成!")  # All cases processing completed!
    logging.info("\nAll cases processing completed!")


# 在运行前验证配置
if not validate_pyramid_config(pyramid_framework):
    raise ValueError("金字塔框架配置无效")

if __name__ == "__main__":
    try:
        start_time = time.time()  # 记录总处理开始时间
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        end_time = time.time()
        total_duration = end_time - start_time
        logging.info(f"程序总运行时间: {total_duration:.2f} 秒 ({total_duration / 60:.2f} 分钟)")  # Total program runtime in seconds and minutes
        logging.info(f"Total program runtime: {total_duration:.2f} seconds ({total_duration / 60:.2f} minutes)")
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}")  # Program execution error
        logging.error(f"Program execution error: {str(e)}")
    finally:
        try:
            loop = asyncio.get_event_loop()
            tasks = asyncio.all_tasks(loop)
            for task in tasks:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            loop.close()
        except Exception as e:
            logging.error(f"清理任务时出错: {str(e)}")  # Error during task cleanup
            logging.error(f"Error during task cleanup: {str(e)}")