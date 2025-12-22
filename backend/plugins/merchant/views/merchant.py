import io
import json
import os
import zipfile
import qrcode
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse
from rest_framework import serializers
from rest_framework.decorators import action
from urllib.parse import quote

from dvadmin.utils.serializers import CustomModelSerializer
from dvadmin.utils.viewset import CustomModelViewSet
from dvadmin.utils.json_response import DetailResponse
from plugins.merchant.models import Merchant


class MerchantSerializer(CustomModelSerializer):
    """
    商户管理-序列化器
    """
    qr_code_url = serializers.SerializerMethodField(read_only=True)
    
    def get_qr_code_url(self, obj):
        """
        根据merchant_code生成二维码文件URL
        """
        if obj.merchant_code:
            # 生成文件路径：media/qrcode/merchant_qrcode_{merchant_code}.png
            file_path = f'media/qrcode/merchant_qrcode_{obj.merchant_code}.png'
            file_full_path = os.path.join(settings.MEDIA_ROOT, 'qrcode', f'merchant_qrcode_{obj.merchant_code}.png')
            
            # 检查文件是否存在
            if os.path.exists(file_full_path):
                request = self.context.get('request')
                if request:
                    # 返回完整的URL
                    return request.build_absolute_uri(f'/{file_path}')
                return f'/{file_path}'
        return None
    
    class Meta:
        model = Merchant
        fields = "__all__"
        read_only_fields = ["id", "merchant_code"]  # merchant_code由系统自动生成，不允许手动修改


class MerchantExportSerializer(CustomModelSerializer):
    """
    商户管理-导出序列化器
    """
    category_display = serializers.SerializerMethodField(read_only=True)
    
    def get_category_display(self, obj):
        """返回类别的显示值"""
        return obj.get_category_display() if obj.category else None
    
    class Meta:
        model = Merchant
        fields = [
            "name",
            "merchant_code",
            "manager",
            "phone",
            "address",
            "category",
            "category_display",
            "gps_status",
            "description",
            "create_datetime",
            "update_datetime",
        ]
        read_only_fields = ["id"]


