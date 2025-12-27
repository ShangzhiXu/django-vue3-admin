#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理重复的部门和菜单项
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
django.setup()

from dvadmin.system.models import Dept, Menu
from django.db.models import Count

print("=" * 50)
print("开始清理重复数据...")
print("=" * 50)

# 1. 清理重复的部门
print("\n1. 清理重复的部门...")
dept_duplicates = Dept.objects.values('name', 'parent_id').annotate(count=Count('id')).filter(count__gt=1)

for dup in dept_duplicates:
    name = dup['name']
    parent_id = dup['parent_id']
    count = dup['count']
    
    depts = Dept.objects.filter(name=name, parent_id=parent_id).order_by('id')
    if count > 1:
        # 保留第一个，删除其他的
        keep_dept = depts.first()
        delete_depts = depts.exclude(id=keep_dept.id)
        delete_count = delete_depts.count()
        
        print(f"  找到 {count} 个重复的部门: '{name}' (parent_id={parent_id})")
        print(f"    保留 ID={keep_dept.id} 的部门")
        print(f"    删除 {delete_count} 个重复部门...")
        
        # 先更新关联的用户，将他们的部门指向保留的部门
        from dvadmin.system.models import Users
        for dept in delete_depts:
            Users.objects.filter(dept_id=dept.id).update(dept_id=keep_dept.id)
        
        # 更新子部门的 parent 指向保留的部门
        for dept in delete_depts:
            Dept.objects.filter(parent_id=dept.id).update(parent_id=keep_dept.id)
        
        # 删除重复的部门
        delete_depts.delete()
        print(f"    ✓ 已删除 {delete_count} 个重复部门")

# 2. 清理重复的菜单
print("\n2. 清理重复的菜单...")
menu_duplicates = Menu.objects.values('name', 'web_path', 'component_name').annotate(count=Count('id')).filter(count__gt=1)

for dup in menu_duplicates:
    name = dup['name']
    web_path = dup['web_path']
    component_name = dup['component_name']
    count = dup['count']
    
    menus = Menu.objects.filter(name=name, web_path=web_path, component_name=component_name).order_by('id')
    if count > 1:
        # 保留第一个，删除其他的
        keep_menu = menus.first()
        delete_menus = menus.exclude(id=keep_menu.id)
        delete_count = delete_menus.count()
        
        print(f"  找到 {count} 个重复的菜单: '{name}' (path={web_path})")
        print(f"    保留 ID={keep_menu.id} 的菜单")
        print(f"    删除 {delete_count} 个重复菜单...")
        
        # 更新子菜单的 parent 指向保留的菜单
        for menu in delete_menus:
            Menu.objects.filter(parent_id=menu.id).update(parent_id=keep_menu.id)
        
        # 删除重复的菜单
        delete_menus.delete()
        print(f"    ✓ 已删除 {delete_count} 个重复菜单")

# 3. 特别处理：删除旧的"总部"部门（如果存在）
print("\n3. 清理旧的'总部'部门...")
old_depts = Dept.objects.filter(name='总部')
if old_depts.exists():
    count = old_depts.count()
    print(f"  找到 {count} 个'总部'部门，正在删除...")
    
    # 先更新关联的用户和子部门
    from dvadmin.system.models import Users
    for dept in old_depts:
        # 将用户迁移到"全部"部门或设为 None
        all_dept = Dept.objects.filter(name='全部').first()
        if all_dept:
            Users.objects.filter(dept_id=dept.id).update(dept_id=all_dept.id)
        else:
            Users.objects.filter(dept_id=dept.id).update(dept_id=None)
        
        # 将子部门迁移到"全部"部门
        if all_dept:
            Dept.objects.filter(parent_id=dept.id).update(parent_id=all_dept.id)
        else:
            Dept.objects.filter(parent_id=dept.id).update(parent_id=None)
    
    old_depts.delete()
    print(f"    ✓ 已删除 {count} 个'总部'部门")

print("\n" + "=" * 50)
print("清理完成！")
print("=" * 50)

