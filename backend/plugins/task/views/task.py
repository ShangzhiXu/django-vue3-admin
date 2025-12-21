from datetime import datetime
from django.db.models import Q
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.decorators import action
from rest_framework.response import Response

from dvadmin.utils.serializers import CustomModelSerializer
from dvadmin.utils.viewset import CustomModelViewSet
from dvadmin.utils.json_response import DetailResponse
from plugins.task.models import Task
from plugins.merchant.models import Merchant
from plugins.workorder.models import WorkOrder
from plugins.workorder.views.workorder import WorkOrderSerializer


class TaskSerializer(CustomModelSerializer):
    """
    任务管理-序列化器
    """
    merchant_count = serializers.SerializerMethodField(read_only=True)
    workorder_count = serializers.SerializerMethodField(read_only=True)
    time_range = serializers.SerializerMethodField(read_only=True)
    # 使用 SerializerMethodField 返回中文显示值
    cycle = serializers.SerializerMethodField(read_only=True)
    # 保留原始值用于编辑
    cycle_value = serializers.CharField(source='cycle', read_only=True)
    manager_name = serializers.SerializerMethodField(read_only=True)
    
    def get_merchant_count(self, obj):
        """获取商户数量"""
        return obj.merchants.count()
    
    def get_workorder_count(self, obj):
        """获取关联的工单数量"""
        return obj.workorders.count()
    
    def get_cycle(self, obj):
        """返回周期的中文显示值"""
        if obj.cycle:
            return obj.get_cycle_display()  # 返回中文：每日、每周、每月等
        return None
    
    def get_manager_name(self, obj):
        """返回负责人名称"""
        return obj.manager.name if obj.manager else None
    
    def get_time_range(self, obj):
        """返回时间范围数组（前端格式）"""
        if obj.start_time and obj.end_time:
            return [
                obj.start_time.strftime('%Y-%m-%d'),
                obj.end_time.strftime('%Y-%m-%d')
            ]
        return None
    
    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ["id", "merchant_count", "workorder_count"]


