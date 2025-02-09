import os
import re
import json
from prompt_config import pattern1, pattern2, pattern3, pattern4
from chat2llm import chat_claude


def get_record_withReasoning(txt_path):
    # 开始处理文件 / Start processing file
    print(f"开始处理文件: {txt_path}")
    print(f"Processing file: {txt_path}")
    with open(txt_path, "r", encoding="utf-8") as f:
        txt_record = f.read().replace("Other Potential differential diagnoses",
                                      "Potential Differential Diagnoses").replace(
            "Most Likely Diagnosis", "Most Likely Main Diagnosis").replace(
            "$$", "$").replace("$$$", "$").replace("<${", "<$[{").replace("}$>", "}]$>").replace(
            '."},', '."}},').replace('Other Potential differential diagnoses',
                                     'Potential differential diagnoses').replace("\n", "").replace("$<$", "<$")

        print(f"处理后的原始记录: {txt_record[:200]}...")
        print(f"Processed raw record: {txt_record[:200]}...")

        # 首先尝试直接解析为字典 / First attempt to parse directly as dictionary
        try:
            dict_result = json.loads(txt_record)
            print("成功直接解析为JSON格式")
            print("Successfully parsed as JSON format")
            return json.dumps(dict_result)
        except json.JSONDecodeError:
            print("直接JSON解析失败，尝试其他方式")
            print("Direct JSON parsing failed, trying other methods")

        # 尝试使用正则表达式提取
        for pattern in [pattern1, pattern2, pattern3, pattern4]:
            try:
                match = re.search(pattern, txt_record, re.DOTALL)
                if match:
                    extracted_content = match.group(1)
                    try:
                        dict_result = eval(extracted_content)
                        print(f"使用正则表达式 {pattern} 成功提取并解析")

                        return str(dict_result)
                    except:
                        continue
            except:
                continue

        # 如果所有常规方法都失败，使用LLM进行格式修正
        # If all conventional methods fail, use LLM for format correction
        print("常规解析方法都失败，尝试使用LLM修正格式")
        print("Conventional parsing methods failed, attempting format correction with LLM")

        # 读取格式校正prompt模板 / Read format correction prompt template
        correction_prompt_path = os.path.join("H:\\LLM2\\dataset\\query\\nejm\\Final\\demo\\prompt",
                                              "formatChecker.txt")
        with open(correction_prompt_path, "r", encoding="utf-8") as f:
            correction_prompt_template = f.read()

        # 替换模板中的占位符
        correction_prompt = correction_prompt_template.replace("{%primary_record%}", txt_record)

        try:
            # 调用Claude进行格式校正，直接使用返回的结果
            corrected_result = chat_claude(correction_prompt, txt_path, txt_path + ".log")

            # 增强的结果提取逻辑
            def extract_json_content(text):
                # 1. 尝试直接解析整个文本
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    pass

                # 2. 尝试提取JSON代码块或特定格式
                patterns = [
                    pattern1,
                    pattern2,
                    pattern3,
                    pattern4
                ]

                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.DOTALL)
                    for match in matches:
                        try:
                            content = match.group(1).strip()
                            return json.loads(content)
                        except (json.JSONDecodeError, IndexError):
                            continue

                return None

            # 使用增强的提取逻辑处理校正后的结果
            extracted_result = extract_json_content(corrected_result)
            if extracted_result:
                print("成功从LLM响应中提取并解析JSON")
                return json.dumps(extracted_result)
            else:
                print("无法从LLM响应中提取有效JSON")
                return "{}"

        except Exception as e:
            print(f"LLM格式校正失败: {str(e)}")
            print(f"LLM format correction failed: {str(e)}")
            return "{}"


