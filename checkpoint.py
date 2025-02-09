import os
import json
import time
import logging
from typing import Tuple
from model_config import backBone
# 添加断点记录相关的常量和函数
CHECKPOINT_FILE = "results\\%s\\checkpoint.json" % backBone


def save_checkpoint(json_name: str, round_index: int = None, layer_name: str = None):
    """保存更详细的断点信息，使用完整的文件名（包含.json扩展名）
    Save detailed checkpoint information using complete filename (including .json extension)
    """
    try:
        # 确保保存完整的文件名（包含.json）
        # Ensure saving complete filename (including .json)
        checkpoint_data = {
            "last_completed_file": json_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "round_index": round_index,
            "layer_name": layer_name
        }
        os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(checkpoint_data, f, indent=2)
        logging.info(f"保存断点: 完成处理病例 {json_name}, 轮次 {round_index}, 层 {layer_name}")
        logging.info(f"Checkpoint saved: Completed case {json_name}, round {round_index}, layer {layer_name}")
    except Exception as e:
        logging.error(f"保存断点时出错: {str(e)}")
        logging.error(f"Error saving checkpoint: {str(e)}")


def load_checkpoint() -> Tuple[str, int, str]:
    """加载更详细的断点信息，返回最后处理的文件名而不是索引
    Load detailed checkpoint information, returns the last processed filename instead of index
    """
    try:
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, "r") as f:
                checkpoint = json.load(f)
                last_file = checkpoint.get("last_completed_file", "")
                last_round = checkpoint.get("round_index")
                last_layer = checkpoint.get("layer_name")
                logging.info(f"加载断点: 上次处理到病例 {last_file}, 轮次 {last_round}, 层 {last_layer}")
                logging.info(f"Checkpoint loaded: Last processed case {last_file}, round {last_round}, layer {last_layer}")
                return last_file, last_round, last_layer
        return "", None, None
    except Exception as e:
        logging.error(f"加载断点时出错: {str(e)}")
        logging.error(f"Error loading checkpoint: {str(e)}")
        return "", None, None
