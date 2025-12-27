from django.db import models
from dvadmin.utils.models import CoreModel

table_prefix = "task_"


class Task(CoreModel):
    """
    任务中心模型
    """
    # 任务名称
    name = models.CharField(max_length=255, verbose_name='任务名称', help_text='任务名称')
    
    # 负责人（关联用户表）
    manager = models.ForeignKey(
        'system.Users',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_tasks',
        db_constraint=False,
        verbose_name='负责人',
        help_text='任务负责人'
    )
    
    # 周期
    CYCLE_CHOICES = (
        ('once', '不重复'),
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('yearly', '每年'),
        ('custom', '自定义'),
    )
    cycle = models.CharField(
        max_length=20,
        choices=CYCLE_CHOICES,
        default='once',
        null=True,
        blank=True,
        verbose_name='周期',
        help_text='任务周期'
    )
    
    # 时间范围
    start_time = models.DateTimeField(verbose_name='开始时间', help_text='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间', help_text='结束时间')
    
    # 关联商户（多对多关系）
    merchants = models.ManyToManyField(
        'merchant.Merchant',
        related_name='tasks',
        db_constraint=False,
        blank=True,
        verbose_name='覆盖商户',
        help_text='任务覆盖的商户列表'
    )
    
    # 检查项（多个用逗号分隔）
    check_items = models.TextField(null=True, blank=True, verbose_name='检查项', help_text='检查项，多个用逗号分隔')
    
    # 任务状态
    STATUS_CHOICES = (
        (0, '待执行'),
        (1, '执行中'),
        (2, '已完成'),
        (3, '已暂停'),
        (4, '已取消'),
    )
    status = models.IntegerField(default=0, choices=STATUS_CHOICES, db_index=True, verbose_name='状态', help_text='任务状态')
    
    # 备注
    remark = models.TextField(null=True, blank=True, verbose_name='备注', help_text='备注')

    class Meta:
        db_table = table_prefix + "task"
        verbose_name = "任务中心"
        verbose_name_plural = verbose_name
        ordering = ('-create_datetime',)
    
    def __str__(self):
        return f"{self.name} - {self.get_cycle_display()}"
