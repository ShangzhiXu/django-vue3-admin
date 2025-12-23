import traceback
from datetime import datetime
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from django.db.models import Q
from dvadmin.system.models import MessageCenter, MessageCenterTargetUser
from plugins.workorder.models import WorkOrder
from dvadmin.system.models import Users


class MobileNotificationsView(APIView):
    """
    移动端通知接口
    访问示例: GET /api/mobile/notifications?phone={phone}&last_check_time={timestamp}
    """
    permission_classes = [AllowAny]  # 允许匿名访问
    renderer_classes = [JSONRenderer]  # 只返回JSON格式

    def get(self, request):
        """
        获取通知列表
        参数:
            phone: 手机号
            last_check_time: 最后检查时间（时间戳，可选）
        """
        try:
            phone = request.query_params.get('phone', '')
            last_check_time_str = request.query_params.get('last_check_time', '')
            
            print("=" * 80)
            print(f"收到通知查询请求:")
            print(f"  phone: {phone}")
            print(f"  last_check_time: {last_check_time_str}")
            print("=" * 80)
            
            if not phone:
                return Response({
                    "code": 400,
                    "data": {},
                    "msg": "手机号不能为空"
                }, status=400, content_type='application/json')
            
            # 根据手机号查找用户
            try:
                user = Users.objects.get(mobile=phone)
            except Users.DoesNotExist:
                return Response({
                    "code": 404,
                    "data": {},
                    "msg": f"未找到手机号为 {phone} 的用户"
                }, status=404, content_type='application/json')
            
            # 解析最后检查时间
            last_check_time = None
            if last_check_time_str:
                try:
                    # 将时间戳转换为datetime对象
                    timestamp = float(last_check_time_str)
                    last_check_time = timezone.make_aware(datetime.fromtimestamp(timestamp))
                    print(f"  解析后的最后检查时间: {last_check_time}")
                except (ValueError, TypeError) as e:
                    print(f"  解析时间戳失败: {str(e)}")
                    # 如果解析失败，忽略该参数
            
            # 查询该用户的通知（只返回未读的）
            target_qs = MessageCenterTargetUser.objects.filter(users=user)
            # 只取未读的
            target_qs = target_qs.filter(is_read=False)
            # 如果有最后检查时间，只返回该时间之后的通知
            if last_check_time:
                target_qs = target_qs.filter(messagecenter__create_datetime__gt=last_check_time)
            # 按创建时间倒序排列
            target_qs = target_qs.select_related('messagecenter').order_by('-messagecenter__create_datetime')
            
            # 构建通知列表
            notifications = []
            for target in target_qs:
                message = target.messagecenter
                notifications.append({
                    'id': message.id,
                    'title': message.title,
                    'content': message.content,
                    'create_time': message.create_datetime.strftime("%Y-%m-%d %H:%M:%S") if message.create_datetime else None,
                    'create_timestamp': int(message.create_datetime.timestamp()) if message.create_datetime else None,
                    'is_read': bool(target.is_read),
                    'target_type': message.target_type,
                })
            
            print(f"  找到 {len(notifications)} 条通知")
            
            return Response({
                "code": 2000,
                "data": {
                    "phone": phone,
                    "user_id": user.id,
                    "user_name": user.name,
                    "notifications": notifications,
                    "count": len(notifications),
                    "last_check_time": last_check_time_str,
                },
                "msg": "查询成功"
            }, content_type='application/json')
            
        except Exception as e:
            print("=" * 80)
            print(f"获取通知时发生错误:")
            print(f"  错误信息: {str(e)}")
            traceback.print_exc()
            print("=" * 80)
            
            return Response({
                "code": 500,
                "data": {},
                "msg": f"服务器错误: {str(e)}",
            }, status=500, content_type='application/json')


class MobileNotificationReadView(APIView):
    """
    标记通知为已读
    访问示例: GET /api/mobile/notifications/read?phone={phone}&message_id={id}
    """
    permission_classes = [AllowAny]  # 允许匿名访问
    renderer_classes = [JSONRenderer]  # 只返回JSON格式

    def get(self, request):
        """
        标记某条通知为已读
        """
        try:
            phone = request.query_params.get('phone', '')
            message_id = request.query_params.get('message_id', '')

            print("=" * 80)
            print("收到通知已读请求:")
            print(f"  phone: {phone}")
            print(f"  message_id: {message_id}")
            print("=" * 80)

            if not phone or not message_id:
                return Response({
                    "code": 400,
                    "data": {},
                    "msg": "参数 phone 和 message_id 不能为空"
                }, status=400, content_type='application/json')

            # 查找用户
            try:
                user = Users.objects.get(mobile=phone)
            except Users.DoesNotExist:
                return Response({
                    "code": 404,
                    "data": {},
                    "msg": f"未找到手机号为 {phone} 的用户"
                }, status=404, content_type='application/json')

            # 标记为已读
            try:
                target = MessageCenterTargetUser.objects.get(
                    users=user,
                    messagecenter_id=message_id
                )
            except MessageCenterTargetUser.DoesNotExist:
                return Response({
                    "code": 404,
                    "data": {},
                    "msg": "未找到对应的通知记录"
                }, status=404, content_type='application/json')

            if not target.is_read:
                target.is_read = True
                target.save(update_fields=['is_read'])
                print(f"  已标记通知 {message_id} 为已读")

            return Response({
                "code": 2000,
                "data": {
                    "phone": phone,
                    "message_id": int(message_id),
                    "is_read": True,
                },
                "msg": "通知已标记为已读"
            }, content_type='application/json')

        except Exception as e:
            print("=" * 80)
            print(f"标记通知已读时发生错误:")
            print(f"  错误信息: {str(e)}")
            traceback.print_exc()
            print("=" * 80)

            return Response({
                "code": 500,
                "data": {},
                "msg": f"服务器错误: {str(e)}",
            }, status=500, content_type='application/json')

