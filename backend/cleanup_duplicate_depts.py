#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理重复的部门数据
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
django.setup()

from dvadmin.system.models import Dept
from collections import defaultdict

print("开始清理重复部门数据...\n")

# 1. 删除"技术部"和"运营部"
dept_names_to_delete = ['技术部', '运营部']
print("=" * 50)
print("步骤1: 删除不需要的部门")
print("=" * 50)
for dept_name in dept_names_to_delete:
    depts = Dept.objects.filter(name=dept_name)
    count = depts.count()
    if count > 0:
        print(f"找到 {count} 个 '{dept_name}' 部门，正在删除...")
        depts.delete()
        print(f"已删除 '{dept_name}'\n")
    else:
        print(f"未找到 '{dept_name}' 部门\n")

# 2. 清理重复的部门（根据name、parent、key来判断）
print("=" * 50)
print("步骤2: 清理重复的部门")
print("=" * 50)

# 获取所有部门
all_depts = Dept.objects.all()
dept_groups = defaultdict(list)

# 按 (name, parent_id, key) 分组
for dept in all_depts:
    parent_id = dept.parent_id if dept.parent else None
    key = dept.key if dept.key else None
    group_key = (dept.name, parent_id, key)
    dept_groups[group_key].append(dept)

# 找出重复的部门组
duplicate_count = 0
for group_key, depts in dept_groups.items():
    if len(depts) > 1:
        name, parent_id, key = group_key
        parent_info = f"parent_id={parent_id}" if parent_id else "parent=None"
        key_info = f"key={key}" if key else "key=None"
        print(f"发现重复: '{name}' ({parent_info}, {key_info}) - 共 {len(depts)} 个")
        
        # 保留第一个（通常是ID最小的），删除其余的
        depts_sorted = sorted(depts, key=lambda x: x.id)
        keep_dept = depts_sorted[0]
        delete_depts = depts_sorted[1:]
        
        print(f"  保留: ID={keep_dept.id}, 创建时间={keep_dept.create_datetime}")
        for dup_dept in delete_depts:
            print(f"  删除: ID={dup_dept.id}, 创建时间={dup_dept.create_datetime}")
            dup_dept.delete()
            duplicate_count += 1
        print()

if duplicate_count == 0:
    print("未发现重复的部门\n")

# 3. 确保"全部"下面只有各个局
print("=" * 50)
print("步骤3: 调整'全部'下的子部门")
print("=" * 50)

# 获取"全部"部门
all_dept = Dept.objects.filter(name="全部", key="all").first()
if not all_dept:
    print("未找到'全部'部门，跳过此步骤\n")
else:
    # 应该包含的局（根据配置文件）
    expected_bureaus = ['商务局', '住建局', '消防救援大队', '应急局']
    
    # 获取"全部"下的所有直接子部门
    children = Dept.objects.filter(parent=all_dept)
    print(f"'全部'下当前有 {children.count()} 个子部门:")
    for child in children:
        print(f"  - {child.name} (ID={child.id})")
    
    # 找出需要删除的子部门（不在预期列表中的）
    to_delete = []
    for child in children:
        if child.name not in expected_bureaus:
            to_delete.append(child)
            print(f"  标记删除: {child.name} (不在预期列表中)")
    
    # 删除不需要的子部门
    if to_delete:
        for dept in to_delete:
            print(f"  正在删除: {dept.name} (ID={dept.id})")
            dept.delete()
        print(f"已删除 {len(to_delete)} 个不需要的子部门\n")
    else:
        print("'全部'下的子部门都是正确的，无需调整\n")
    
    # 检查各个局是否在"全部"下，如果不在则添加
    print("检查各个局是否在'全部'下:")
    for bureau_name in expected_bureaus:
        bureau = Dept.objects.filter(name=bureau_name, parent__isnull=True).first()
        if bureau:
            if bureau.parent_id != all_dept.id:
                print(f"  {bureau_name} 不在'全部'下，正在调整...")
                bureau.parent = all_dept
                bureau.save()
                print(f"  已调整 {bureau_name} 的父部门为'全部'")
            else:
                print(f"  {bureau_name} 已在'全部'下 ✓")
        else:
            print(f"  警告: 未找到 {bureau_name} 部门")

print("\n" + "=" * 50)
print("清理完成！")
print("=" * 50)

