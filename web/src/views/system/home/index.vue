<template>
	<div class="home-container">
		<!-- 顶部问候区域 -->
		<div class="top-section">
			<div class="greeting-section">
				<div class="greeting">
					<span class="greeting-text">{{ greeting }}</span>
					<span class="greeting-emoji">👋</span>
				</div>
				<div class="status-message">今天也是元气满满的一天, 目前系统运行平稳。</div>
			</div>
			<div class="action-section">
				<el-button type="primary" size="large" :icon="Plus" @click="handleStartInspection">
					发起检查任务
				</el-button>
			</div>
		</div>

		<!-- 指标卡片区域 -->
		<div class="metrics-section">
			<div class="metric-card">
				<div class="metric-icon building-icon">🏢</div>
				<div class="metric-content">
					<div class="metric-value">{{ statistics.total_merchants || 0 }}</div>
					<div class="metric-label">总商户数</div>
					<div class="metric-trend" :class="statistics.merchant_trend >= 0 ? 'up' : 'down'">
						{{ statistics.merchant_trend >= 0 ? '↑' : '↓' }}{{ Math.abs(statistics.merchant_trend || 0).toFixed(1) }}% 较上周
					</div>
				</div>
				<div class="metric-bg-text">24H</div>
			</div>

			<div class="metric-card">
				<div class="metric-icon success-icon">✓</div>
				<div class="metric-content">
					<div class="metric-value">{{ statistics.today_completion_rate || 0 }}%</div>
					<div class="metric-label">今日检查完成率</div>
					<div class="metric-trend" :class="statistics.completion_trend >= 0 ? 'up' : 'down'">
						{{ statistics.completion_trend >= 0 ? '↑' : '↓' }}{{ Math.abs(statistics.completion_trend || 0).toFixed(1) }}% 环比
					</div>
				</div>
			</div>

			<div class="metric-card">
				<div class="metric-icon warning-icon">🔥</div>
				<div class="metric-content">
					<div class="metric-value">{{ statistics.pending_workorders || 0 }}</div>
					<div class="metric-label">待整改隐患</div>
					<div class="metric-trend" :class="statistics.today_pending > 0 ? 'up' : 'flat'">
						{{ statistics.today_pending > 0 ? `↑${statistics.today_pending} 新增` : '-- 持平' }}
					</div>
				</div>
			</div>

			<div class="metric-card">
				<div class="metric-icon people-icon">👥</div>
				<div class="metric-content">
					<div class="metric-value">{{ statistics.active_users || 0 }}</div>
					<div class="metric-label">本月活跃巡检员</div>
					<div class="metric-trend flat">-- 持平</div>
				</div>
			</div>
		</div>

		<!-- 中间内容区域 -->
		<div class="content-section">
			<!-- 左侧：检查趋势图表 -->
			<div class="left-content">
				<div class="chart-card">
					<div class="card-header">
						<div class="card-title">
							<SvgIcon name="ele-DataAnalysis" :size="18" />
							<span>近7日检查趋势</span>
						</div>
						<div class="chart-filters">
							<el-button 
								v-for="filter in chartFilters" 
								:key="filter.value"
								:type="activeFilter === filter.value ? 'primary' : 'default'"
								size="small"
								@click="activeFilter = filter.value"
							>
								{{ filter.label }}
							</el-button>
						</div>
					</div>
					<div ref="chartRef" class="chart-container"></div>
				</div>
			</div>

			<!-- 右侧：快捷操作和最新动态 -->
			<div class="right-content">
				<!-- 快捷操作 -->
				<div class="quick-actions-card">
					<div class="card-header">
						<div class="card-title">
							<SvgIcon name="ele-Operation" :size="18" />
							<span>快捷操作</span>
						</div>
					</div>
					<div class="quick-actions-list">
						<div 
							v-for="action in quickActions" 
							:key="action.id"
							class="quick-action-item"
							@click="handleQuickAction(action)"
						>
							<SvgIcon :name="action.icon" class="action-icon" :size="20" />
							<span class="action-text">{{ action.label }}</span>
						</div>
					</div>
				</div>

				<!-- 最新动态 -->
				<div class="updates-card">
					<div class="card-header">
						<div class="card-title">
							<SvgIcon name="ele-Bell" :size="18" />
							<span>最新动态</span>
						</div>
					</div>
					<div class="updates-list">
						<div 
							v-for="(update, index) in latestUpdates" 
							:key="index"
							class="update-item"
						>
							<div class="update-dot"></div>
							<div class="update-content">{{ update }}</div>
						</div>
						<div v-if="latestUpdates.length === 0" class="update-item">
							<div class="update-content" style="color: #909399;">暂无最新动态</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts" setup name="home">
