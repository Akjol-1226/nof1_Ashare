#!/usr/bin/env python3
"""
修复代理问题的测试脚本
尝试禁用代理后访问AKShare
"""

import os
import akshare as ak
from datetime import datetime

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def check_proxy_settings():
    """检查当前代理设置"""
    print_section("检查代理设置")
    
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY']
    
    found_proxy = False
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"发现代理设置: {var} = {value}")
            found_proxy = True
    
    if not found_proxy:
        print("✅ 未发现环境变量中的代理设置")
    else:
        print("\n⚠️  发现代理设置，这可能导致连接问题")
    
    return found_proxy

def test_with_proxy_disabled():
    """禁用代理后测试"""
    print_section("测试1: 禁用代理后访问")
    
    # 临时清除代理设置
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY']
    old_values = {}
    
    for var in proxy_vars:
        if var in os.environ:
            old_values[var] = os.environ[var]
            del os.environ[var]
    
    print("已临时禁用代理...")
    
    try:
        print("\n尝试获取实时行情...")
        df = ak.stock_zh_a_spot_em()
        
        print(f"✅ 成功！获取了 {len(df)} 只股票的数据")
        
        # 检查我们的6只股票
        target_codes = ['000063', '300750', '600703', '002594', '688256', '600276']
        target_names = ['中兴通讯', '宁德时代', '三安光电', '比亚迪', '寒武纪', '恒瑞医药']
        
        print(f"\n检查6只目标股票:")
        for code, name in zip(target_codes, target_names):
            stock = df[df['代码'] == code]
            if not stock.empty:
                s = stock.iloc[0]
                print(f"  ✓ {code} {name}: ¥{s['最新价']:.2f} ({s['涨跌幅']:+.2f}%)")
            else:
                print(f"  ✗ {code} {name}: 未找到")
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        return False
        
    finally:
        # 恢复代理设置
        for var, value in old_values.items():
            os.environ[var] = value

def test_with_requests_session():
    """使用requests session禁用代理"""
    print_section("测试2: 使用no_proxy配置")
    
    # 设置no_proxy
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    
    try:
        print("尝试获取历史数据（更稳定）...")
        df = ak.stock_zh_a_hist(
            symbol="000063",
            period="daily",
            start_date="20241101",
            end_date="20241112",
            adjust="qfq"
        )
        
        print(f"✅ 成功！获取了 {len(df)} 天的历史数据")
        print("\n最近3日数据:")
        print(df.tail(3))
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        return False

def generate_fix_script():
    """生成修复脚本"""
    print_section("生成修复脚本")
    
    fix_sh = """#!/bin/bash
# 临时禁用代理并启动后端

echo "禁用代理设置..."
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy
unset ALL_PROXY

echo "启动后端服务..."
cd backend
python3 main.py
"""
    
    with open('start_no_proxy.sh', 'w') as f:
        f.write(fix_sh)
    
    os.chmod('start_no_proxy.sh', 0o755)
    
    print("✅ 已生成修复脚本: start_no_proxy.sh")
    print("\n使用方法:")
    print("  ./start_no_proxy.sh")
    
    # 生成Python配置
    config_py = """# 在backend/main.py的开头添加这些代码来禁用代理

import os

# 禁用代理
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('ALL_PROXY', None)
"""
    
    with open('no_proxy_config.txt', 'w') as f:
        f.write(config_py)
    
    print("✅ 已生成配置说明: no_proxy_config.txt")

def main():
    print(f"\n{'#'*80}")
    print(f"#  代理问题诊断和修复")
    print(f"#  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")
    
    # 1. 检查代理
    has_proxy = check_proxy_settings()
    
    # 2. 测试禁用代理
    test1_ok = test_with_proxy_disabled()
    
    # 3. 测试历史数据
    test2_ok = test_with_requests_session()
    
    # 4. 生成修复脚本
    generate_fix_script()
    
    # 总结
    print_section("诊断总结")
    
    if has_proxy:
        print("🔍 问题原因:")
        print("   系统配置了HTTP/HTTPS代理，但代理服务不可用")
        print("   导致AKShare无法访问东方财富网API\n")
    
    print("💡 解决方案:")
    print("\n【方案1】临时禁用代理（推荐）")
    print("  运行生成的脚本:")
    print("    ./start_no_proxy.sh")
    
    print("\n【方案2】永久禁用代理")
    print("  编辑 ~/.zshrc 或 ~/.bash_profile，添加:")
    print("    unset HTTP_PROXY")
    print("    unset HTTPS_PROXY")
    print("    unset http_proxy")
    print("    unset https_proxy")
    
    print("\n【方案3】使用历史数据接口")
    if test2_ok:
        print("  ✅ 历史数据接口工作正常！")
        print("  可以用历史数据进行开发和测试")
    
    print("\n【方案4】检查系统代理设置")
    print("  macOS: 系统偏好设置 > 网络 > 高级 > 代理")
    print("  检查是否配置了不需要的代理")
    
    print("\n" + "="*80 + "\n")
    
    if test1_ok:
        print("✅ 好消息：禁用代理后接口可以正常工作！")
        print("   使用上述方案1或方案2即可解决问题。")
    elif test2_ok:
        print("✅ 历史数据接口工作正常！")
        print("   虽然实时行情有问题，但系统仍然可用。")
    else:
        print("⚠️  所有接口都失败了，建议:")
        print("   1. 检查网络连接")
        print("   2. 尝试使用其他网络环境")
        print("   3. 联系网络管理员")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被中断")

