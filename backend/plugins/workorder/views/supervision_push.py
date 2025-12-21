from datetime import date, datetime, timedelta
from django.db.models import Q, F, ExpressionWrapper, DurationField
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from dvadmin.utils.serializers import CustomModelSerializer
from dvadmin.utils.viewset import CustomModelViewSet
from dvadmin.utils.json_response import DetailResponse
from plugins.workorder.models import WorkOrder, SupervisionPush


class SupervisionPushWorkOrderSerializer(CustomModelSerializer):
    """
    督办推送工单列表-序列化器
    """
    merchant_name = serializers.SerializerMethodField(read_only=True)
    merchant_manager = serializers.SerializerMethodField(read_only=True)
    merchant_phone = serializers.SerializerMethodField(read_only=True)
    hazard_level_display = serializers.SerializerMethodField(read_only=True)
    project_manager_name = serializers.SerializerMethodField(read_only=True)
    overdue_days = serializers.SerializerMethodField(read_only=True)
    overdue_hours = serializers.SerializerMethodField(read_only=True)
    overdue_duration_display = serializers.SerializerMethodField(read_only=True)
    lag_level = serializers.SerializerMethodField(read_only=True)
    last_feedback = serializers.SerializerMethodField(read_only=True)
    
    def get_merchant_name(self, obj):
        """获取商户名称"""
        return obj.merchant.name if obj.merchant else None
    
    def get_merchant_manager(self, obj):
        """获取商户负责人"""
        return obj.merchant.manager if obj.merchant else None
    
    def get_merchant_phone(self, obj):
        """获取商户联系电话"""
        return obj.merchant.phone if obj.merchant else None
    
    def get_hazard_level_display(self, obj):
        """获取隐患等级的中文显示值"""
        return obj.get_hazard_level_display() if obj.hazard_level else None
    
    def get_project_manager_name(self, obj):
        """获取项目负责人名称"""
        if obj.project_manager:
            return obj.project_manager.name
        if obj.task and obj.task.manager:
            return obj.task.manager.name
        return None
    
    def get_overdue_days(self, obj):
        """计算逾期天数"""
        if obj.deadline:
            today = date.today()
            delta = today - obj.deadline
            return max(0, delta.days)
        return 0
    
    def get_overdue_hours(self, obj):
        """计算逾期总小时数"""
        if obj.deadline:
            # 由于 USE_TZ = False，使用 naive datetime
            now = datetime.now()
            # deadline是DateField，转换为datetime（当天0点）
            deadline_datetime = datetime.combine(obj.deadline, datetime.min.time())
            if now > deadline_datetime:
                delta = now - deadline_datetime
                total_hours = int(delta.total_seconds() / 3600)
                return total_hours
        return 0
    
    def get_overdue_duration_display(self, obj):
        """获取逾期时长显示文本（如：5天4小时）"""
        days = self.get_overdue_days(obj)
        total_hours = self.get_overdue_hours(obj)
        
        if total_hours > 0:
            # 计算超出天数的额外小时数
            extra_hours = total_hours % 24
            if days > 0:
                if extra_hours > 0:
                    return f"{days}天{extra_hours}小时"
                return f"{days}天"
            else:
                return f"{total_hours}小时"
        elif days > 0:
            return f"{days}天"
        return "0小时"
    
    def get_lag_level(self, obj):
        """获取滞后级别"""
        days = self.get_overdue_days(obj)
        if days > 3:
            return {'label': '严重滞后', 'type': 'danger'}
        elif days > 1:
            return {'label': '一般滞后', 'type': 'warning'}
        elif days > 0:
            return {'label': '轻微滞后', 'type': 'info'}
        return {'label': '正常', 'type': 'success'}
    
    def get_last_feedback(self, obj):
        """获取最后反馈信息（暂时使用remark字段，后续可扩展）"""
        if obj.remark:
            return obj.remark
        return "无任何反馈"
    
    class Meta:
        model = WorkOrder
        fields = [
            "id", "workorder_no", "merchant_name", "merchant_manager", "merchant_phone",
            "project", "hazard_level", "hazard_level_display", "problem_description",
            "report_time", "deadline", "status", "project_manager_name",
            "overdue_days", "overdue_hours", "overdue_duration_display",
            "lag_level", "last_feedback", "create_datetime"
        ]


class SupervisionPushSerializer(CustomModelSerializer):
    """
    督办推送记录-序列化器
    """
    workorder_count = serializers.SerializerMethodField(read_only=True)
    push_method_display = serializers.SerializerMethodField(read_only=True)
    push_status_display = serializers.SerializerMethodField(read_only=True)
    
    def get_workorder_count(self, obj):
        """获取关联工单数量"""
        return obj.workorders.count()
    
    def get_push_method_display(self, obj):
        """获取推送方式显示值"""
        return obj.get_push_method_display() if obj.push_method else None
    
    def get_push_status_display(self, obj):
        """获取推送状态显示值"""
        return obj.get_push_status_display() if obj.push_status else None
    
    class Meta:
        model = SupervisionPush
        fields = "__all__"
        read_only_fields = ["id", "push_time"]


