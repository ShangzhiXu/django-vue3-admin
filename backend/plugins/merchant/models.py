import hashlib
from django.db import models
from dvadmin.utils.models import CoreModel

table_prefix = "merchant_"


class Merchant(CoreModel):
    """
    商户管理模型
    """
    name = models.CharField(max_length=255, verbose_name='商户名称', help_text='商户名称')
    manager = models.CharField(max_length=100, null=True, blank=True, verbose_name='负责人', help_text='负责人')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='联系电话', help_text='联系电话')
    address = models.TextField(null=True, blank=True, verbose_name='地址', help_text='地址')
    
    # GPS 状态改为可存任意字符串，例如经纬度 "-37,145"
    gps_status = models.CharField(max_length=64, null=True, blank=True, verbose_name='GPS', help_text='GPS 信息，如经纬度字符串')

    # 场所类别
    CATEGORY_CHOICES = (
        (1, '大型商超'),
        (2, '商业综合体'),
        (3, '大型餐饮饭店'),
        (4, '大型宾馆'),
        (5, '大型洗浴'),
        (6, '成品油市场'),
        (7, '再生资源回收利用'),
        (8, '新车，二手车销售'),
        (9, '洗车服务（不包括“汽车修理与维护”）'),
        (10, '托管班、“小饭桌”、自习室等校外托管服务场所（不包含课余辅导、教育培训）'),
        (11, '九小场所（小超市、小饭馆、小旅店、小美容洗浴）'),
        (12, '拍卖'),
        (13, '旧货流通'),
        (14, '报废机动车回收'),
        (15, '摄影服务（婚纱摄影）'),
        (16, '家用电器修理'),
        (17, '其他'),
    )
    category = models.IntegerField(
        default=17, 
        choices=CATEGORY_CHOICES, 
        verbose_name='场所类别', 
        help_text='场所类别'
    )
    
    # 商户唯一标识码（根据商户信息自动生成）
    merchant_code = models.CharField(
        max_length=32, 
        unique=True, 
        db_index=True, 
        null=True, 
        blank=True,
        verbose_name='商户标识码', 
        help_text='根据商户名称、负责人、联系电话、地址自动生成的唯一标识码'
    )
    
    # 二维码存储文件ID，通过序列化器返回完整URL
    qr_code = models.CharField(max_length=500, null=True, blank=True, verbose_name='二维码', help_text='二维码图片文件ID或URL')

    def _generate_merchant_code(self):
        """
        根据商户信息生成唯一标识码
        使用MD5哈希算法，取前16位作为标识码
        """
        # 组合商户信息（去除空格并转为小写，确保一致性）
        info_parts = [
            (self.name or '').strip().lower(),
            (self.manager or '').strip().lower(),
            (self.phone or '').strip().lower(),
            (self.address or '').strip().lower(),
        ]
        info_string = '|'.join(info_parts)
        
        # 使用MD5生成哈希值
        md5 = hashlib.md5()
        md5.update(info_string.encode('utf-8'))
        hash_value = md5.hexdigest()
        
        # 取前16位作为标识码
        code = hash_value[:16]
        
        # 检查是否已存在，如果存在则添加后缀
        base_code = code
        suffix = 0
        while Merchant.objects.filter(merchant_code=code).exclude(pk=self.pk if self.pk else None).exists():
            suffix += 1
            # 使用后8位 + 后缀数字（最多2位）确保唯一
            code = f"{base_code[:14]}{suffix:02d}"
            if suffix >= 99:  # 防止无限循环
                # 如果还是重复，使用完整哈希值
                code = hash_value[:16]
                break
        
        return code
    
    def save(self, *args, **kwargs):
        """
        保存时自动生成商户标识码
        """
        # 如果merchant_code为空或者是新建对象，则生成新的code
        if not self.merchant_code:
            self.merchant_code = self._generate_merchant_code()
        super().save(*args, **kwargs)

    class Meta:
        db_table = table_prefix + "merchant"
        verbose_name = "商户管理"
        verbose_name_plural = verbose_name
        ordering = ('-create_datetime',)