class MerchantViewSet(CustomModelViewSet):
    """
    商户管理接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = Merchant.objects.all()
    serializer_class = MerchantSerializer
    filter_fields = ['name', 'manager', 'phone', 'gps_status', 'merchant_code', 'category']
    search_fields = ['name', 'manager', 'phone', 'address', 'merchant_code']
    extra_filter_class = []
    
    # 导出配置
    export_field_label = {
        "name": "商户名称",
        "merchant_code": "商户编码",
        "manager": "负责人",
        "phone": "联系电话",
        "address": "地址",
        "category_display": "类别",
        "gps_status": "GPS状态",
        "description": "描述",
        "create_datetime": "创建时间",
        "update_datetime": "更新时间",
    }
    export_serializer_class = MerchantExportSerializer
    
    @action(methods=['post'], detail=True)
    def generate_qrcode(self, request, pk=None):
        """
        生成商户二维码，保存到media/qrcode/目录
        """
        merchant = self.get_object()
        
        # 确保商户有标识码（如果没有则生成）
        if not merchant.merchant_code:
            merchant.save()
        
        # 二维码内容: JSON结构，包含商户信息（需要转换为字符串）
        qr_content_dict = {
            "merchant_id": merchant.id,
            "merchant_name": merchant.name,
            "merchant_code": merchant.merchant_code,
            "merchant_phone": merchant.phone or "",
            "merchant_address": merchant.address or "",
        }
        qr_content = json.dumps(qr_content_dict, ensure_ascii=False)  # 转换为JSON字符串
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)  # qrcode库需要字符串，不能直接传入字典
        qr.make(fit=True)
        
        # 创建二维码图片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 将图片保存到内存
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # 保存文件到media/qrcode/目录
        file_name = f'merchant_qrcode_{merchant.merchant_code}.png'
        qrcode_dir = os.path.join(settings.MEDIA_ROOT, 'qrcode')
        os.makedirs(qrcode_dir, exist_ok=True)
        
        file_path = os.path.join(qrcode_dir, file_name)
        with open(file_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        # 更新商户的qr_code字段（保存相对路径，用于标识）
        merchant.qr_code = f'qrcode/{file_name}'
        merchant.save(update_fields=['qr_code'])
        
        # 返回文件信息（包含qr_code_url）
        serializer = MerchantSerializer(merchant, context={'request': request})
        return DetailResponse(data=serializer.data, msg="二维码生成成功")
    
    def _generate_single_qrcode(self, merchant):
        """
        生成单个商户的二维码（内部方法，用于批量生成）
        """
        # 确保商户有标识码（如果没有则生成）
        if not merchant.merchant_code:
            merchant.save()
        
        # 二维码内容: JSON结构，包含商户信息
        qr_content_dict = {
            "merchant_id": merchant.id,
            "merchant_name": merchant.name,
            "merchant_code": merchant.merchant_code,
            "merchant_phone": merchant.phone or "",
            "merchant_address": merchant.address or "",
        }
        qr_content = json.dumps(qr_content_dict, ensure_ascii=False)
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        # 创建二维码图片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 将图片保存到内存
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # 保存文件到media/qrcode/目录
        file_name = f'merchant_qrcode_{merchant.merchant_code}.png'
        qrcode_dir = os.path.join(settings.MEDIA_ROOT, 'qrcode')
        os.makedirs(qrcode_dir, exist_ok=True)
        
        file_path = os.path.join(qrcode_dir, file_name)
        with open(file_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        # 更新商户的qr_code字段
        merchant.qr_code = f'qrcode/{file_name}'
        merchant.save(update_fields=['qr_code'])
        
        return file_path, file_name
    
    @action(methods=['post'], detail=False)
    def batch_generate_qrcode(self, request):
        """
        批量生成二维码（默认生成全部）
        """
        ids = request.data.get('ids', [])
        
        # 如果没有传入ids，则处理全部商户
        if ids:
            merchants = Merchant.objects.filter(id__in=ids)
        else:
            merchants = Merchant.objects.all()
        
        success_count = 0
        failed_count = 0
        
        for merchant in merchants:
            try:
                self._generate_single_qrcode(merchant)
                success_count += 1
            except Exception as e:
                failed_count += 1
                continue
        
        msg = f"成功生成 {success_count} 个二维码"
        if failed_count > 0:
            msg += f"，失败 {failed_count} 个"
        
        return DetailResponse(data={'success_count': success_count, 'failed_count': failed_count}, msg=msg)
    
    @action(methods=['post'], detail=False)
    def batch_export_qrcode(self, request):
        """
        批量导出二维码（打包成zip文件，默认导出全部）
        """
        ids = request.data.get('ids', [])
        
        # 如果没有传入ids，则处理全部商户
        if ids:
            merchants = Merchant.objects.filter(id__in=ids).filter(merchant_code__isnull=False)
        else:
            merchants = Merchant.objects.filter(merchant_code__isnull=False)
        
        # 创建zip文件
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            added_count = 0
            for merchant in merchants:
                if merchant.merchant_code:
                    file_name = f'merchant_qrcode_{merchant.merchant_code}.png'
                    file_path = os.path.join(settings.MEDIA_ROOT, 'qrcode', file_name)
                    
                    if os.path.exists(file_path):
                        # 读取文件并添加到zip
                        with open(file_path, 'rb') as f:
                            # 使用商户名称作为zip内的文件名（避免重复）
                            zip_name = f'{merchant.name}_{file_name}'
                            zip_file.writestr(zip_name, f.read())
                            added_count += 1
        
        if added_count == 0:
            return DetailResponse(msg="没有找到可导出的二维码文件", code=400)
        
        # 准备响应
        zip_buffer.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f'商户二维码_{timestamp}.zip'
        
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename.encode("utf-8"))}'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        return response
