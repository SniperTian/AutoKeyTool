# config.py
import json
import os

class ConfigManager:
    @staticmethod
    def save_config(filepath, data):
        """
        保存配置到 JSON 文件
        :param filepath: 保存路径
        :param data: 字典格式的配置数据
        :return: (bool, str) -> (是否成功, 提示信息)
        """
        try:
            # ensure_ascii=False 保证中文字符不乱码
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True, "保存成功"
        except Exception as e:
            return False, f"保存失败: {str(e)}"

    @staticmethod
    def load_config(filepath):
        """
        加载 JSON 配置
        :return: (data, str) -> (配置字典或None, 提示信息)
        """
        if not os.path.exists(filepath):
            return None, "文件不存在"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data, "加载成功"
        except Exception as e:
            return None, f"配置文件格式错误: {str(e)}"