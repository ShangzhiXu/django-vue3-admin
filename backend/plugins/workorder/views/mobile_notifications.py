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
                except (ValueError, TypeError) as e:
                    # 如果解析失败，忽略该参数
                    pass
            
            # 查询该用户的所有通知（包括已读和未读）
            target_qs = MessageCenterTargetUser.objects.filter(users=user)
            # 如果有最后检查时间，只返回该时间之后的通知
            if last_check_time:
                target_qs = target_qs.filter(messagecenter__create_datetime__gt=last_check_time)
            # 按创建时间倒序排列
            target_qs = target_qs.select_related('messagecenter').order_by('-messagecenter__create_datetime')
            
            # 构建通知列表
            notifications = []
            for target in target_qs:
                message = target.messagecenter
                is_read_value = bool(target.is_read)
                notifications.append({
                    'id': message.id,
                    'title': message.title,
                    'content': message.content,
                    'create_time': message.create_datetime.strftime("%Y-%m-%d %H:%M:%S") if message.create_datetime else None,
                    'create_timestamp': int(message.create_datetime.timestamp()) if message.create_datetime else None,
                    'is_read': is_read_value,
                    'target_type': message.target_type,
                })
            
            
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
            return Response({
                "code": 500,
                "data": {},
                "msg": f"服务器错误: {str(e)}",
            }, status=500, content_type='application/json')


class MobileNotificationReadView(APIView):
    """
    标记通知为已读
    访问示例: GET/POST /api/mobile/notifications/read?phone={phone}&message_id={id}
    """
    permission_classes = [AllowAny]  # 允许匿名访问
    renderer_classes = [JSONRenderer]  # 只返回JSON格式

    def _mark_as_read(self, request):
        """
        标记某条通知为已读（内部方法，供GET和POST共用）
        """
        try:
            # 支持GET和POST两种方式
            # 优先从query_params获取（GET请求或POST请求的URL参数）
            phone = request.query_params.get('phone', '')
            message_id = request.query_params.get('message_id', '')
            
            # 如果query_params中没有，尝试从request.data获取（POST请求的body）
            if not phone and hasattr(request, 'data'):
                phone = request.data.get('phone', '')
            if not message_id and hasattr(request, 'data'):
                message_id = request.data.get('message_id', '')

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

            # 标记为已读（不删除记录）
            message_id_value = int(message_id)
            
            # 更新为已读状态
            target.is_read = True
            target.save(update_fields=['is_read'])  # 明确指定更新字段
            
            # 验证更新是否成功
            target.refresh_from_db()  # 从数据库重新加载

            return Response({
                "code": 2000,
                "data": {
                    "phone": phone,
                    "message_id": message_id_value,
                    "is_read": True,
                },
                "msg": "通知已标记为已读"
            }, content_type='application/json')

        except Exception as e:
            return Response({
                "code": 500,
                "data": {},
                "msg": f"服务器错误: {str(e)}",
            }, status=500, content_type='application/json')

    def get(self, request):
        """
        标记某条通知为已读 (GET方法)
        """
        return self._mark_as_read(request)

    def post(self, request):
        """
        标记某条通知为已读 (POST方法)
        """
        return self._mark_as_read(request)

