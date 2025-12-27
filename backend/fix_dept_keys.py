#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复部门 key 值冲突
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
django.setup()

from dvadmin.system.models import Dept

print("开始修复部门 key 值...")

# 清理可能冲突的旧 key 值
conflict_keys = ['all', 'swj', 'swj_jgj', 'swj_jgj_aqk', 'swj_jgj_bgs', 'swj_jgj_jjjs', 
                 'swj_jgj_smlt', 'swj_jgj_db', 'swj_zshxmzx', 'swj_zshxmzx_bgs', 
                 'swj_zshxmzx_fwk', 'swj_zshxmzx_zsk', 'swj_lwsczx', 'swj_lwsczx_lwsczx',
                 'zjj', 'zjj_jgj', 'zjj_jgj_bgs', 'xfjydd', 'xfjydd_ddjg', 'xfjydd_ddjg_bgs',
                 'yjj', 'yjj_jgj', 'yjj_jgj_bgs']

# 将冲突的 key 值改为 None（避免唯一性约束）
for key in conflict_keys:
    depts = Dept.objects.filter(key=key)
    count = depts.count()
    if count > 0:
        print(f"找到 {count} 个 key='{key}' 的部门，正在清理...")
        # 将 key 改为 None，避免唯一性冲突
        depts.update(key=None)
        print(f"已清理 key='{key}' 的部门")

# 更新旧部门名称
old_names = {
    '总部': None,  # 删除或重命名
    '商务局（总部）': '商务局',
}

for old_name, new_name in old_names.items():
    depts = Dept.objects.filter(name=old_name)
    count = depts.count()
    if count > 0:
        if new_name:
            print(f"找到 {count} 个 '{old_name}' 部门，正在重命名为 '{new_name}'...")
            depts.update(name=new_name, key=None)
        else:
            print(f"找到 {count} 个 '{old_name}' 部门，正在清理 key 值...")
            depts.update(key=None)

print("修复完成！现在可以重新初始化部门数据了。")

