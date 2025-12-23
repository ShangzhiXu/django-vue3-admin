import os
import traceback
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from plugins.workorder.models import WorkOrder, WorkOrderRecheck


class MobileWorkOrderRechecksView(APIView):
    """
    获取工单复查记录列表
    访问示例: GET /api/mobile/workorders/{workorderNo}/rechecks
    """
    permission_classes = [AllowAny]  # 允许匿名访问
    renderer_classes = [JSONRenderer]  # 只返回JSON格式

    def get(self, request, workorder_no):
        """
        获取工单复查记录列表
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

            # 获取所有复查记录
            rechecks = WorkOrderRecheck.objects.filter(workorder=workorder).order_by('-recheck_time')
            
            recheck_list = []
            for recheck in rechecks:
                # 获取该次复查的图片
                recheck_photo_dir = os.path.join(settings.MEDIA_ROOT, 'workorders', workorder_no, 'rechecks')
                photos = []
                
                if os.path.exists(recheck_photo_dir):
                    # 根据复查时间匹配图片（简化处理：获取该目录下所有图片）
                    files = sorted(os.listdir(recheck_photo_dir))
                    for filename in files:
                        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            # 检查文件名是否包含复查时间戳（简化处理）
                            relative_path = f'workorders/{workorder_no}/rechecks/{filename}'
                            photos.append({
                                'filename': filename,
                                'url': f'/media/{relative_path}',
                                'path': relative_path
                            })
                
                recheck_list.append({
                    'id': recheck.id,
                    'recheck_time': recheck.recheck_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'is_qualified': recheck.is_qualified,
                    'is_qualified_display': '合格' if recheck.is_qualified == 1 else '不合格',
                    'remark': recheck.remark,
                    'photos': photos,
                    'photos_count': len(photos)
                })

            return Response({
                "code": 2000,
                "data": {
                    "workorder_id": workorder.id,
                    "workorder_no": workorder.workorder_no,
                    "rechecks": recheck_list,
                    "count": len(recheck_list)
                },
                "msg": "查询成功"
            }, content_type='application/json')

        except Exception as e:
            print("=" * 80)
            print(f"获取工单复查记录时发生错误:")
            print(f"  错误信息: {str(e)}")
            traceback.print_exc()
            print("=" * 80)

            return Response({
                "code": 500,
                "data": {},
                "msg": f"服务器错误: {str(e)}",
            }, status=500, content_type='application/json')

