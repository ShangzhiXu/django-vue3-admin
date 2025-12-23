from datetime import datetime, timedelta, date
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

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
        获取数据大屏统计数据
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
                # 从问题描述中提取关键信息，如果没有则使用隐患等级
                if wo.problem_description:
                    problem = wo.problem_description[:20] if len(wo.problem_description) > 20 else wo.problem_description
                else:
                    # 获取隐患等级显示值
                    hazard_level_display = dict(WorkOrder.HAZARD_LEVEL_CHOICES).get(wo.hazard_level, '未知')
                    problem = f"{hazard_level_display}隐患"
                warning_list.append({
                    'merchant_name': wo.merchant.name,
                    'problem': problem,
                    'workorder_no': wo.workorder_no,
                })
        
        # 4. 人员绩效Top5（按负责的工单数量排序）
        from django.db.models import Count
        
        # 统计每个检查人和包保责任人负责的工单数量
        from django.db.models import Q
        # 统计检查人
        inspector_data = WorkOrder.objects.filter(
            inspector__isnull=False
        ).values('inspector__id', 'inspector__name').annotate(
            workorder_count=Count('id')
        )
        # 统计包保责任人
        responsible_data = WorkOrder.objects.filter(
            responsible_person__isnull=False
        ).values('responsible_person__id', 'responsible_person__name').annotate(
            workorder_count=Count('id')
        )
        
        # 合并统计（按用户ID合并）
        user_performance = {}
        for item in inspector_data:
            user_id = item['inspector__id']
            if user_id not in user_performance:
                user_performance[user_id] = {
                    'name': item['inspector__name'] or '未知',
                    'count': 0
                }
            user_performance[user_id]['count'] += item['workorder_count']
        
        for item in responsible_data:
            user_id = item['responsible_person__id']
            if user_id not in user_performance:
                user_performance[user_id] = {
                    'name': item['responsible_person__name'] or '未知',
                    'count': 0
                }
            user_performance[user_id]['count'] += item['workorder_count']
        
        # 排序并取前5
        performance_list = sorted(
            [{'name': v['name'], 'count': v['count']} for v in user_performance.values()],
            key=lambda x: x['count'],
            reverse=True
        )[:5]
        
        for idx, item in enumerate(performance_list, 1):
            item['rank'] = idx
        
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
            'warnings': warning_list,
            'performance_top5': performance_list,
        }
        
        return DetailResponse(data=data)
