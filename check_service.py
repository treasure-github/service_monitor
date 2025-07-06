import requests, socket

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}
def check_service(service):
    try:
        print("正在检查接口："+service.name)
        method = service.method.upper() if service.method else 'GET'

        if service.check_type in ['http', 'https']:
            r = None
            if method == 'POST':
                r = requests.post(service.target,headers=headers, timeout=6)
            else:
                r = requests.get(service.target,headers=headers, timeout=6)

            if r.status_code == 200:
                if service.keyword and service.keyword not in r.text:
                    return False, "关键字不匹配"
                return True, "HTTP 正常"
            # print( r.text)
            return False, f"HTTP 状态码: {r.status_code}"
        elif service.check_type == 'tcp':
            ip, port = service.target.split(':')
            with socket.create_connection((ip, int(port)), timeout=10):
                return True, "TCP 正常"
        return False, "未知检查类型"
    except Exception as e:
        return False, str(e)