class SupervisionPushViewSet(CustomModelViewSet):
    """
    督办推送接口
    """
    queryset = SupervisionPush.objects.prefetch_related('workorders').all()
    serializer_class = SupervisionPushSerializer
    filter_fields = ['push_status', 'push_method']
    search_fields = ['title', 'regulatory_unit']
    
    @action(methods=['get'], detail=False, url_path='workorder-list')
    def workorder_list(self, request):
        """
        获取待督办工单列表（支持筛选）
        """
        # 获取筛选参数
        overdue_hours = request.query_params.get('overdue_hours', None)  # 逾期时长（小时）
        hazard_level = request.query_params.get('hazard_level', None)  # 隐患等级
        status = request.query_params.get('status', None)  # 工单状态
        
        # 基础查询：查询已逾期或已被督办的工单（status=3或deadline已过或is_supervised=True）
        queryset = WorkOrder.objects.filter(
            Q(status=3) | Q(deadline__lt=date.today()) | Q(is_supervised=True)
        ).select_related('merchant', 'task', 'project_manager').order_by('-deadline')
        
        # 按逾期时长筛选
        if overdue_hours:
            try:
                hours = int(overdue_hours)
                # 计算最早截止时间（现在减去逾期小时数）
                # 由于 USE_TZ = False，使用 naive datetime
                cutoff_datetime = datetime.now() - timedelta(hours=hours)
                # 转换为date对象，因为deadline是DateField
                cutoff_date = cutoff_datetime.date()
                # 筛选截止时间早于cutoff_date的工单
                queryset = queryset.filter(deadline__lte=cutoff_date)
            except (ValueError, TypeError):
                pass
        
        # 按隐患等级筛选
        if hazard_level:
            queryset = queryset.filter(hazard_level=hazard_level)
        
        # 按状态筛选
        if status is not None:
            try:
                status_int = int(status)
                queryset = queryset.filter(status=status_int)
            except (ValueError, TypeError):
                pass
        
        # 自动更新逾期状态
        today = date.today()
        queryset.filter(
            Q(status__in=[0, 1]) & Q(deadline__lt=today)
        ).update(status=3)
        
        # 分页
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 10))
        offset = (page - 1) * limit
        
        total = queryset.count()
        workorders = queryset[offset:offset + limit]
        
        serializer = SupervisionPushWorkOrderSerializer(workorders, many=True)
        
        return DetailResponse(
            data={
                'list': serializer.data,
                'total': total,
                'page': page,
                'limit': limit
            },
            msg="获取成功"
        )
    
    @action(methods=['post'], detail=False, url_path='batch-push')
    def batch_push(self, request):
        """
        批量推送督办通知
        """
        workorder_ids = request.data.get('workorder_ids', [])
        regulatory_unit = request.data.get('regulatory_unit', '监管单位')
        push_method = request.data.get('push_method', 'system')
        
        if not workorder_ids:
            return DetailResponse(msg="请选择要推送的工单", code=400)
        
        # 获取工单
        workorders = WorkOrder.objects.filter(id__in=workorder_ids)
        if not workorders.exists():
            return DetailResponse(msg="工单不存在", code=400)
        
        # 生成推送内容
        workorder_list = []
        for wo in workorders:
            overdue_days = (date.today() - wo.deadline).days if wo.deadline else 0
            workorder_list.append(
                f"工单号：{wo.workorder_no}，商户：{wo.merchant.name if wo.merchant else '未知'}，"
                f"问题：{wo.problem_description or '无'}，逾期：{overdue_days}天"
            )
        
        push_content = f"督办通知\n\n以下是严重逾期工单，请及时处理：\n\n" + "\n".join(workorder_list)
        push_title = f"督办通知-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 创建推送记录
        push_record = SupervisionPush.objects.create(
            title=push_title,
            regulatory_unit=regulatory_unit,
            push_method=push_method,
            push_content=push_content,
            push_status='success',  # 暂时默认为成功，后续接入实际推送接口后改为pending
            push_time=datetime.now()  # 由于 USE_TZ = False，使用 naive datetime
        )
        
        # 关联工单
        push_record.workorders.set(workorders)
        
        # TODO: 这里可以接入实际的推送服务（短信、邮件等）
        # 暂时只是记录，不实际发送
        
        return DetailResponse(
            data={
                'push_id': push_record.id,
                'count': workorders.count()
            },
            msg=f"已成功推送 {workorders.count()} 个工单的督办通知"
        )
    
    @action(methods=['get'], detail=False, url_path='history')
    def history(self, request):
        """
        获取推送历史列表
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # 分页
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 10))
        offset = (page - 1) * limit
        
        total = queryset.count()
        records = queryset[offset:offset + limit]
        
        serializer = self.get_serializer(records, many=True)
        
        return DetailResponse(
            data={
                'list': serializer.data,
                'total': total,
                'page': page,
                'limit': limit
            },
            msg="获取成功"
        )

