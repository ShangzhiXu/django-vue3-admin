from django.db import models
from dvadmin.utils.models import CoreModel

table_prefix = "workorder_"


class WorkOrder(CoreModel):
    """
    工单管理模型
    """
    # 工单号：格式 WO + 年月日 + 3位序号，例如 WO20231221001
    workorder_no = models.CharField(max_length=100, unique=True, db_index=True, verbose_name='工单号', help_text='工单号')
    
    # 关联商户表（使用字符串引用，避免循环导入）
    merchant = models.ForeignKey(
        'merchant.Merchant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workorders',
        db_constraint=False,
        verbose_name='商户',
        help_text='关联商户'
    )
    
    # 关联任务表（使用字符串引用，避免循环导入）
    task = models.ForeignKey(
        'task.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workorders',
        db_constraint=False,
        verbose_name='关联任务',
        help_text='该工单所属的任务'
    )
    
    # 项目
    project = models.CharField(max_length=255, null=True, blank=True, verbose_name='项目', help_text='项目名称')
    
    # 项目负责人（关联用户表）
    project_manager = models.ForeignKey(
        'system.Users',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_workorders',
        db_constraint=False,
        verbose_name='项目负责人',
        help_text='项目负责人，默认从任务继承'
    )
    
    # 隐患等级
    HAZARD_LEVEL_CHOICES = (
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    )
    hazard_level = models.CharField(
        max_length=20,
        choices=HAZARD_LEVEL_CHOICES,
        verbose_name='隐患等级',
        help_text='隐患等级'
    )
    
    # 问题描述
    problem_description = models.TextField(null=True, blank=True, verbose_name='问题描述', help_text='问题描述')
    
    # 上报时间（自动记录创建时间）
    report_time = models.DateTimeField(auto_now_add=True, verbose_name='上报时间', help_text='上报时间')
    
    # 截止时间
    deadline = models.DateField(verbose_name='截止时间', help_text='截止时间')
    
    # 工单状态
    STATUS_CHOICES = (
        (0, '待整改'),
        (1, '待复查'),
        (3, '已逾期'),
    )
    status = models.IntegerField(default=0, choices=STATUS_CHOICES, db_index=True, verbose_name='状态', help_text='工单状态')
    
    # 完成时间
    completed_time = models.DateTimeField(null=True, blank=True, verbose_name='完成时间', help_text='完成时间')
    
    # 是否被督办
    is_supervised = models.BooleanField(default=False, db_index=True, verbose_name='是否被督办', help_text='是否被督办')
    
    # 备注
    remark = models.TextField(null=True, blank=True, verbose_name='备注', help_text='备注')

    class Meta:
        db_table = table_prefix + "workorder"
        verbose_name = "工单管理"
        verbose_name_plural = verbose_name
        ordering = ('-create_datetime',)
    
    def __str__(self):
        return f"{self.workorder_no} - {self.merchant.name if self.merchant else '未关联商户'}"


class SupervisionPush(CoreModel):
    """
    督办推送记录模型
    """
    # 推送标题
    title = models.CharField(max_length=255, verbose_name='推送标题', help_text='推送标题')
    
    # 关联工单（多对多关系）
    workorders = models.ManyToManyField(
        'WorkOrder',
        related_name='supervision_pushes',
        db_constraint=False,
        verbose_name='关联工单',
        help_text='被推送的工单列表'
    )
    
    # 监管单位名称（暂时用字符串，后续可扩展为关联表）
    regulatory_unit = models.CharField(max_length=255, verbose_name='监管单位', help_text='监管单位名称')
    
    # 推送方式
    PUSH_METHOD_CHOICES = (
        ('sms', '短信'),
        ('email', '邮件'),
        ('system', '系统通知'),
        ('multiple', '多渠道'),
    )
    push_method = models.CharField(
        max_length=20,
        choices=PUSH_METHOD_CHOICES,
        default='system',
        verbose_name='推送方式',
        help_text='推送方式'
    )
    
    # 推送状态
    PUSH_STATUS_CHOICES = (
        ('pending', '待推送'),
        ('success', '推送成功'),
        ('failed', '推送失败'),
        ('partial', '部分成功'),
    )
    push_status = models.CharField(
        max_length=20,
        choices=PUSH_STATUS_CHOICES,
        default='pending',
        verbose_name='推送状态',
        help_text='推送状态'
    )
    
    # 推送内容
    push_content = models.TextField(verbose_name='推送内容', help_text='推送内容')
    
    # 推送结果详情
    push_result = models.TextField(null=True, blank=True, verbose_name='推送结果', help_text='推送结果详情')
    
    # 推送时间
    push_time = models.DateTimeField(null=True, blank=True, verbose_name='推送时间', help_text='实际推送时间')
    
    # 备注
    remark = models.TextField(null=True, blank=True, verbose_name='备注', help_text='备注')

    class Meta:
        db_table = table_prefix + "supervision_push"
        verbose_name = "督办推送记录"
        verbose_name_plural = verbose_name
        ordering = ('-create_datetime',)
    
    def __str__(self):
        return f"{self.title} - {self.get_push_status_display()}"
