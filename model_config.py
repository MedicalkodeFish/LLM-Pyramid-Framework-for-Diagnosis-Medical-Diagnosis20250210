backBone = "o3-mini" #"claude-3-5-sonnet" #"o1-mini"


#模块LLMs型号配置
#Module LLMs Model Configuration
multiple_LLMs_dict = {"LLM1": "gpt-4o",
                      "LLM2": "gemini-1.5-pro",
                      "LLM3": "claude-3-5-sonnet",#"claude-3-opus",
                      "LLM4": backBone}

single_LLMs_dict = {"LLM1": backBone,
                    "LLM2": backBone,
                    "LLM3": backBone,
                    "LLM4": backBone}

#融合层LLM型号配置
#Merge Layer LLM Model Configuration
mergeLayer_LLMs_dict = {"LLM4": backBone}


#模型型号映射
#Model Version Mapping
model_dict = {"o3-mini": "o3-mini-all",
              "gpt-4o": "gpt-4o-2024-11-20",
              "gemini-1.5-pro": "gemini-1.5-pro-latest",
              "gemini-2": "gemini-2.0-flash-thinking-exp",
              "gpt-3.5-turbo": "gpt-3.5-turbo",
              "claude-3-opus": "claude-3-opus-20240229",
              "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
              "o1-mini": "o1-mini-2024-09-12",
              "gpt-4o-mini": "gpt-4o-mini-2024-07-18"}

#API配置
#API Configuration
api_config = {
        "gpt-4o-mini": {
        "api_key": "",
        "url": "",
        "model_id": "gpt-4o-mini-2024-07-18"
    },
        "o3-mini": {
        "api_key": "",
        "url": "",
        "model_id": "o3-mini-all"
    },
        "deep-seek-v3": {
        "api_key": "",

        "url": "",
        "model_id": "deepseek-chat"
    },
        "deep-seek-r1": {
        "api_key": "",
        "url": "",
        "model_id": "deepseek-reasoner"
    },
    "claude-3-5-sonnet": {
        "api_key": "",
        "url": "",
        "model_id": "claude-3-5-sonnet-20241022"
    },
    "o1-mini": {
        "api_key": "",
        "url": "",
        "model_id": "o1-mini-2024-09-12"
    },
    "o1-preview": {
        "api_key": "",
        "url": "",
        "model_id": "o1-preview-2024-09-12"
    },
    "gpt-4o": {
        "api_key": "",
        "url": "",
        "model_id": "gpt-4o-mini-2024-07-18"
    },
    "gemini-1.5-pro": {
        "api_key": "",
        "url": "",
        "model_id": "gemini-1.5-pro-latest"
    },
    "gemini-2": {
        "api_key": "",
        "url": "",
        "model_id": "gemini-2.0-flash-thinking-exp"
    },
    "gpt-3.5-turbo": {
        "api_key": "",
        "url": "",
        "model_id": "gpt-3.5-turbo"
    },
    "claude-3-opus": {
        "api_key": "",
        "url": "",
        "model_id": "claude-3-opus-20240229"
    }
}




