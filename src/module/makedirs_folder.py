import os

# 要创建的文件夹路径

def mkdir_folder(folder_path):
    os.makedirs(folder_path, exist_ok=True)
