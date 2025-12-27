#!/usr/bin/env python
"""
修复督办中心菜单配置
将 is_catalog 设置为 False，确保 component 字段正确
"""
import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
django.setup()

from dvadmin.system.models import Menu

def fix_supervision_menu():
    """修复督办中心菜单"""
    print("开始修复督办中心菜单...")
    
    # 查找督办中心菜单
    supervision_menus = Menu.objects.filter(name='督办中心')
    
    if not supervision_menus.exists():
        print("未找到督办中心菜单，请先创建菜单")
        return
    
    count = 0
    for menu in supervision_menus:
        print(f"\n处理菜单 ID: {menu.id}, 名称: {menu.name}")
        print(f"当前 is_catalog: {menu.is_catalog}")
        print(f"当前 component: {menu.component}")
        print(f"当前 web_path: {menu.web_path}")
        
        # 修复 is_catalog
        if menu.is_catalog:
            menu.is_catalog = False
            print(f"  -> 将 is_catalog 设置为 False")
        
        # 修复 component
        if not menu.component or menu.component.strip() == '':
            menu.component = 'plugins/supervision/index'
            print(f"  -> 设置 component 为: plugins/supervision/index")
        
        # 确保 component_name 正确
        if not menu.component_name or menu.component_name.strip() == '':
            menu.component_name = 'supervision'
            print(f"  -> 设置 component_name 为: supervision")
        
        # 确保 web_path 正确
        if not menu.web_path or menu.web_path.strip() == '':
            menu.web_path = '/supervision'
            print(f"  -> 设置 web_path 为: /supervision")
        
        # 保存
        menu.save()
        count += 1
        print(f"  ✓ 菜单已更新")
    
    print(f"\n完成！共修复 {count} 个督办中心菜单")
    
    # 验证修复结果
    print("\n验证修复结果:")
    for menu in Menu.objects.filter(name='督办中心'):
        print(f"  ID: {menu.id}, is_catalog: {menu.is_catalog}, component: {menu.component}, web_path: {menu.web_path}")

if __name__ == '__main__':
    fix_supervision_menu()