class TaskCreateSerializer(CustomModelSerializer):
    """
    任务创建-序列化器
    """
   
    time_range = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="时间范围 [start_time, end_time]"
    )
    # 显式设置 start_time 和 end_time 为可选，因为会从 time_range 转换而来
    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    merchants = PrimaryKeyRelatedField(
        many=True,
        queryset=Merchant.objects.all(),
        required=False,
        allow_null=True,
        help_text="覆盖商户列表（ID数组）"
    )
    
    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ["id"]
    
    def validate_cycle(self, value):
        """验证周期字段，支持中文值转换为英文值"""
        # 如果值为空，返回原值
        if not value:
            return value
        
        # 转换为字符串，确保能正确比较
        value_str = str(value).strip()
        
        # 周期选项的中文到英文映射
        cycle_map = {
            '不重复': 'once',
            '每日': 'daily',
            '每周': 'weekly',
            '每月': 'monthly',
            '每年': 'yearly',
            '自定义': 'custom',
        }
        
        # 如果传入的是中文值，转换为英文值
        if value_str in cycle_map:
            return cycle_map[value_str]
        
        # 如果已经是英文值，验证是否在有效选项中
        valid_choices = [choice[0] for choice in Task.CYCLE_CHOICES]
        if value_str not in valid_choices:
            raise serializers.ValidationError(
                f"周期 '{value_str}' 不是合法选项。有效选项: {', '.join(valid_choices)}"
            )
        
        return value_str
    
    def _parse_date(self, date_str):
        """解析日期字符串，支持多种格式"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # 如果包含 T（ISO 格式），提取日期部分
        if 'T' in date_str:
            date_part = date_str.split('T')[0]
            try:
                return datetime.strptime(date_part, '%Y-%m-%d')
            except ValueError:
                pass
        
        # 尝试直接解析为 YYYY-MM-DD 格式
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            pass
        
        # 尝试解析为 YYYY-MM-DD HH:MM:SS 格式
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
        
        raise ValueError(f"无法解析日期格式: {date_str}，期望格式: YYYY-MM-DD")
    
    def validate(self, attrs):
        """验证时间范围"""
        print("=" * 50)
        print("【调试信息】开始创建任务")
        print("接收到的 attrs 所有字段:", list(attrs.keys()))
        print("time_range 的值:", attrs.get('time_range'))
        print("time_range 的类型:", type(attrs.get('time_range')))
        if attrs.get('time_range'):
            print("time_range 的长度:", len(attrs.get('time_range')))
            print("time_range 的每个元素:", [str(item) for item in attrs.get('time_range')])
        print("=" * 50)
        
        time_range = attrs.pop('time_range', None)
        
        # time_range 是必填的，必须存在
        if not time_range:
            raise serializers.ValidationError({"time_range": "必须提供时间范围"})
        
        # 验证 time_range 格式
        if not isinstance(time_range, list):
            raise serializers.ValidationError({"time_range": "time_range 必须是数组格式"})
        
        if len(time_range) != 2:
            raise serializers.ValidationError({"time_range": f"time_range 数组长度必须为2，当前为 {len(time_range)}"})
        
        # 转换时间格式
        try:
            attrs['start_time'] = self._parse_date(time_range[0])
            attrs['end_time'] = self._parse_date(time_range[1])
        except ValueError as e:
            raise serializers.ValidationError({"time_range": f"时间格式错误，应为 'YYYY-MM-DD'，错误详情: {str(e)}"})
        
        # 验证时间逻辑
        if attrs['start_time'] >= attrs['end_time']:
            raise serializers.ValidationError({"time_range": "结束时间必须晚于开始时间"})
        
        print("验证通过，最终 attrs 中的时间字段:", {
            'start_time': attrs.get('start_time'),
            'end_time': attrs.get('end_time')
        })
        print("=" * 50)
        
        return attrs
    
    def create(self, validated_data):
        """创建任务，处理多对多字段"""
        merchants = validated_data.pop('merchants', [])
        task = super().create(validated_data)
        if merchants:
            task.merchants.set(merchants)
        return task


class TaskUpdateSerializer(CustomModelSerializer):
    """
    任务更新-序列化器
    """
    time_range = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="时间范围 [start_time, end_time]"
    )
    # 显式设置 start_time 和 end_time 为可选，因为会从 time_range 转换而来
    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    merchants = PrimaryKeyRelatedField(
        many=True,
        queryset=Merchant.objects.all(),
        required=False,
        allow_null=True,
        help_text="覆盖商户列表（ID数组）"
    )
    
    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ["id"]
    
    def validate_cycle(self, value):
        """验证周期字段，支持中文值转换为英文值"""
        # 如果值为空，且是更新操作，允许不传（保持原值）
        if not value:
            # 如果是更新操作且没有传 cycle 字段，返回 None（保持原值）
            if self.instance:
                return None
            return value
        
        # 转换为字符串，确保能正确比较
        value_str = str(value).strip()
        
        # 周期选项的中文到英文映射
        cycle_map = {
            '不重复': 'once',
            '每日': 'daily',
            '每周': 'weekly',
            '每月': 'monthly',
            '每年': 'yearly',
            '自定义': 'custom',
        }
        
        # 如果传入的是中文值，转换为英文值
        if value_str in cycle_map:
            return cycle_map[value_str]
        
        # 如果已经是英文值，验证是否在有效选项中
        valid_choices = [choice[0] for choice in Task.CYCLE_CHOICES]
        if value_str not in valid_choices:
            raise serializers.ValidationError(
                f"周期 '{value_str}' 不是合法选项。有效选项: {', '.join(valid_choices)}"
            )
        
        return value_str
    
    def _parse_date(self, date_str):
        """解析日期字符串，支持多种格式"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # 如果包含 T（ISO 格式），提取日期部分
        if 'T' in date_str:
            date_part = date_str.split('T')[0]
            try:
                return datetime.strptime(date_part, '%Y-%m-%d')
            except ValueError:
                pass
        
        # 尝试直接解析为 YYYY-MM-DD 格式
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            pass
        
        # 尝试解析为 YYYY-MM-DD HH:MM:SS 格式
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
        
        raise ValueError(f"无法解析日期格式: {date_str}，期望格式: YYYY-MM-DD")
    
    def validate(self, attrs):
        """验证时间范围"""
        time_range = attrs.pop('time_range', None)
        
        # 只有在 time_range 存在且有效时才进行转换
        if time_range:
            # 检查 time_range 是否为有效数组
            if not isinstance(time_range, list):
                # 如果 time_range 不是数组，可能是前端发送了其他格式，忽略它
                pass
            elif len(time_range) == 2 and time_range[0] and time_range[1]:
                # 只有当数组长度为2且两个元素都不为空时才转换
                try:
                    attrs['start_time'] = self._parse_date(time_range[0])
                    attrs['end_time'] = self._parse_date(time_range[1])
                    
                    if attrs['start_time'] >= attrs['end_time']:
                        raise serializers.ValidationError({"time_range": "结束时间必须晚于开始时间"})
                except ValueError as e:
                    raise serializers.ValidationError({"time_range": f"时间格式错误，应为 'YYYY-MM-DD'，错误详情: {str(e)}"})
            # 如果 time_range 为空数组或只有一个元素，不进行转换，保持原有时间
        
        # 如果只更新了部分时间字段，需要与现有数据比较
        if self.instance:
            start_time = attrs.get('start_time', self.instance.start_time)
            end_time = attrs.get('end_time', self.instance.end_time)
            if start_time and end_time and start_time >= end_time:
                raise serializers.ValidationError({"time_range": "结束时间必须晚于开始时间"})
        
        return attrs
    
    def update(self, instance, validated_data):
        """更新任务，处理多对多字段"""
        merchants = validated_data.pop('merchants', None)
        task = super().update(instance, validated_data)
        if merchants is not None:
            task.merchants.set(merchants)
        return task


