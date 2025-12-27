#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理旧的部门数据
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
django.setup()

from dvadmin.system.models import Dept

# 要删除的旧部门名称
old_dept_names = [
    '总部',
    '商务局（总部）',
]

# 要清理的旧 key 值（如果存在）
old_keys = [
    'dvadmin',
    'swj_hq',
    'zongbu',
    'technology',
]

print("开始清理旧部门数据...")

# 删除旧部门名称
for dept_name in old_dept_names:
    depts = Dept.objects.filter(name=dept_name)
    count = depts.count()
    if count > 0:
        print(f"找到 {count} 个 '{dept_name}' 部门，正在删除...")
        depts.delete()
        print(f"已删除 '{dept_name}'")
    else:
        print(f"未找到 '{dept_name}' 部门")

# 清理旧的 key 值（设置为 None，避免唯一性冲突）
for old_key in old_keys:
    depts = Dept.objects.filter(key=old_key)
    count = depts.count()
    if count > 0:
        print(f"找到 {count} 个 key='{old_key}' 的部门，正在清理 key 值...")
        depts.update(key=None)
        print(f"已清理 key='{old_key}' 的部门")

print("清理完成！")

