#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate admin role menu permissions from init_menu.json
"""
import json
import os

# Read menu configuration
menu_file = os.path.join(os.path.dirname(__file__), 'dvadmin', 'system', 'fixtures', 'init_menu.json')
with open(menu_file, 'r', encoding='utf-8') as f:
    menus = json.load(f)

# Function to extract all menus recursively
def extract_menus(menu_list, result=None):
    if result is None:
        result = []
    for menu in menu_list:
        if menu.get('web_path'):
            result.append({
                'role__key': 'admin',
                'menu__web_path': menu['web_path'],
                'menu__component_name': menu.get('component_name', '')
            })
        if menu.get('children'):
            extract_menus(menu['children'], result)
    return result

# Extract all menus
all_permissions = extract_menus(menus)

# Write to file
output_file = os.path.join(os.path.dirname(__file__), 'dvadmin', 'system', 'fixtures', 'init_rolemenupermission.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_permissions, f, ensure_ascii=False, indent=4)

print(f"Generated {len(all_permissions)} menu permissions for admin role")
print(f"Saved to: {output_file}")










