#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为admin角色授权所有菜单权限的脚本
使用方法：
1. 直接运行此脚本：python grant_all_menus_to_admin.py
2. 或者通过Django shell运行：python manage.py shell < grant_all_menus_to_admin.py
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
django.setup()

from dvadmin.system.models import Role, Menu, RoleMenuPermission

def grant_all_menus_to_admin():
    """
    Grant all menu permissions to admin role
    """
    try:
        # Get admin role
        admin_role = Role.objects.get(key='admin')
        print(f"Found admin role: {admin_role.name} (ID: {admin_role.id})")
        
        # Get all menus
        all_menus = Menu.objects.all()
        print(f"Found {all_menus.count()} menus")
        
        # Get existing menu permissions for admin role
        existing_permissions = RoleMenuPermission.objects.filter(role=admin_role)
        existing_menu_ids = set(existing_permissions.values_list('menu_id', flat=True))
        print(f"Admin role already has {len(existing_menu_ids)} menu permissions")
        
        # Create permissions for all menus (if not exists)
        added_count = 0
        for menu in all_menus:
            if menu.id not in existing_menu_ids:
                RoleMenuPermission.objects.create(role=admin_role, menu=menu)
                added_count += 1
                print(f"  + Granted menu: {menu.name} ({menu.web_path})")
        
        print(f"\nDone! Added {added_count} new menu permissions to admin role")
        print(f"Admin role now has {RoleMenuPermission.objects.filter(role=admin_role).count()} menu permissions")
        
    except Role.DoesNotExist:
        print("Error: Admin role not found. Please run 'python manage.py init' first")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    grant_all_menus_to_admin()

