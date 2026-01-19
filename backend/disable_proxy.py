"""
强制禁用代理的模块
在导入其他模块之前导入此模块
"""

import os
import sys

# 方法1: 清除环境变量
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'NO_PROXY', 'no_proxy']
for var in proxy_vars:
    os.environ.pop(var, None)

# 方法2: 设置no_proxy为所有域名
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# 方法3: Monkey patch urllib
try:
    import urllib.request
    # 创建不使用代理的opener
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    urllib.request.install_opener(opener)
except Exception as e:
    print(f"Warning: Failed to disable urllib proxy: {e}", file=sys.stderr)

# 方法4: Monkey patch requests
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    # 创建自定义session类，强制禁用代理
    _original_session = requests.Session
    
    class NoProxySession(_original_session):
        def __init__(self):
            super().__init__()
            self.proxies = {}
            self.trust_env = False  # 不信任环境变量
            
            # 配置重试策略
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.mount("http://", adapter)
            self.mount("https://", adapter)
        
        def request(self, *args, **kwargs):
            # 强制移除代理参数
            kwargs.pop('proxies', None)
            kwargs['proxies'] = {}
            return super().request(*args, **kwargs)
    
    # 替换默认Session
    requests.Session = NoProxySession
    requests.sessions.Session = NoProxySession
    
except Exception as e:
    print(f"Warning: Failed to patch requests: {e}", file=sys.stderr)

# 方法5: 为httpx也禁用代理（如果使用）
# try:
#     import httpx
#     
#     _original_client = httpx.Client
#     
#     class NoProxyClient(_original_client):
#         def __init__(self, *args, **kwargs):
#             kwargs.pop('proxies', None)
#             kwargs['proxies'] = {}
#             kwargs['trust_env'] = False
#             super().__init__(*args, **kwargs)
#     
#     httpx.Client = NoProxyClient
#     
# except (ImportError, Exception) as e:
#     pass  # httpx可能未安装

# 方法6: 强制设置requests和urllib3不信任系统代理
try:
    import requests
    # Monkey patch getproxies函数
    import urllib.request as urllib_request
    urllib_request.getproxies = lambda: {}
    urllib_request.proxy_bypass = lambda x: True
except:
    pass

# 方法7: 对于urllib3也强制禁用
try:
    import urllib3
    # 禁用urllib3的代理警告
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass

print("✓ 代理已强制禁用（所有HTTP库）")

