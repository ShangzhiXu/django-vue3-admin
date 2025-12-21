from datetime import date, datetime
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from dvadmin.utils.serializers import CustomModelSerializer
from dvadmin.utils.viewset import CustomModelViewSet
from dvadmin.utils.json_response import DetailResponse
from plugins.workorder.models import WorkOrder


class WorkOrderSerializer(CustomModelSerializer):
    """
    工单管理-序列化器
    """
    merchant_name = serializers.SerializerMethodField(read_only=True)
    merchant_manager = serializers.SerializerMethodField(read_only=True)
    merchant_phone = serializers.SerializerMethodField(read_only=True)
    hazard_level_display = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.SerializerMethodField(read_only=True)
    task_name = serializers.SerializerMethodField(read_only=True)
    project_manager_name = serializers.SerializerMethodField(read_only=True)
    
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
    
    def get_status_display(self, obj):
        """获取状态的中文显示值"""
        return obj.get_status_display() if obj.status is not None else None
    
    def get_task_name(self, obj):
        """获取关联任务名称"""
        return obj.task.name if obj.task else None
    
    def get_project_manager_name(self, obj):
        """获取项目负责人名称"""
        if obj.project_manager:
            return obj.project_manager.name
        # 如果没有设置项目负责人，尝试从任务继承
        if obj.task and obj.task.manager:
            return obj.task.manager.name
        return None
    
    class Meta:
        model = WorkOrder
        fields = "__all__"
        read_only_fields = ["id", "workorder_no", "report_time"]
    
    def to_representation(self, instance):
        """序列化时自动判断是否逾期"""
        data = super().to_representation(instance)
        # 如果状态不是已逾期，且截止时间已过，自动标记为已逾期
        if instance.status != 3 and instance.deadline and instance.deadline < date.today():
            instance.status = 3
            instance.save(update_fields=['status'])
            data['status'] = 3
        return data


class WorkOrderCreateSerializer(CustomModelSerializer):
    """
    工单创建-序列化器
    """
    
    class Meta:
        model = WorkOrder
        fields = "__all__"
        read_only_fields = ["id", "workorder_no", "report_time", "status"]
    
    def create(self, validated_data):
        """创建工单时自动生成工单号，并从任务继承项目负责人"""
        # 生成工单号：WO + 年月日 + 3位序号
        today = timezone.now().date()
        date_str = today.strftime('%Y%m%d')
        
        # 查询当天最大的序号
        max_order = WorkOrder.objects.filter(
            workorder_no__startswith=f'WO{date_str}'
        ).order_by('-workorder_no').first()
        
        if max_order:
            # 提取序号并加1
            sequence = int(max_order.workorder_no[-3:]) + 1
        else:
            sequence = 1
        
        # 生成工单号
        validated_data['workorder_no'] = f'WO{date_str}{sequence:03d}'
        
        # 如果未设置项目负责人，且有关联任务，则从任务继承
        if not validated_data.get('project_manager') and validated_data.get('task'):
            from plugins.task.models import Task
            task = validated_data['task']
            if isinstance(task, Task) and task.manager:
                validated_data['project_manager'] = task.manager
        
        return super().create(validated_data)


class WorkOrderUpdateSerializer(CustomModelSerializer):
    """
    工单更新-序列化器
    """
    
    class Meta:
        model = WorkOrder
        fields = "__all__"
        read_only_fields = ["id", "workorder_no", "report_time"]


class WorkOrderExportSerializer(CustomModelSerializer):
    """
    工单导出序列化器
    """
    merchant_name = serializers.SerializerMethodField(read_only=True)
    hazard_level = serializers.SerializerMethodField(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)
    task_name = serializers.SerializerMethodField(read_only=True)
    report_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    deadline = serializers.DateField(format="%Y-%m-%d", required=False, read_only=True)
    completed_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    create_datetime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    update_datetime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    
    def get_merchant_name(self, obj):
        """返回商户名称"""
        return obj.merchant.name if obj.merchant else ""
    
    def get_hazard_level(self, obj):
        """返回隐患等级的中文显示值"""
        return obj.get_hazard_level_display() if obj.hazard_level else ""
    
    def get_status(self, obj):
        """返回状态的中文显示值"""
        return obj.get_status_display() if obj.status is not None else ""
    
    def get_task_name(self, obj):
        """返回任务名称"""
        return obj.task.name if obj.task else ""
    
    class Meta:
        model = WorkOrder
        fields = (
            "workorder_no",
            "merchant_name",
            "project",
            "hazard_level",
            "problem_description",
            "report_time",
            "deadline",
            "status",
            "completed_time",
            "task_name",
            "remark",
            "create_datetime",
            "update_datetime",
        )


class WorkOrderViewSet(CustomModelViewSet):
    """
    工单管理接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = WorkOrder.objects.select_related('merchant', 'task').all()
    serializer_class = WorkOrderSerializer
    create_serializer_class = WorkOrderCreateSerializer
    update_serializer_class = WorkOrderUpdateSerializer
    filter_fields = ['status', 'hazard_level', 'deadline']
    search_fields = ['workorder_no']
    extra_filter_class = []
    
    # 导出配置
    export_field_label = {
        "workorder_no": "工单号",
        "merchant_name": "商户名称",
        "project": "项目",
        "hazard_level": "隐患等级",
        "problem_description": "问题描述",
        "report_time": "上报时间",
        "deadline": "截止时间",
        "status": "状态",
        "completed_time": "完成时间",
        "task_name": "关联任务",
        "remark": "备注",
        "create_datetime": "创建时间",
        "update_datetime": "更新时间",
    }
    export_serializer_class = WorkOrderExportSerializer
    
    def get_queryset(self):
        """自定义查询集，支持商户名称搜索和自动判断逾期"""
        queryset = super().get_queryset()
        
        # 自动检查并更新逾期状态
        today = date.today()
        queryset.filter(
            Q(status__in=[0, 1]) &  # 待整改或待复查
            Q(deadline__lt=today)  # 截止时间已过
        ).update(status=3)  # 更新为已逾期
        
        return queryset
    
    def filter_queryset(self, queryset):
        """自定义过滤，支持商户名称搜索"""
        queryset = super().filter_queryset(queryset)
        
        # 处理商户名称搜索
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(workorder_no__icontains=search) |
                Q(merchant__name__icontains=search)
            )
        
        # 处理上报时间范围查询
        report_time_after = self.request.query_params.get('report_time_after', None)
        report_time_before = self.request.query_params.get('report_time_before', None)
        if report_time_after:
            queryset = queryset.filter(report_time__gte=report_time_after)
        if report_time_before:
            queryset = queryset.filter(report_time__lte=report_time_before)
        
        return queryset
    
    @action(methods=['post'], detail=False)
    def batch_supervise(self, request):
        """
        批量督办
        """
        workorder_ids = request.data.get('ids', [])
        if not workorder_ids:
            return DetailResponse(msg="请选择要督办的工单", code=400)
        
        count = WorkOrder.objects.filter(id__in=workorder_ids).update(
            status=0,  # 设置为待整改状态
            is_supervised=True  # 标记为已督办
        )
        
        return DetailResponse(data={'count': count}, msg=f"已对 {count} 个工单执行批量督办")
    
    @action(methods=['post'], detail=True)
    def supervise(self, request, pk=None):
        """
        单个督办
        """
        workorder = self.get_object()
        workorder.status = 0  # 设置为待整改状态
        workorder.is_supervised = True  # 标记为已督办
        workorder.save(update_fields=['status', 'is_supervised'])
        
        return DetailResponse(msg=f"已对工单 {workorder.workorder_no} 执行督办")

