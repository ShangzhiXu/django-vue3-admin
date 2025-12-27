from datetime import datetime, timedelta, date
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from collections import defaultdict

from dvadmin.utils.json_response import DetailResponse
from plugins.merchant.models import Merchant
from plugins.workorder.models import WorkOrder
from plugins.task.models import Task
from dvadmin.system.models import Users


class HomeViewSet(ViewSet):
    """
    首页数据接口
    """
    
    @action(methods=['get'], detail=False)
    def statistics(self, request):
        """
        获取首页统计数据
        """
        today = date.today()
        this_month_start = today.replace(day=1)
        last_week_start = today - timedelta(days=7)
        
        # 1. 总商户数
        total_merchants = Merchant.objects.count()
        
        # 2. 今日检查完成率
        # 今日创建且状态为待复查或已完成的工单数
        # 注意：completed_time 可能为 null，所以需要先过滤掉 null 值
        today_completed_workorders = WorkOrder.objects.filter(
            Q(create_datetime__date=today, status__in=[1, 2]) |  # 今日创建且待复查/已完成
            Q(completed_time__isnull=False, completed_time__date=today, status=2)  # 或今日完成的工单（不管什么时候创建）
        ).distinct().count()
        total_today_workorders = WorkOrder.objects.filter(create_datetime__date=today).count()
        today_completion_rate = (today_completed_workorders / total_today_workorders * 100) if total_today_workorders > 0 else 0
        
        # 3. 待整改隐患数（工单状态为待整改）
        pending_workorders = WorkOrder.objects.filter(status=0).count()
        
        # 4. 本月活跃巡检员数（本月有创建工单或任务的用户，或者有负责的任务）
        # 获取本月有活动的用户（创建了工单或任务，或者是任务负责人）
        active_user_ids = set()
        # 本月创建的任务负责人
        active_user_ids.update(
            Task.objects.filter(create_datetime__gte=this_month_start)
            .exclude(manager__isnull=True)
            .values_list('manager_id', flat=True)
        )
        # 本月创建的工单的检查人和包保责任人
        active_user_ids.update(
            WorkOrder.objects.filter(create_datetime__gte=this_month_start)
            .exclude(inspector__isnull=True)
            .values_list('inspector_id', flat=True)
        )
        active_user_ids.update(
            WorkOrder.objects.filter(create_datetime__gte=this_month_start)
            .exclude(responsible_person__isnull=True)
            .values_list('responsible_person_id', flat=True)
        )
        active_users = len(active_user_ids) if active_user_ids else 0
        
        # 5. 近7日检查趋势（每日工单数量）
        chart_data = []
        chart_labels = []
        for i in range(6, -1, -1):  # 从6天前到今天
            check_date = today - timedelta(days=i)
            count = WorkOrder.objects.filter(
                create_datetime__date=check_date
            ).count()
            chart_data.append(count)
            # 格式化日期标签
            if i == 0:
                chart_labels.append('今天')
            elif i == 1:
                chart_labels.append('昨天')
            else:
                chart_labels.append(check_date.strftime('%m-%d'))
        
        # 6. 最新动态（最近10条工单记录）
        latest_workorders = WorkOrder.objects.select_related('merchant', 'task').order_by('-create_datetime')[:10]
        latest_updates = []
        for wo in latest_workorders:
            if wo.merchant:
                update_text = f"工单 {wo.workorder_no} - {wo.merchant.name} 状态: {wo.get_status_display()}"
                latest_updates.append(update_text)
        
        # 计算趋势（较上周）
        last_week_merchants = Merchant.objects.filter(
            create_datetime__date__gte=last_week_start,
            create_datetime__date__lt=today
        ).count()
        merchant_trend = ((total_merchants - last_week_merchants) / last_week_merchants * 100) if last_week_merchants > 0 else 0
        
        # 计算今日完成率环比（与昨天比较）
        yesterday = today - timedelta(days=1)
        yesterday_completed_workorders = WorkOrder.objects.filter(
            Q(create_datetime__date=yesterday, status__in=[1, 2]) |  # 昨日创建且待复查/已完成
            Q(completed_time__isnull=False, completed_time__date=yesterday, status=2)  # 或昨日完成的工单（不管什么时候创建）
        ).distinct().count()
        total_yesterday_workorders = WorkOrder.objects.filter(create_datetime__date=yesterday).count()
        yesterday_completion_rate = (yesterday_completed_workorders / total_yesterday_workorders * 100) if total_yesterday_workorders > 0 else 0
        completion_trend = today_completion_rate - yesterday_completion_rate
        
        # 计算待整改新增（今日新增的待整改工单）
        today_pending = WorkOrder.objects.filter(
            status=0,
            create_datetime__date=today
        ).count()
        
        data = {
            'total_merchants': total_merchants,
            'merchant_trend': round(merchant_trend, 1),
            'today_completion_rate': round(today_completion_rate, 1),
            'completion_trend': round(completion_trend, 1),
            'pending_workorders': pending_workorders,
            'today_pending': today_pending,
            'active_users': active_users,
            'chart_data': {
                'labels': chart_labels,
                'data': chart_data,
            },
            'latest_updates': latest_updates,
        }
        
        return DetailResponse(data=data)
    
    @action(methods=['get'], detail=False)
    def dashboard(self, request):
        """
        获取数据中心统计数据
        """
        today = date.today()
        
        # 1. 今日概览
        # 计划检查：今日创建的任务数
        planned_checks = Task.objects.filter(start_time__date=today).count()
        
        # 已完成：今日创建且状态为待复查或已完成的工单，或今日完成的工单
        # 注意：completed_time 可能为 null，所以需要先过滤掉 null 值
        completed_checks = WorkOrder.objects.filter(
            Q(create_datetime__date=today, status__in=[1, 2]) |  # 今日创建且待复查/已完成
            Q(completed_time__isnull=False, completed_time__date=today, status=2)  # 或今日完成的工单（不管什么时候创建）
        ).distinct().count()
        
        # 发现隐患：今日创建的工单数（有隐患等级）
        found_hazards = WorkOrder.objects.filter(
            create_datetime__date=today
        ).exclude(hazard_level__isnull=True).count()
        
        # 2. 问题类型分布（根据工单的检查类别分类）
        # 消防类
        fire_count = WorkOrder.objects.filter(
            check_category='fire'
        ).count()
        
        # 燃气类
        gas_count = WorkOrder.objects.filter(
            check_category='gas'
        ).count()
        
        # 安全管理类
        safety_count = WorkOrder.objects.filter(
            check_category='safety_manage'
        ).count()
        
        # 液体燃料类
        liquid_fuel_count = WorkOrder.objects.filter(
            check_category='liquid_fuel'
        ).count()
        
        # 其他（未分类的）
        other_count = WorkOrder.objects.filter(
            check_category__isnull=True
        ).count()
        
        # 3. 实时预警动态（待整改的工单，按创建时间倒序）
        warnings = WorkOrder.objects.filter(
            status=0  # 待整改
        ).select_related('merchant').order_by('-create_datetime')[:10]
        
        warning_list = []
        for wo in warnings:
            if wo.merchant:
                # 始终显示检查类别（问题类别）
                if wo.check_category:
                    # 获取检查类别显示值
                    category_display = dict(WorkOrder.CHECK_CATEGORY_CHOICES).get(wo.check_category, '未知')
                    problem = category_display
                else:
                    # 如果没有检查类别，显示"未分类"
                    problem = '未分类'
                warning_list.append({
                    'merchant_name': wo.merchant.name,
                    'problem': problem,
                    'workorder_no': wo.workorder_no,
                })
        
        # 4. 人员绩效Top5（按被督办的工单数量排序，显示包保责任人）
        # 统计每个包保责任人被督办的工单数量
        supervised_data = WorkOrder.objects.filter(
            responsible_person__isnull=False,
            is_supervised=True
        ).values('responsible_person__id', 'responsible_person__name').annotate(
            supervised_count=Count('id')
        )
        
        # 排序并取前5
        performance_list = sorted(
            [{'name': item['responsible_person__name'] or '未知', 'count': item['supervised_count']} for item in supervised_data],
            key=lambda x: x['count'],
            reverse=True
        )[:5]
        
        for idx, item in enumerate(performance_list, 1):
            item['rank'] = idx
        
        # 5. 移交总数
        transfer_total = WorkOrder.objects.filter(is_transferred=True).count()
        
        # 6. 场所分类统计（饼图数据）
        category_map = dict(Merchant.CATEGORY_CHOICES)
        category_stats = defaultdict(int)
        
        # 统计每个场所类别的商户数量
        merchant_categories = Merchant.objects.values('category').annotate(count=Count('id'))
        for item in merchant_categories:
            category_id = item['category']
            category_name = category_map.get(category_id, f'类别{category_id}')
            category_stats[category_name] = item['count']
        
        # 转换为列表格式，用于饼图
        category_pie_data = [
            {'name': name, 'value': count}
            for name, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # 7. 问题类别柱状图数据（已有数据，转换为列表格式）
        problem_bar_data = [
            {'name': '消防类', 'value': fire_count},
            {'name': '燃气类', 'value': gas_count},
            {'name': '安全管理类', 'value': safety_count},
            {'name': '液体燃料类', 'value': liquid_fuel_count},
            {'name': '其他', 'value': other_count},
        ]
        
        # 8. 隐患热力图数据（每个商户一个点，隐患越多颜色越深）
        # 按商户统计隐患数量
        merchant_hazards = WorkOrder.objects.filter(
            hazard_level__isnull=False,
            merchant__isnull=False,
            merchant__gps_status__isnull=False
        ).values(
            'merchant__id',
            'merchant__name',
            'merchant__gps_status'
        ).annotate(
            hazard_count=Count('id')
        )
        
        heatmap_points = []
        for merchant in merchant_hazards:
            gps_str = merchant['merchant__gps_status']
            if gps_str:
                # GPS格式可能是 "经度,纬度" 或 "-37,145"
                try:
                    parts = gps_str.split(',')
                    if len(parts) == 2:
                        lng = float(parts[0].strip())
                        lat = float(parts[1].strip())
                        hazard_count = merchant['hazard_count']
                        heatmap_points.append({
                            'lng': lng,
                            'lat': lat,
                            'hazard_count': hazard_count,
                            'merchant_name': merchant['merchant__name'],
                        })
                except (ValueError, IndexError):
                    continue
        
        data = {
            'today_overview': {
                'planned_checks': planned_checks,
                'completed_checks': completed_checks,
                'found_hazards': found_hazards,
            },
            'problem_distribution': {
                'fire': fire_count,
                'gas': gas_count,
                'safety': safety_count,
                'liquid_fuel': liquid_fuel_count,
                'other': other_count,
            },
            'problem_bar_data': problem_bar_data,  # 柱状图数据
            'warnings': warning_list,
            'performance_top5': performance_list,
            'transfer_total': transfer_total,  # 移交总数
            'category_pie_data': category_pie_data,  # 场所分类饼图数据
            'heatmap_points': heatmap_points,  # 隐患热力图点位数据
        }
        
        return DetailResponse(data=data)
