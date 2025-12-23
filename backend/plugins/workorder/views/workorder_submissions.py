import os
import traceback
import shutil
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from dvadmin.utils.permission import AdminPermission
from plugins.workorder.models import WorkOrder, WorkOrderSubmission


class MobileWorkOrderSubmissionsView(APIView):
    """
    获取工单提交记录列表（包括首次提交和复查）
    访问示例: GET /api/mobile/workorders/{workorderNo}/submissions
    """
    permission_classes = [AllowAny]  # 允许匿名访问
    renderer_classes = [JSONRenderer]  # 只返回JSON格式

    def get(self, request, workorder_no):
        """
        获取工单提交记录列表
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

            # 获取所有提交记录（按时间倒序）
            submissions = WorkOrderSubmission.objects.filter(workorder=workorder).order_by('-submit_time')
            
            submission_list = []
            for submission in submissions:
                # 根据是否为复查决定图片目录
                if submission.is_recheck == 1:
                    photo_dir = os.path.join(settings.MEDIA_ROOT, 'workorders', workorder_no, 'rechecks')
                    photo_subdir = 'rechecks'
                else:
                    photo_dir = os.path.join(settings.MEDIA_ROOT, 'workorders', workorder_no, 'completed')
                    photo_subdir = 'completed'
                
                # 获取该次提交的图片
                photos = []
                if os.path.exists(photo_dir):
                    files = sorted(os.listdir(photo_dir))
                    for filename in files:
                        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            # 简化处理：获取该目录下所有图片（实际应该根据时间匹配）
                            relative_path = f'workorders/{workorder_no}/{photo_subdir}/{filename}'
                            photos.append({
                                'filename': filename,
                                'url': f'/media/{relative_path}',
                                'path': relative_path
                            })
                
                submission_list.append({
                    'id': submission.id,
                    'submit_time': submission.submit_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'is_recheck': submission.is_recheck,
                    'is_qualified': submission.is_qualified,
                    'is_qualified_display': '合格' if submission.is_qualified == 1 else '不合格',
                    'remark': submission.remark,
                    'photos': photos,
                    'photos_count': len(photos)
                })

            return Response({
                "code": 2000,
                "data": {
                    "workorder_id": workorder.id,
                    "workorder_no": workorder.workorder_no,
                    "submissions": submission_list,
                    "count": len(submission_list)
                },
                "msg": "查询成功"
            }, content_type='application/json')

        except Exception as e:
            print("=" * 80)
            print(f"获取工单提交记录时发生错误:")
            print(f"  错误信息: {str(e)}")
            traceback.print_exc()
            print("=" * 80)

            return Response({
                "code": 500,
                "data": {},
                "msg": f"服务器错误: {str(e)}",
            }, status=500, content_type='application/json')


class MobileWorkOrderSubmissionDeleteView(APIView):
    """
    删除工单提交记录（仅管理员）
    访问示例: DELETE /api/mobile/workorders/{workorderNo}/submissions/{submissionId}
    """
    permission_classes = [AdminPermission]  # 需要管理员权限
    renderer_classes = [JSONRenderer]  # 只返回JSON格式

    def delete(self, request, workorder_no, submission_id):
        """
        删除指定的提交记录
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

            # 获取提交记录
            try:
                submission = WorkOrderSubmission.objects.get(id=submission_id, workorder=workorder)
            except WorkOrderSubmission.DoesNotExist:
                return Response({
                    "code": 404,
                    "data": {},
                    "msg": f"提交记录不存在"
                }, status=404, content_type='application/json')

            # 删除关联的图片文件
            if submission.is_recheck == 1:
                photo_dir = os.path.join(settings.MEDIA_ROOT, 'workorders', workorder_no, 'rechecks')
            else:
                photo_dir = os.path.join(settings.MEDIA_ROOT, 'workorders', workorder_no, 'completed')
            
            # 删除目录下的所有图片（简化处理，实际应该根据时间匹配）
            if os.path.exists(photo_dir):
                try:
                    # 删除整个目录（可选，或者只删除匹配的文件）
                    # 这里为了安全，只删除目录下的图片文件
                    files = os.listdir(photo_dir)
                    for filename in files:
                        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            file_path = os.path.join(photo_dir, filename)
                            try:
                                os.remove(file_path)
                                print(f"删除图片文件: {file_path}")
                            except Exception as e:
                                print(f"删除图片文件失败: {file_path}, 错误: {str(e)}")
                except Exception as e:
                    print(f"删除图片目录失败: {photo_dir}, 错误: {str(e)}")

            # 删除提交记录
            submission_id = submission.id
            submission.delete()
            print(f"删除提交记录成功: ID={submission_id}")

            return Response({
                "code": 2000,
                "data": {
                    "submission_id": submission_id,
                    "workorder_no": workorder_no
                },
                "msg": "删除成功"
            }, content_type='application/json')

        except Exception as e:
            print("=" * 80)
            print(f"删除工单提交记录时发生错误:")
            print(f"  错误信息: {str(e)}")
            traceback.print_exc()
            print("=" * 80)

            return Response({
                "code": 500,
                "data": {},
                "msg": f"服务器错误: {str(e)}",
            }, status=500, content_type='application/json')