def get_record(txt_path):
    # 开始处理文件 / Start processing file
    print(f"开始处理文件: {txt_path}")
    print(f"Starting to process file: {txt_path}")
    with open(txt_path, "r", encoding="utf-8") as f:
        txt_record = f.read().replace("Other Potential differential diagnoses",
                                      "Potential Differential Diagnoses").replace(
            "Most Likely Diagnosis", "Most Likely Main Diagnosis").replace(
            "$$", "$").replace("$$$", "$").replace("<${", "<$[{").replace("}$>", "}]$>").replace(
            '."},', '."}},').replace('Other Potential differential diagnoses',
                                     'Potential differential diagnoses').replace("\n\n", "\n").replace("$<$", "<$")

        print(f"处理后的原始记录: {txt_record[:200]}...")
        print(f"Processed raw record: {txt_record[:200]}...")

        dict_result = None
        # 首先尝试直接解析为字典 / First attempt to parse directly as dictionary
        try:
            dict_result = json.loads(txt_record)
            print("成功直接解析为JSON格式")
            print("Successfully parsed as JSON format")
        except json.JSONDecodeError:
            print("直接JSON解析失败，尝试其他方式")
            print("Direct JSON parsing failed, trying other methods")
            # 尝试使用正则表达式提取
            for pattern in [pattern1, pattern2, pattern3, pattern4]:
                try:
                    match = re.search(pattern, txt_record, re.DOTALL)
                    if match:
                        extracted_content = match.group(1)
                        try:
                            dict_result = eval(extracted_content)
                            print(f"使用正则表达式 {pattern} 成功提取并解析")
                            break
                        except:
                            continue
                except:
                    continue

        if dict_result is None:
            # 如果所有常规方法都失败，使用LLM进行格式修正
            # If all conventional methods fail, use LLM for format correction
            print("常规解析方法都失败，尝试使用LLM修正格式")
            print("Conventional parsing methods failed, attempting format correction with LLM")
            correction_prompt_path = os.path.join("H:\\LLM2\\dataset\\query\\nejm\\Final\\demo\\prompt",
                                                  "formatChecker.txt")
            with open(correction_prompt_path, "r", encoding="utf-8") as f:
                correction_prompt_template = f.read()
            correction_prompt = correction_prompt_template.replace("{%primary_record%}", txt_record)

            try:
                corrected_result = chat_claude(correction_prompt, txt_path, txt_path + ".log")
                # 将校正过的结果进行记录
                out_txt_path = txt_path.replace("_primary.txt", ".txt")
                with open(out_txt_path, "w", encoding="utf-8") as f:
                    f.write(corrected_result)

                # 增强的JSON提取逻辑
                def extract_json_with_fallback(text):
                    # 1. 尝试直接解析
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        pass

                    # 2. 尝试提取并解析JSON代码块
                    json_patterns = [
                        pattern1,
                        pattern2,
                        pattern3,
                        pattern4
                    ]

                    for pattern in json_patterns:
                        matches = re.finditer(pattern, text, re.DOTALL)
                        for match in matches:
                            try:
                                content = match.group(1).strip()
                                return json.loads(content)
                            except (json.JSONDecodeError, IndexError):
                                continue

                    # 3. 尝试提取最外层的花括号或方括号内容
                    try:
                        brace_pattern = r'{[^{}]*(?:{[^{}]*}[^{}]*)*}'
                        bracket_pattern = r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]'

                        for pattern in [brace_pattern, bracket_pattern]:
                            match = re.search(pattern, text)
                            if match:
                                return json.loads(match.group(0))
                    except (json.JSONDecodeError, AttributeError):
                        pass

                    return None

                # 直接使用校正后的结果进行解析，而不是重新读取文件
                dict_result = extract_json_with_fallback(corrected_result)
                if not dict_result:
                    return "Error: Unable to extract valid information"

            except Exception as e:
                print(f"LLM格式校正失败: {str(e)}")
                print(f"LLM format correction failed: {str(e)}")
                return "Error: Format correction failed"

        # 提取所需信息
        try:
            # 处理列表形式的记录
            if isinstance(dict_result, list):
                try:
                    potential_diagnoses = list(dict_result[0]['Potential differential diagnoses'].keys())
                except KeyError:
                    try:
                        potential_diagnoses = list(dict_result[0]['Potential Differential Diagnoses'].keys())
                    except KeyError:
                        potential_diagnoses = []

                try:
                    mostlikely_diag = dict_result[1]['Most Likely Main Diagnosis']
                except (KeyError, IndexError):
                    try:
                        mostlikely_diag = dict_result[1]['Most Likely Main Diagnoses']
                    except (KeyError, IndexError):
                        try:
                            mostlikely_diag = dict_result[0]['Most Likely Main Diagnosis']
                        except KeyError:
                            mostlikely_diag = "Not found"

            # 处理字典形式的记录
            else:
                try:
                    potential_diagnoses = list(dict_result["Potential differential diagnoses"].keys())
                except KeyError:
                    try:
                        potential_diagnoses = list(dict_result["Potential Differential Diagnoses"].keys())
                    except KeyError:
                        potential_diagnoses = []

                try:
                    mostlikely_diag = dict_result["Most Likely Main Diagnosis"]
                except KeyError:
                    try:
                        mostlikely_diag = dict_result["Most Likely Main Diagnoses"]
                    except KeyError:
                        mostlikely_diag = "Not found"

            # 处理嵌套的最可能诊断
            if not isinstance(mostlikely_diag, str):
                mostlikely_diag_new = []
                if isinstance(mostlikely_diag, list):
                    for item in mostlikely_diag:
                        if isinstance(item, dict):
                            for key, value in item.items():
                                if "iagnos" in key:
                                    mostlikely_diag_new.append(value)
                mostlikely_diag = "\n".join(mostlikely_diag_new) if mostlikely_diag_new else "Not found"

            # 格式化输出
            return f"Potential diagnoses: {potential_diagnoses}, Most likely diagnoses: {mostlikely_diag}"

        except Exception as e:
            print(f"提取信息时发生错误: {str(e)}")
            print(f"Error occurred while extracting information: {str(e)}")
            return "Error: Information extraction failed"