class TaskExportSerializer(CustomModelSerializer):
    """
    任务导出序列化器
    """
    cycle = serializers.SerializerMethodField(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)
    manager_name = serializers.SerializerMethodField(read_only=True)
    start_time = serializers.DateTimeField(format="%Y-%m-%d", required=False, read_only=True)
    end_time = serializers.DateTimeField(format="%Y-%m-%d", required=False, read_only=True)
    merchants = serializers.SerializerMethodField(read_only=True)
    create_datetime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    update_datetime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    
    def get_cycle(self, obj):
        """返回周期的中文显示值"""
        return obj.get_cycle_display() if obj.cycle else ""
    
    def get_status(self, obj):
        """返回状态的中文显示值"""
        return obj.get_status_display() if obj.status is not None else ""
    
    def get_manager_name(self, obj):
        """返回负责人名称"""
        return obj.manager.name if obj.manager else ""
    
    def get_merchants(self, obj):
        """返回商户名称列表（用逗号分隔）"""
        merchant_names = obj.merchants.values_list('name', flat=True)
        return ', '.join(merchant_names) if merchant_names else ""
    
    class Meta:
        model = Task
        fields = (
            "name",
            "manager_name",
            "cycle",
            "start_time",
            "end_time",
            "merchants",
            "check_items",
            "status",
            "remark",
            "create_datetime",
            "update_datetime",
        )


class TaskViewSet(CustomModelViewSet):
    """
    任务管理接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = Task.objects.select_related('manager').prefetch_related('merchants', 'workorders').all()
    serializer_class = TaskSerializer
    create_serializer_class = TaskCreateSerializer
    update_serializer_class = TaskUpdateSerializer
    filter_fields = ['name', 'cycle', 'status', 'start_time', 'end_time']
    search_fields = ['name']
    extra_filter_class = []
    
    # 导出配置
    export_field_label = {
        "name": "任务名称",
        "manager_name": "负责人",
        "cycle": "周期",
        "start_time": "开始时间",
        "end_time": "结束时间",
        "merchants": "覆盖商户",
        "check_items": "检查项",
        "status": "状态",
        "remark": "备注",
        "create_datetime": "创建时间",
        "update_datetime": "更新时间",
    }
    export_serializer_class = TaskExportSerializer
    
    def create(self, request, *args, **kwargs):
        """重写 create 方法，添加调试信息"""
        print("=" * 50)
        print("【ViewSet 调试】接收到创建任务请求")
        print("原始 request.data:", request.data)
        print("request.data 类型:", type(request.data))
        if 'time_range' in request.data:
            print("time_range 在 request.data 中，值为:", request.data.get('time_range'))
            print("time_range 类型:", type(request.data.get('time_range')))
        print("=" * 50)
        return super().create(request, *args, **kwargs)
    
    def filter_queryset(self, queryset):
        """自定义过滤，支持时间范围查询和商户筛选"""
        queryset = super().filter_queryset(queryset)
        
        # 处理时间范围查询（前端传 time_range）
        time_range = self.request.query_params.get('time_range', None)
        if time_range:
            # 如果前端传的是时间范围字符串，需要解析
            # 这里假设前端可能通过其他方式传参，实际可能需要根据前端实现调整
            pass
        
        # 处理商户筛选
        merchant = self.request.query_params.get('merchant', None)
        if merchant:
            queryset = queryset.filter(merchants__id=merchant)
        
        return queryset
    
    @action(methods=['get'], detail=True)
    def workorders(self, request, pk=None):
        """
        获取任务关联的工单列表
        """
        task = self.get_object()
        workorders = WorkOrder.objects.filter(task=task).select_related('merchant', 'task').order_by('-create_datetime')
        
        # 分页
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 10))
        offset = (page - 1) * limit
        
        total = workorders.count()
        workorders = workorders[offset:offset + limit]
        
        serializer = WorkOrderSerializer(workorders, many=True)
        
        return DetailResponse(
            data={
                'list': serializer.data,
                'total': total,
                'page': page,
                'limit': limit
            },
            msg="获取成功"
        )

