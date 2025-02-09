from model_config import multiple_LLMs_dict, single_LLMs_dict

#模块的结构
#Module structure
AR_chain = {
    "inputLayer": {"layerNum": 1,
                   "parallel_num": 1,
                   "model_type": ["LLM1"],
                   "prompt_type": "AR",
                   "previousSampling": None
                   },
    "layer1": {"layerNum": 2,
               "parallel_num": 1,
               "model_type": ["LLM2"],
               "prompt_type": "AR",
               "previousSampling": [["AR_chain_inputLayer_LLM1"]]},
    "layer2": {"layerNum": 3,
               "parallel_num": 1,
               "model_type": ["LLM3"],
               "prompt_type": "AR_2",
               "previousSampling": [["AR_chain_inputLayer_LLM1", "AR_chain_layer1"]]},
    "layer3": {"layerNum": 4,
               "parallel_num": 1,
               "model_type": ["LLM4"],
               "previousSampling": [["AR_chain_inputLayer_LLM1", "AR_chain_layer1", "AR_chain_layer2"]],
               "prompt_type": "AR_3"}}

AR_tree = {
    "inputLayer": {
        "layerNum": 1,
        "parallel_num": 4,
        "model_type": ["LLM1", "LLM2", "LLM3", "LLM4"],
        "previousSampling": None,
        "prompt_type": "AR"
    },
    "layer1": {
        "layerNum": 2,
        "parallel_num": 1,
        "model_type": ["LLM4"],
        "previousSampling": [["AR_tree_inputLayer_LLM1", "AR_tree_inputLayer_LLM2"]],
        "prompt_type": "CoT_2"
    },
    "layer2": {
        "layerNum": 3,
        "parallel_num": 1,
        "model_type": ["LLM4"],
        "previousSampling": [["AR_tree_layer1", "AR_tree_inputLayer_LLM3"]],
        "prompt_type": "CoT_2"
    },
    "layer3": {
        "layerNum": 4,
        "parallel_num": 1,
        "model_type": ["LLM4"],
        "previousSampling": [["AR_tree_layer2", "AR_tree_layer1", "AR_tree_inputLayer_LLM4"]],
        "prompt_type": "CoT_3"
    }
}

CoT_tree = {
    "inputLayer": {"layerNum": 1,
                   "parallel_num": 4,
                   "model_type": ["LLM1", "LLM2", "LLM3", "LLM4"],
                   "previousSampling": None,
                   "prompt_type": "CoT"},
    "layer1": {"layerNum": 2,
               "parallel_num": 1,
               "model_type": ["LLM4"],
               "previousSampling": [["CoT_tree_inputLayer_LLM1", "CoT_tree_inputLayer_LLM2"]],
               "prompt_type": "CoT_2"},
    "layer2": {"layerNum": 3,
               "parallel_num": 1,
               "model_type": ["LLM4"],
               "previousSampling": [["CoT_tree_layer1", "CoT_tree_inputLayer_LLM3"]],
               "prompt_type": "CoT_2"},
    "layer3": {"layerNum": 4,
               "parallel_num": 1,
               "model_type": ["LLM4"],
               "previousSampling": [["CoT_tree_layer2", "CoT_tree_layer1", "CoT_tree_inputLayer_LLM4"]],
               "prompt_type": "CoT_3"}}




#具体的模块配置
#Specific module configurations
modules = {"Multiple_AR_chain": {"module_type": AR_chain,
                                 "LLMs_dict": multiple_LLMs_dict},
           "Single_AR_chain": {"module_type": AR_chain,
                               "LLMs_dict": single_LLMs_dict},
           "Multiple_AR_tree": {"module_type": AR_tree,
                                "LLMs_dict": multiple_LLMs_dict},
           "Single_AR_tree": {"module_type": AR_tree,
                              "LLMs_dict": single_LLMs_dict},
           "Multiple_CoT_tree": {"module_type": CoT_tree,
                                 "LLMs_dict": multiple_LLMs_dict},
           "Single_CoT_tree": {"module_type": CoT_tree,
                               "LLMs_dict": single_LLMs_dict}
           }



#金字塔框架结构配置
#Pyramid framework structure configuration
pyramid_framework = {
    "mergelayer1": {
        "layerNum": 1,
        "parallel_num": 6,
        "combine_rounds": False,
        "combine_multiple_single": False,
        "model_type": ["LLM4", "LLM4", "LLM4", "LLM4", "LLM4", "LLM4"],
        "previousSampling": [["Multiple_AR_chain_layer3", "Multiple_CoT_tree_layer3"],
                             ["Single_AR_chain_layer3", "Single_CoT_tree_layer3"]],
        "prompt_type": "CoT_2"
    },
    "mergelayer2": {
        "layerNum": 2,
        "parallel_num": 6,
        "combine_rounds": False,
        "combine_multiple_single": False,
        "model_type": ["LLM4", "LLM4", "LLM4", "LLM4", "LLM4", "LLM4"],
        "previousSampling": [["Multiple_mergelayer1", "Multiple_AR_tree_layer3"],
                             ["Single_mergelayer1", "Single_AR_tree_layer3"]],
        "prompt_type": "CoT_2"
    },
    "mergelayer3": {
        "layerNum": 3,
        "parallel_num": 2,
        "combine_rounds": True,
        "combine_multiple_single": False,
        "model_type": ["LLM4", "LLM4"],
        "previousSampling": [["Multiple_mergelayer2"],
                             ["Single_mergelayer2"]],
        "prompt_type": "CoT_3"
    },
    "output": {
        "layerNum": 4,
        "parallel_num": 1,
        "combine_rounds": False,
        "combine_multiple_single": True,
        "model_type": ["LLM4"],
        "previousSampling": [["Multiple_mergelayer3"],
                             ["Single_mergelayer3"]],
        "prompt_type": "CoT_2"
    }
}

