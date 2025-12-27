"""
刷新系统配置缓存
使用方法: python manage.py refresh_system_config
"""
from django.core.management.base import BaseCommand
from application import dispatch


class Command(BaseCommand):
    help = '刷新系统配置缓存'

    def handle(self, *args, **options):
        try:
            dispatch.refresh_system_config()
            self.stdout.write(
                self.style.SUCCESS('系统配置缓存已成功刷新！')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'刷新系统配置缓存失败: {str(e)}')
            )

