import json
import os

class ConfigManager:
    @staticmethod
    def save_config(filepath, data):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True, "保存成功"
        except Exception as e:
            return False, f"保存失败: {str(e)}"

    @staticmethod
    def load_config(filepath):
        if not os.path.exists(filepath):
            return None, "文件不存在"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data, "加载成功"
        except Exception as e:
            return None, f"配置文件格式错误: {str(e)}"