#!/bin/bash
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
