from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from dvadmin.system.models import Users


def recursion(instance, parent, result):
    """递归获取部门路径"""
    new_instance = getattr(instance, parent, None)
    res = []
    data = getattr(instance, result, None)
    if data:
        res.append(data)
    if new_instance:
        array = recursion(new_instance, parent, result)
        res += array
    return res


class MobileStatisticsView(APIView):
    """
    移动端用户统计信息接口
    访问示例: GET /api/mobile/statistics?phone=15203936797
    """
    permission_classes = [AllowAny]  # 允许匿名访问
    renderer_classes = [JSONRenderer]  # 只返回JSON格式

    def get(self, request):
        """
        获取用户统计信息
        参数:
            phone: 手机号
        """
        try:
            phone = request.query_params.get('phone', '')
            
            if not phone:
                return Response({
                    "code": 400,
                    "data": {},
                    "msg": "手机号不能为空"
                }, status=400, content_type='application/json')
            
            # 根据手机号查找用户
            try:
                user = Users.objects.select_related('dept').prefetch_related('role', 'post').get(mobile=phone)
            except Users.DoesNotExist:
                return Response({
                    "code": 404,
                    "data": {},
                    "msg": f"未找到手机号为 {phone} 的用户"
                }, status=404, content_type='application/json')
            
            # 获取部门完整路径
            dept_full_path = None
            if user.dept:
                dept_name_all = recursion(user.dept, "parent", "name")
                dept_name_all.reverse()
                dept_full_path = "/".join(dept_name_all) if dept_name_all else user.dept.name
            
            # 构建返回数据
            data = {
                "user_id": user.id,
                "username": user.username,
                "name": user.name,
                "mobile": user.mobile,
                "email": user.email if user.email else None,
                "avatar": user.avatar if user.avatar else None,
                "gender": user.gender if user.gender is not None else 0,
                "gender_text": dict(user.GENDER_CHOICES).get(user.gender, "未知") if user.gender is not None else "未知",
                "dept": {
                    "id": user.dept.id if user.dept else None,
                    "name": user.dept.name if user.dept else None,
                    "full_path": dept_full_path,
                } if user.dept else None,
                "roles": [
                    {
                        "id": role.id,
                        "name": role.name,
                    }
                    for role in user.role.all()
                ],
                "posts": [
                    {
                        "id": post.id,
                        "name": post.name,
                    }
                    for post in user.post.all()
                ],
            }
            
            return Response({
                "code": 2000,
                "data": data,
                "msg": "查询成功"
            }, content_type='application/json')
            
        except Exception as e:
            return Response({
                "code": 500,
                "data": {},
                "msg": f"服务器错误: {str(e)}",
            }, status=500, content_type='application/json')