import { ref, onMounted, onUnmounted, onActivated, computed, watch, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import * as echarts from 'echarts';
import { Plus, BarChart, Lightning, Bell, OfficeBuilding, DocumentChecked, User } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { GetStatistics } from './api';

const router = useRouter();
const route = useRoute();

// 问候语
const greeting = computed(() => {
	const hour = new Date().getHours();
	if (hour < 12) return '上午好, 管理员';
	if (hour < 18) return '下午好, 管理员';
	return '晚上好, 管理员';
});

// 图表相关
const chartRef = ref<HTMLElement>();
let chartInstance: echarts.ECharts | null = null;
const activeFilter = ref('all');
const chartFilters = [
	{ label: '全部', value: 'all' },
	{ label: '消防', value: 'fire' },
	{ label: '卫生', value: 'hygiene' },
];

// 快捷操作
const quickActions = [
	{ id: 1, label: '新增商户录入', icon: OfficeBuilding, route: '/merchant' },
	{ id: 2, label: '督办逾期工单', icon: DocumentChecked, route: '/workorder' },
	{ id: 3, label: '添加新员工', icon: User, route: '/system/user' },
];

// 统计数据
const statistics = ref({
	total_merchants: 0,
	merchant_trend: 0,
	today_completion_rate: 0,
	completion_trend: 0,
	pending_workorders: 0,
	today_pending: 0,
	active_users: 0,
	chart_data: {
		labels: [],
		data: [],
	},
	latest_updates: [],
});

// 最新动态
const latestUpdates = computed(() => statistics.value.latest_updates || []);

// 加载统计数据
const loadStatistics = async () => {
	try {
		const res = await GetStatistics();
		if (res.code === 2000 && res.data) {
			statistics.value = res.data;
			// 更新图表数据
			updateChart();
		}
	} catch (error) {
		console.error('加载统计数据失败:', error);
		ElMessage.error('加载统计数据失败');
	}
};

// 刷新首页数据
const refreshHomeData = () => {
	// 加载统计数据
	loadStatistics();
	
	// 重新初始化图表（如果图表已存在，先销毁再创建）
	if (chartInstance) {
		chartInstance.dispose();
		chartInstance = null;
	}
	
	// 使用 nextTick 确保 DOM 已更新
	nextTick(() => {
		// 延迟一下确保 DOM 完全渲染
		setTimeout(() => {
			initChart();
		}, 200);
	});
};

// 初始化图表（带重试机制）
const initChart = (retryCount = 0) => {
	if (!chartRef.value) {
		// 如果 DOM 还没准备好，重试（最多重试3次）
		if (retryCount < 3) {
			setTimeout(() => {
				initChart(retryCount + 1);
			}, 200);
		}
		return;
	}

	// 如果图表已存在，先销毁
	if (chartInstance) {
		chartInstance.dispose();
		chartInstance = null;
	}

	try {
		chartInstance = echarts.init(chartRef.value);
		updateChart();
		
		// 确保图表正确渲染
		setTimeout(() => {
			if (chartInstance) {
				chartInstance.resize();
			}
		}, 100);
	} catch (error) {
		console.error('图表初始化失败:', error);
		// 如果初始化失败，重试
		if (retryCount < 3) {
			setTimeout(() => {
				initChart(retryCount + 1);
			}, 300);
		}
		return;
	}

	// 响应式调整
	window.addEventListener('resize', handleResize);
};

const handleResize = () => {
	if (chartInstance) {
		chartInstance.resize();
	}
};

// 更新图表数据
const updateChart = () => {
	if (!chartInstance) return;
	
	const chartData = statistics.value.chart_data || { labels: [], data: [] };
	
	const option = {
		tooltip: {
			trigger: 'axis',
			axisPointer: {
				type: 'shadow',
			},
		},
		grid: {
			left: '3%',
			right: '4%',
			bottom: '3%',
			top: '10%',
			containLabel: true,
		},
		xAxis: {
			type: 'category',
			data: chartData.labels.length > 0 ? chartData.labels : ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
			axisTick: {
				alignWithLabel: true,
			},
		},
		yAxis: {
			type: 'value',
		},
		series: [
			{
				name: '检查次数',
				type: 'bar',
				barWidth: '60%',
				data: chartData.data.length > 0 ? chartData.data : [0, 0, 0, 0, 0, 0, 0],
				itemStyle: {
					color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
						{ offset: 0, color: '#83bff6' },
						{ offset: 0.5, color: '#188df0' },
						{ offset: 1, color: '#188df0' },
					]),
				},
			},
		],
	};

	chartInstance.setOption(option);
};

