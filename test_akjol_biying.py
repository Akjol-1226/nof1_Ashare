import requests

# 替换为你自己的 licence
YOUR_LICENCE = "99E9AF7B-830F-4D58-AAD1-5A825554325B"
STOCK_CODE = "000001"  # 示例股票代码

# 构造 URL
# url = f"https://api.biyingapi.com/hsstock/real/time/{STOCK_CODE}/{YOUR_LICENCE}"
# url = f"https://api.biyingapi.com/hsstock/real/five/{STOCK_CODE}/{YOUR_LICENCE}" # 五档交易接口
url = f"http://api.biyingapi.com/hsrl/ssjy_more/{YOUR_LICENCE}?stock_codes=000001,600019"
# 发送 GET 请求
response = requests.get(url)

# 检查响应状态
if response.status_code == 200:
    data = response.json()  # 假设返回的是 JSON 格式
    print("请求成功，返回数据：")
    print(data)
else:
    print(f"请求失败，状态码：{response.status_code}")
    print("响应内容：", response.text)
    
    
# 实时交易数据
# API接口：https://api.biyingapi.com/hsstock/real/time/股票代码/证书您的licence
# 接口说明：根据《股票列表》得到的股票代码获取实时交易数据（您可以理解为日线的最新数据），该接口为券商数据源。
# 数据更新：实时
# 请求频率：1分钟300次 | 包年版1分钟3千次 | 白金版1分钟6千次
# 返回格式：标准Json格式      [{},...{}]
# 字段名称	数据类型	字段说明
# p	number	最新价
# o	number	开盘价
# h	number	最高价
# l	number	最低价
# yc	number	前收盘价
# cje	number	成交总额
# v	number	成交总量
# pv	number	原始成交总量
# t	string	更新时间
# ud	float	涨跌额
# pc	float	涨跌幅
# zf	float	振幅
# t	string	更新时间
# pe	number	市盈率
# tr	number	换手率
# pb_ratio	number	市净率
# tv	number	成交量

# 买卖五档盘口
# API接口：https://api.biyingapi.com/hsstock/real/five/股票代码/证书您的licence
# 接口说明：根据《股票列表》得到的股票代码获取实时买卖五档盘口数据。
# 数据更新：实时
# 请求频率：1分钟300次 | 包年版1分钟3千次 | 白金版1分钟6千次
# 返回格式：标准Json格式      [{},...{}]
# 字段名称	数据类型	字段说明
# ps	number	委卖价
# pb	number	委买价
# vs	number	委卖量
# vb	number	委买量
# t	string	更新时间

# 实时交易数据（多股）
# API接口：http://api.biyingapi.com/hsrl/ssjy_more/您的licence?stock_codes=股票代码1,股票代码2……股票代码20
# 接口说明：一次性获取《股票列表》中不超过20支股票的实时交易数据（您可以理解为日线的最新数据）
# 数据更新：实时
# 请求频率：1分钟300次 | 包年版1分钟3千次 | 白金版1分钟6千次
# 返回格式：标准Json格式      [{},...{}]
# 字段名称	数据类型	字段说明
# p	number	最新价
# o	number	开盘价
# h	number	最高价
# l	number	最低价
# yc	number	前收盘价
# cje	number	成交总额
# v	number	成交总量
# pv	number	原始成交总量
# t	string	更新时间
# ud	float	涨跌额
# pc	float	涨跌幅
# zf	float	振幅
# t	string	更新时间
# pe	number	市盈率
# tr	number	换手率
# pb_ratio	number	市净率
# tv	number	成交量
# dm	string	股票代码


