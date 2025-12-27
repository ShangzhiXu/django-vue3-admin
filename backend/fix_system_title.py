#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复系统配置中的标题
将"通榆县巡检平台系统"更新为"通榆县商贸安全管理平台"
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
django.setup()

from dvadmin.system.models import SystemConfig
from application import dispatch

print("开始修复系统配置标题...")

# 查找登录页配置的父级
login_parent = SystemConfig.objects.filter(key='login', parent__isnull=True).first()
if not login_parent:
    print("未找到'登录页配置'父级配置，请检查数据库")
    exit(1)

# 查找并更新 site_title
site_title_config = SystemConfig.objects.filter(
    parent=login_parent,
    key='site_title'
).first()

if site_title_config:
    old_value = site_title_config.value
    if old_value == '通榆县巡检平台系统':
        site_title_config.value = '通榆县商贸安全管理平台'
        site_title_config.save()
        print(f"已更新 site_title: '{old_value}' -> '通榆县商贸安全管理平台'")
    else:
        print(f"site_title 当前值为: '{old_value}'，无需更新")
else:
    print("未找到 site_title 配置项")

# 查找并更新 site_name
site_name_config = SystemConfig.objects.filter(
    parent=login_parent,
    key='site_name'
).first()

if site_name_config:
    old_value = site_name_config.value
    if old_value == '通榆县巡检平台系统':
        site_name_config.value = '通榆县商贸安全管理平台'
        site_name_config.save()
        print(f"已更新 site_name: '{old_value}' -> '通榆县商贸安全管理平台'")
    else:
        print(f"site_name 当前值为: '{old_value}'，无需更新")
else:
    print("未找到 site_name 配置项")

# 刷新系统配置缓存
print("\n正在刷新系统配置缓存...")
try:
    dispatch.refresh_system_config()
    print("系统配置缓存已刷新")
except Exception as e:
    print(f"刷新缓存时出错: {str(e)}")

print("\n修复完成！")
print("提示: 如果前端仍显示旧标题，请清除浏览器缓存或重新登录")

