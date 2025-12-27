from typing import Optional

from rest_framework.request import Request

from dvadmin.system.models import MessageCenter, MessageCenterTargetUser, Users


def send_notification_to_user(
    user: Optional[Users],
    title: str,
    content: str,
    request: Optional[Request] = None,
    target_type: int = 0,
) -> Optional[MessageCenter]:
    """
    发送系统通知给单个用户

    :param user: 接收用户
    :param title: 通知标题
    :param content: 通知内容
    :param request: 当前请求（用于记录创建人等审计信息）
    :param target_type: 目标类型，0=按用户，1=按角色，2=按部门，3=系统通知
    :return: 创建的 MessageCenter 实例，或 None（如果 user 为空）
    """
    if not user:
        return None

    # 使用 CoreModelManager.create，可以把 request 传进去，自动填充 creator、dept 等字段
    message = MessageCenter.objects.create(
        request=request,
        title=title,
        content=content,
        target_type=target_type,
    )

    # 关联到目标用户
    MessageCenterTargetUser.objects.create(
        users=user,
        messagecenter=message,
        is_read=False,
    )

    return message








