import pandas as pd


excel_path = r"dataset\question\query_question.xlsx"
excel = pd.read_excel(excel_path)
question_list = list(excel["question"])
json_name_list = list(excel["File Name"])

