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
    
    # 检查类别（例如：安全管理类、燃气类、消防类、液体燃料类）
    CHECK_CATEGORY_CHOICES = (
        ('safety_manage', '安全管理类'),
        ('gas', '燃气类'),
        ('fire', '消防类'),
        ('liquid_fuel', '液体燃料类'),
    )
    check_category = models.CharField(
        max_length=32,
        choices=CHECK_CATEGORY_CHOICES,
        null=True,
        blank=True,
        verbose_name='检查类别',
        help_text='安全管理类、燃气类、消防类、液体燃料类等'
    )

    # 具体检查问题（单选项，例如“安全生产制度”“燃气报警器、燃气自动切断装置”等）
    check_item = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='检查问题',
        help_text='具体检查问题，来自预设问题列表'
    )
    
    # 检查人（关联用户表）
    inspector = models.ForeignKey(
        'system.Users',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspected_workorders',
        db_constraint=False,
        verbose_name='检查人',
        help_text='检查人'
    )
    
    # 包保责任人（关联用户表）
    responsible_person = models.ForeignKey(
        'system.Users',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_workorders',
        db_constraint=False,
        verbose_name='包保责任人',
        help_text='包保责任人'
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
        null=True,
        blank=True,
        verbose_name='隐患等级',
        help_text='隐患等级'
    )
    
    # 问题描述
    problem_description = models.TextField(null=True, blank=True, verbose_name='问题描述', help_text='问题描述')
    
    # 整改类别
    RECTIFICATION_CATEGORY_CHOICES = (
        ('immediate', '当场整改'),
        ('deadline', '限期整改'),
        ('transfer', '移交整改'),
    )
    rectification_category = models.CharField(
        max_length=32,
        choices=RECTIFICATION_CATEGORY_CHOICES,
        null=True,
        blank=True,
        verbose_name='整改类别',
        help_text='当场整改、限期整改、移交整改'
    )
    
    # 上报时间（自动记录创建时间）
    report_time = models.DateTimeField(auto_now_add=True, verbose_name='上报时间', help_text='上报时间')
    
    # 截止时间
    deadline = models.DateField(null=True, blank=True, verbose_name='截止时间', help_text='截止时间')
    
    # 工单状态
    STATUS_CHOICES = (
        (0, '待整改'),
        (1, '待复查'),
        (2, '已完成'),
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


class WorkOrderSubmission(CoreModel):
    """
    工单提交记录模型（包括首次提交和复查）
    """
    # 关联工单
    workorder = models.ForeignKey(
        'WorkOrder',
        on_delete=models.CASCADE,
        related_name='submissions',
        db_constraint=False,
        verbose_name='工单',
        help_text='关联的工单'
    )
    
    # 提交时间
    submit_time = models.DateTimeField(auto_now_add=True, verbose_name='提交时间', help_text='提交时间')
    
    # 是否为复查（0=否，1=是）
    is_recheck = models.IntegerField(default=0, choices=[(0, '否'), (1, '是')], verbose_name='是否为复查', help_text='0=否，1=是')
    
    # 是否合格（0=不合格，1=合格）
    is_qualified = models.IntegerField(default=0, choices=[(0, '不合格'), (1, '合格')], verbose_name='是否合格', help_text='0=不合格，1=合格')
    
    # 备注
    remark = models.TextField(null=True, blank=True, verbose_name='备注', help_text='提交备注')
    
    # 提交人（关联用户表）
    submitter = models.ForeignKey(
        'system.Users',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_workorders',
        db_constraint=False,
        verbose_name='提交人',
        help_text='提交人'
    )
    
    class Meta:
        db_table = table_prefix + "workorder_submission"
        verbose_name = "工单提交记录"
        verbose_name_plural = verbose_name
        ordering = ('-submit_time',)
    
    def __str__(self):
        recheck_text = "复查" if self.is_recheck == 1 else "首次提交"
        qualified_text = "合格" if self.is_qualified == 1 else "不合格"
        return f"{self.workorder.workorder_no} - {recheck_text} - {qualified_text} - {self.submit_time}"


class WorkOrderRecheck(CoreModel):
    """
    工单复查记录模型（保留以兼容旧代码，实际使用WorkOrderSubmission）
    """
    # 关联工单
    workorder = models.ForeignKey(
        'WorkOrder',
        on_delete=models.CASCADE,
        related_name='rechecks',
        db_constraint=False,
        verbose_name='工单',
        help_text='关联的工单'
    )
    
    # 复查时间
    recheck_time = models.DateTimeField(auto_now_add=True, verbose_name='复查时间', help_text='复查时间')
    
    # 是否合格（0=不合格，1=合格）
    is_qualified = models.IntegerField(default=0, choices=[(0, '不合格'), (1, '合格')], verbose_name='是否合格', help_text='0=不合格，1=合格')
    
    # 备注
    remark = models.TextField(null=True, blank=True, verbose_name='备注', help_text='复查备注')
    
    # 复查人（关联用户表）
    rechecker = models.ForeignKey(
        'system.Users',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rechecked_workorders',
        db_constraint=False,
        verbose_name='复查人',
        help_text='复查人'
    )
    
    class Meta:
        db_table = table_prefix + "workorder_recheck"
        verbose_name = "工单复查记录"
        verbose_name_plural = verbose_name
        ordering = ('-recheck_time',)
    
    def __str__(self):
        return f"{self.workorder.workorder_no} - {self.get_is_qualified_display()} - {self.recheck_time}"


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
