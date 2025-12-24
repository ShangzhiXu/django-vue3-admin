import os
import traceback
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from plugins.workorder.models import WorkOrder


class MobileWorkOrderPhotosView(APIView):
    """
    获取工单完成时的照片列表
    访问示例: GET /api/mobile/workorders/{workorderNo}/photos/list
    """
    permission_classes = [AllowAny]  # 允许匿名访问
    renderer_classes = [JSONRenderer]  # 只返回JSON格式
    
    def get(self, request, workorder_no):
        """
        获取工单完成时的照片列表
        """
        try:
            # 只通过工单号查询工单对象
            try:
                workorder = WorkOrder.objects.get(workorder_no=workorder_no)
            except WorkOrder.DoesNotExist:
                workorder = None
            
            if not workorder:
                return Response({
                    "code": 404,
                    "data": {},
                    "msg": f"工单 {workorder_no} 不存在"
                }, status=404, content_type='application/json')
            
            # 获取工单完成时的照片目录
            workorder_photo_dir = os.path.join(settings.MEDIA_ROOT, 'workorders', workorder_no, 'completed')
            
            # 获取所有图片文件
            photos = []
            if os.path.exists(workorder_photo_dir):
                files = sorted(os.listdir(workorder_photo_dir))
                for filename in files:
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        relative_path = f'workorders/{workorder_no}/completed/{filename}'
                        photos.append({
                            'filename': filename,
                            'url': f'/media/{relative_path}',
                            'path': relative_path
                        })
            
            return Response({
                "code": 2000,
                "data": {
                    "workorder_id": workorder.id,
                    "workorder_no": workorder.workorder_no,
                    "photos": photos,
                    "count": len(photos)
                },
                "msg": "查询成功"
            }, content_type='application/json')
            
        except Exception as e:
            print("=" * 80)
            print(f"获取工单照片时发生错误:")
            print(f"  错误信息: {str(e)}")
            traceback.print_exc()
            print("=" * 80)
            
            return Response({
                "code": 500,
                "data": {},
                "msg": f"服务器错误: {str(e)}"
            }, status=500, content_type='application/json')




