from datetime import datetime
import pytz
# 全局定义东八区时区对象
BJ_TZ = pytz.timezone('Asia/Shanghai')

def get_bj_now():
    """返回当前东八区带时区信息的时间"""
    utc_now = datetime.utcnow()
    return utc_now.replace(tzinfo=pytz.utc).astimezone(BJ_TZ)