// 发起检查任务
const handleStartInspection = () => {
	ElMessage.info('发起检查任务功能开发中...');
	// router.push('/task');
};

// 快捷操作
const handleQuickAction = (action: any) => {
	ElMessage.info(`${action.label}功能开发中...`);
	if (action.route) {
		router.push(action.route);
	}
};

// 防抖标记，避免重复刷新
let isRefreshing = false;

// 统一的刷新函数（带防抖）
const triggerRefresh = () => {
	if (isRefreshing) {
		return; // 如果正在刷新，直接返回
	}
	
	isRefreshing = true;
	nextTick(() => {
		setTimeout(() => {
			refreshHomeData();
			// 刷新完成后重置标记
			setTimeout(() => {
				isRefreshing = false;
			}, 500);
		}, 100);
	});
};

// 监听路由路径变化
watch(
	() => route.path,
	(newPath, oldPath) => {
		// 如果进入首页，且从其他页面跳转过来
		if (newPath === '/home' && oldPath && oldPath !== '/home') {
			triggerRefresh();
		}
	},
	{ immediate: false }
);

// 监听自定义刷新事件（从路由守卫触发）
const handleHomeRefresh = () => {
	if (route.path === '/home' || route.name === 'home') {
		triggerRefresh();
	}
};

// 当组件被激活时（keep-alive 场景）
onActivated(() => {
	// 检查当前路由是否是首页
	if (route.path === '/home' || route.name === 'home') {
		// 延迟一下确保 DOM 已渲染
		nextTick(() => {
			setTimeout(() => {
				refreshHomeData();
			}, 300);
		});
	}
});

// 监听自定义事件
onMounted(() => {
	window.addEventListener('home-refresh', handleHomeRefresh);
});

onUnmounted(() => {
	window.removeEventListener('home-refresh', handleHomeRefresh);
});


onMounted(() => {
	// 首次加载数据
	loadStatistics();
	
	// 使用 nextTick 确保 DOM 已渲染
	nextTick(() => {
		setTimeout(() => {
			initChart();
		}, 300);
	});
});

onUnmounted(() => {
	if (chartInstance) {
		chartInstance.dispose();
		window.removeEventListener('resize', handleResize);
	}
});
</script>

<style scoped lang="scss">
.home-container {
	padding: 24px;
	background: #f5f7fa;
	min-height: calc(100vh - 100px);
}

