# test_path.py
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent   # 如果 run.py 在根目录，就 parent 一次；如果在子目录就 parent.parent
# 调整为你的实际情况：如果 config.py 在 app/ 下，就用 parent.parent
# BASE_DIR = Path(__file__).resolve().parent.parent

print('脚本所在路径:', __file__)
print('当前工作目录 (os.getcwd()):', os.getcwd())
print('BASE_DIR 计算结果:', BASE_DIR)
print('预期数据库路径:', BASE_DIR / 'instance' / 'site.db')
print('文件是否存在:', (BASE_DIR / 'instance' / 'site.db').exists())