// 顶部区域
.top-section {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 24px;

	.greeting-section {
		.greeting {
			display: flex;
			align-items: center;
			gap: 8px;
			margin-bottom: 8px;

			.greeting-text {
				font-size: 24px;
				font-weight: 500;
				color: #303133;
			}

			.greeting-emoji {
				font-size: 24px;
			}
		}

		.status-message {
			font-size: 14px;
			color: #909399;
		}
	}

	.action-section {
		:deep(.el-button) {
			padding: 12px 24px;
			font-size: 14px;
		}
	}
}

// 指标卡片区域
.metrics-section {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 20px;
	margin-bottom: 24px;

	.metric-card {
		background: #fff;
		border-radius: 8px;
		padding: 24px;
		box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
		position: relative;
		overflow: hidden;
		transition: transform 0.2s, box-shadow 0.2s;

		&:hover {
			transform: translateY(-4px);
			box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15);
		}

		.metric-icon {
			position: absolute;
			top: 24px;
			right: 24px;
			font-size: 32px;
			opacity: 0.2;
		}

		.success-icon {
			color: #67c23a;
		}

		.warning-icon {
			color: #e6a23c;
		}

		.people-icon {
			color: #409eff;
		}

		.metric-content {
			.metric-value {
				font-size: 32px;
				font-weight: 600;
				color: #303133;
				margin-bottom: 8px;
			}

			.metric-label {
				font-size: 14px;
				color: #909399;
				margin-bottom: 8px;
			}

			.metric-trend {
				font-size: 12px;

				&.up {
					color: #67c23a;
				}

				&.down {
					color: #f56c6c;
				}

				&.flat {
					color: #909399;
				}
			}
		}

		.metric-bg-text {
			position: absolute;
			bottom: -10px;
			right: -10px;
			font-size: 48px;
			font-weight: bold;
			color: #f0f2f5;
			opacity: 0.5;
		}
	}
}

// 内容区域
.content-section {
	display: grid;
	grid-template-columns: 2fr 1fr;
	gap: 20px;

	.left-content,
	.right-content {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}
}

// 通用卡片样式
.chart-card,
.quick-actions-card,
.updates-card {
	background: #fff;
	border-radius: 8px;
	padding: 24px;
	box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;

		.card-title {
			display: flex;
			align-items: center;
			gap: 8px;
			font-size: 16px;
			font-weight: 500;
			color: #303133;

			.el-icon {
				font-size: 18px;
				color: #409eff;
			}
		}

		.chart-filters {
			display: flex;
			gap: 8px;
		}
	}
}

// 图表容器
.chart-container {
	width: 100%;
	height: 300px;
}

// 快捷操作
.quick-actions-list {
	display: flex;
	flex-direction: column;
	gap: 12px;

	.quick-action-item {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 16px;
		border-radius: 6px;
		cursor: pointer;
		transition: background-color 0.2s;

		&:hover {
			background-color: #f5f7fa;
		}

		.action-icon {
			color: #409eff;
		}

		.action-text {
			font-size: 14px;
			color: #303133;
		}
	}
}

// 最新动态
.updates-list {
	display: flex;
	flex-direction: column;
	gap: 16px;

	.update-item {
		display: flex;
		align-items: flex-start;
		gap: 12px;

		.update-dot {
			width: 8px;
			height: 8px;
			border-radius: 50%;
			background: #409eff;
			margin-top: 6px;
			flex-shrink: 0;
		}

		.update-content {
			font-size: 14px;
			color: #606266;
			line-height: 1.6;
		}
	}
}

// 响应式设计
@media (max-width: 1400px) {
	.metrics-section {
		grid-template-columns: repeat(2, 1fr);
	}
}

@media (max-width: 768px) {
	.top-section {
		flex-direction: column;
		gap: 16px;
	}

	.metrics-section {
		grid-template-columns: 1fr;
	}

	.content-section {
		grid-template-columns: 1fr;
	}
}
</style>
