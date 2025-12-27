<template>
	<div class="dashboard-container">
		<!-- 顶部标题栏 -->
		<div class="dashboard-header">
			<div class="header-left">
				<SvgIcon name="ele-Shield" class="shield-icon" />
				<h1 class="header-title">智能巡检大数据监管中心</h1>
			</div>
			<div class="header-right">
				<el-button type="primary" @click="exitFullscreen">退出大屏</el-button>
			</div>
		</div>

		<!-- 主要内容区域 -->
		<div class="dashboard-content">
			<!-- 左侧列 -->
			<div class="dashboard-left">
				<!-- 场所分类饼图 -->
				<div class="panel category-pie">
					<div class="panel-title">场所分类分布</div>
					<div ref="categoryPieChartRef" class="chart-container"></div>
				</div>

				<!-- 问题类别柱状图 -->
				<div class="panel problem-bar">
					<div class="panel-title">问题类别分布</div>
					<div ref="problemBarChartRef" class="chart-container"></div>
				</div>
			</div>

			<!-- 中间列 -->
			<div class="dashboard-center">
				<div class="panel heatmap-panel">
					<div class="panel-title">隐患分布热力图</div>
					<div class="heatmap-area">
						<div class="map-container">
							<!-- 动态渲染隐患点位 -->
							<div
								v-for="(point, index) in dashboardData.heatmap_points || []"
								:key="index"
								class="map-dot"
								:style="getDotStyle(point)"
								:title="`${point.merchant_name} - 隐患数：${point.hazard_count}`"
							></div>
							<div class="map-label">隐患商户：{{ (dashboardData.heatmap_points || []).length }} 个</div>
							
							<!-- 今日概览（放在热力图右上角） -->
							<div class="today-overview-overlay">
								<div class="panel-title" @click="toggleTodayOverview">
									<span>今日概览</span>
									<span class="expand-icon" :class="{ expanded: todayOverviewExpanded }">+</span>
								</div>
								<div v-show="todayOverviewExpanded" class="overview-items">
									<div class="overview-item">
										<div class="item-label">计划检查</div>
										<div class="item-value">{{ dashboardData.today_overview?.planned_checks || 0 }}</div>
									</div>
									<div class="overview-item">
										<div class="item-label">已完成</div>
										<div class="item-value success">{{ dashboardData.today_overview?.completed_checks || 0 }}</div>
									</div>
									<div class="overview-item">
										<div class="item-label">发现隐患</div>
										<div class="item-value danger">{{ dashboardData.today_overview?.found_hazards || 0 }}</div>
									</div>
									<div class="overview-item">
										<div class="item-label">移交总数</div>
										<div class="item-value warning">{{ dashboardData.transfer_total || 0 }}</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- 右侧列 -->
			<div class="dashboard-right">
				<!-- 实时预警动态 -->
				<div class="panel warning-dynamic">
					<div class="panel-title">实时预警动态</div>
					<div class="warning-list">
						<div 
							v-for="(warning, index) in dashboardData.warnings" 
							:key="index"
							class="warning-item"
						>
							<div class="warning-name">{{ warning.merchant_name }}</div>
							<div class="warning-content danger">{{ warning.problem }}</div>
						</div>
						<div v-if="!dashboardData.warnings || dashboardData.warnings.length === 0" class="warning-item">
							<div class="warning-content" style="color: #a0a0a0;">暂无预警信息</div>
						</div>
					</div>
				</div>

				<!-- 督办Top5 -->
				<div class="panel performance-top5">
					<div class="panel-title">督办 Top5</div>
					<div class="performance-list">
						<div 
							v-for="(item, index) in dashboardData.performance_top5" 
							:key="index"
							class="performance-item"
						>
							<div class="rank">{{ item.rank }}</div>
							<div class="name">{{ item.name }}</div>
							<div class="count">{{ item.count }} 次</div>
						</div>
						<div v-if="!dashboardData.performance_top5 || dashboardData.performance_top5.length === 0" class="performance-item">
							<div class="name" style="color: #a0a0a0;">暂无数据</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts" setup name="dashboard">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useRouter } from 'vue-router';
import SvgIcon from '/@/components/svgIcon/index.vue';
import { GetDashboardData } from './api';
import { ElMessage } from 'element-plus';
import * as echarts from 'echarts';

const router = useRouter();

// 图表引用
const categoryPieChartRef = ref<HTMLDivElement>();
const problemBarChartRef = ref<HTMLDivElement>();
let categoryPieChart: echarts.ECharts | null = null;
let problemBarChart: echarts.ECharts | null = null;

// 今日概览展开/收起状态
const todayOverviewExpanded = ref(false);

// 切换今日概览展开/收起
const toggleTodayOverview = () => {
	todayOverviewExpanded.value = !todayOverviewExpanded.value;
};

// 大屏数据
const dashboardData = ref({
	today_overview: {
		planned_checks: 0,
		completed_checks: 0,
		found_hazards: 0,
	},
	problem_distribution: {
		fire: 0,
		health: 0,
		license: 0,
		other: 0,
	},
	warnings: [],
	performance_top5: [],
	transfer_total: 0,
	category_pie_data: [],
	problem_bar_data: [],
	heatmap_points: [],
});

// 加载大屏数据
const loadDashboardData = async () => {
	try {
		const res = await GetDashboardData();
		if (res.code === 2000 && res.data) {
			dashboardData.value = res.data;
			// 更新图表
			nextTick(() => {
				updateCharts();
			});
		}
	} catch (error) {
		console.error('加载大屏数据失败:', error);
		ElMessage.error('加载大屏数据失败');
	}
};

// 初始化图表
const initCharts = () => {
	if (categoryPieChartRef.value && !categoryPieChart) {
		categoryPieChart = echarts.init(categoryPieChartRef.value);
	}
	if (problemBarChartRef.value && !problemBarChart) {
		problemBarChart = echarts.init(problemBarChartRef.value);
	}
};

// 更新图表
const updateCharts = () => {
	initCharts();
	
	// 更新场所分类饼图
	if (categoryPieChart && dashboardData.value.category_pie_data) {
		const option = {
			tooltip: {
				trigger: 'item',
				formatter: '{a} <br/>{b}: {c} ({d}%)',
			},
			legend: {
				orient: 'vertical',
				left: 'left',
				textStyle: {
					color: '#fff',
					fontSize: 12,
				},
			},
			series: [
				{
					name: '场所分类',
					type: 'pie',
					radius: ['40%', '70%'],
					avoidLabelOverlap: false,
					itemStyle: {
						borderRadius: 10,
						borderColor: '#0a0e27',
						borderWidth: 2,
					},
					label: {
						show: true,
						color: '#fff',
						fontSize: 12,
					},
					emphasis: {
						label: {
							show: true,
							fontSize: 14,
							fontWeight: 'bold',
						},
					},
					data: dashboardData.value.category_pie_data,
				},
			],
		};
		categoryPieChart.setOption(option);
	}
	
	// 更新问题类别柱状图
	if (problemBarChart && dashboardData.value.problem_bar_data) {
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
				bottom: '15%', // 增加底部空间以显示完整标签
				containLabel: true,
			},
			xAxis: {
				type: 'category',
				data: dashboardData.value.problem_bar_data.map((item: any) => item.name),
				axisLabel: {
					color: '#fff',
					fontSize: 12,
					interval: 0, // 强制显示所有标签
					rotate: 0, // 不旋转，如果文字太长可以设置为45
					formatter: (value: string) => {
						// 如果文字太长，可以换行或截断
						return value.length > 8 ? value.substring(0, 8) + '...' : value;
					},
				},
				axisLine: {
					lineStyle: {
						color: '#409eff',
					},
				},
			},
			yAxis: {
				type: 'value',
				axisLabel: {
					color: '#fff',
					fontSize: 12,
				},
				axisLine: {
					lineStyle: {
						color: '#409eff',
					},
				},
				splitLine: {
					lineStyle: {
						color: 'rgba(64, 158, 255, 0.2)',
					},
				},
			},
			series: [
				{
					name: '问题数量',
					type: 'bar',
					data: dashboardData.value.problem_bar_data.map((item: any) => item.value),
					itemStyle: {
						color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
							{ offset: 0, color: '#409eff' },
							{ offset: 1, color: '#66b1ff' },
						]),
						borderRadius: [4, 4, 0, 0],
					},
					label: {
						show: true,
						position: 'top',
						color: '#fff',
						fontSize: 12,
					},
				},
			],
		};
		problemBarChart.setOption(option);
	}
};

// 获取点位样式（根据GPS坐标随机分布，但保持相对位置，并根据隐患数量设置颜色）
const getDotStyle = (point: any) => {
	// 这里简化处理，实际应该根据GPS坐标转换为地图上的相对位置
	// 为了演示，我们使用一个简单的随机分布
	const hash = point.merchant_name.split('').reduce((acc: number, char: string) => acc + char.charCodeAt(0), 0);
	const top = 10 + (hash % 80);
	const left = 10 + ((hash * 7) % 80);
	
	// 根据隐患数量设置颜色：隐患越多颜色越深（红色），少的灰色
	const hazardCount = point.hazard_count || 0;
	let backgroundColor = '#909399'; // 灰色（隐患少）
	let boxShadowColor = 'rgba(144, 147, 153, 0.8)';
	
	if (hazardCount >= 5) {
		// 隐患很多：深红色
		backgroundColor = '#f56c6c';
		boxShadowColor = 'rgba(245, 108, 108, 0.9)';
	} else if (hazardCount >= 3) {
		// 隐患较多：红色
		backgroundColor = '#f78989';
		boxShadowColor = 'rgba(247, 137, 137, 0.8)';
	} else if (hazardCount >= 2) {
		// 隐患中等：橙红色
		backgroundColor = '#f5a623';
		boxShadowColor = 'rgba(245, 166, 35, 0.8)';
	} else if (hazardCount >= 1) {
		// 隐患较少：浅红色
		backgroundColor = '#f5b6b6';
		boxShadowColor = 'rgba(245, 182, 182, 0.6)';
	}
	
	return {
		top: `${top}%`,
		left: `${left}%`,
		backgroundColor: backgroundColor,
		boxShadow: `0 0 15px ${boxShadowColor}`,
	};
};

// 退出全屏
const exitFullscreen = () => {
	router.push('/home');
};

// 定时器引用
let refreshInterval: NodeJS.Timeout | null = null;

// 全屏处理
onMounted(() => {
	// 隐藏侧边栏和头部（如果需要全屏效果）
	document.body.style.overflow = 'hidden';
	// 初始化图表
	nextTick(() => {
		initCharts();
	});
	// 加载数据
	loadDashboardData();
	// 设置定时刷新（每30秒刷新一次）
	refreshInterval = setInterval(() => {
		loadDashboardData();
	}, 30000);
	
	// 监听窗口大小变化，调整图表
	window.addEventListener('resize', () => {
		if (categoryPieChart) {
			categoryPieChart.resize();
		}
		if (problemBarChart) {
			problemBarChart.resize();
		}
	});
});

onUnmounted(() => {
	document.body.style.overflow = '';
	// 清除定时器
	if (refreshInterval) {
		clearInterval(refreshInterval);
		refreshInterval = null;
	}
	// 销毁图表
	if (categoryPieChart) {
		categoryPieChart.dispose();
		categoryPieChart = null;
	}
	if (problemBarChart) {
		problemBarChart.dispose();
		problemBarChart = null;
	}
	// 移除窗口大小监听
	window.removeEventListener('resize', () => {});
});
</script>

<style scoped lang="scss">
.dashboard-container {
	width: 100vw;
	height: 100vh;
	background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
	color: #fff;
	overflow: hidden;
	position: fixed;
	top: 0;
	left: 0;
	z-index: 9999;
}

.dashboard-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 20px 40px;
	background: rgba(0, 0, 0, 0.3);

	.header-left {
		display: flex;
		align-items: center;
		gap: 15px;

		.shield-icon {
			font-size: 32px;
			color: #409eff;
		}

		.header-title {
			font-size: 28px;
			font-weight: 600;
			margin: 0;
			background: linear-gradient(90deg, #409eff 0%, #66b1ff 100%);
			-webkit-background-clip: text;
			-webkit-text-fill-color: transparent;
			background-clip: text;
		}
	}

	.header-right {
		:deep(.el-button) {
			padding: 10px 20px;
			font-size: 14px;
		}
	}
}

.dashboard-content {
	display: grid;
	grid-template-columns: 420px 1fr 280px;
	gap: 20px;
	padding: 20px;
	height: calc(100vh - 80px);
	overflow: hidden;
}

.panel {
	background: rgba(0, 0, 0, 0.4);
	border-radius: 8px;
	padding: 20px;
	backdrop-filter: blur(10px);
	box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
	display: flex;
	flex-direction: column;
	min-height: 0;

	.panel-title {
		font-size: 18px;
		font-weight: 600;
		margin-bottom: 20px;
		padding-bottom: 10px;
		color: #66b1ff;
		flex-shrink: 0; // 标题不缩放
	}
}

// 左侧列
.dashboard-left {
	display: flex;
	flex-direction: column;
	gap: 20px;
	overflow-y: auto;
	height: 100%;

	.today-overview {
		.overview-items {
			display: flex;
			flex-direction: column;
			gap: 20px;

			.overview-item {
				.item-label {
					font-size: 14px;
					color: #a0a0a0;
					margin-bottom: 8px;
				}

				.item-value {
					font-size: 36px;
					font-weight: bold;
					color: #409eff;

					&.success {
						color: #67c23a;
					}

					&.danger {
						color: #f56c6c;
					}
					
					&.warning {
						color: #e6a23c;
					}
				}
			}
		}
	}

	.category-pie {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-height: 0;
		
		.chart-container {
			width: 100%;
			flex: 1;
			min-height: 0;
		}
	}
	
	.problem-bar {
		flex: 1.2; // 保持框大小不变
		display: flex;
		flex-direction: column;
		min-height: 0;
		
		.panel-title {
			flex-shrink: 0;
			margin-bottom: 5px; // 减少标题底部间距，给图表更多空间
		}
		
		.chart-container {
			width: 100%;
			flex: 1;
			min-height: 0;
		}
		
		// 确保问题类别分布的所有字都能显示，图表占满容器
		:deep(.echarts) {
			width: 100% !important;
			height: 100% !important;
		}
	}
}

// 中间列
.dashboard-center {
	height: 100%;
	
	.heatmap-panel {
		height: 100%;
		display: flex;
		flex-direction: column;
		min-height: 0;

		.heatmap-area {
			flex: 1;
			position: relative;
			min-height: 0;

			.map-container {
				width: 100%;
				height: 100%;
				background: rgba(0, 0, 0, 0.3);
				border-radius: 4px;
				position: relative;
				overflow: hidden;

				.map-dot {
					position: absolute;
					width: 12px;
					height: 12px;
					border-radius: 50%;
					transform: translate(-50%, -50%);
					animation: pulse 2s infinite;
					cursor: pointer;
					z-index: 10;
				}
				
				.today-overview-overlay {
					position: absolute;
					top: 20px;
					right: 20px;
					background: rgba(0, 0, 0, 0.6);
					border-radius: 8px;
					padding: 15px;
					backdrop-filter: blur(10px);
					box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
					min-width: 200px;
					z-index: 20;
					
					.panel-title {
						font-size: 16px;
						font-weight: 600;
						margin-bottom: 0;
						padding-bottom: 8px;
						border-bottom: 1px solid rgba(102, 177, 255, 0.3);
						color: #66b1ff;
						cursor: pointer;
						display: flex;
						justify-content: space-between;
						align-items: center;
						user-select: none;
						transition: all 0.3s;
						
						&:hover {
							color: #66b1ff;
							opacity: 0.9;
						}
						
						.expand-icon {
							font-size: 20px;
							font-weight: bold;
							width: 24px;
							height: 24px;
							display: flex;
							align-items: center;
							justify-content: center;
							border-radius: 4px;
							background: rgba(102, 177, 255, 0.2);
							transition: transform 0.3s;
							
							&.expanded {
								transform: rotate(45deg);
							}
						}
					}
					
					.overview-items {
						display: flex;
						flex-direction: column;
						gap: 12px;
						
						.overview-item {
							.item-label {
								font-size: 12px;
								color: #a0a0a0;
								margin-bottom: 4px;
							}
							
							.item-value {
								font-size: 24px;
								font-weight: bold;
								color: #409eff;
								
								&.success {
									color: #67c23a;
								}
								
								&.danger {
									color: #f56c6c;
								}
								
								&.warning {
									color: #e6a23c;
								}
							}
						}
					}
				}

				.map-label {
					position: absolute;
					bottom: 20px;
					left: 50%;
					transform: translateX(-50%);
					color: #a0a0a0;
					font-size: 14px;
				}
			}
		}
	}
}

// 右侧列
.dashboard-right {
	display: flex;
	flex-direction: column;
	gap: 20px;
	overflow-y: auto;
	height: 100%;
	
	.warning-dynamic {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-height: 0;
		
		.warning-list {
			flex: 1;
			overflow-y: auto;
		}
	}
	
	.performance-top5 {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-height: 0;
		
		.performance-list {
			flex: 1;
			overflow-y: auto;
		}
	}

	.warning-dynamic {
		.warning-list {
			display: flex;
			flex-direction: column;
			gap: 15px;

			.warning-item {
				padding: 12px;
				background: rgba(255, 255, 255, 0.05);
				border-radius: 4px;

				.warning-name {
					font-size: 14px;
					margin-bottom: 5px;
					color: #fff;
				}

				.warning-content {
					font-size: 13px;

					&.danger {
						color: #f56c6c;
					}
				}
			}
		}
	}

	.performance-top5 {
		.performance-list {
			display: flex;
			flex-direction: column;
			gap: 15px;

			.performance-item {
				display: flex;
				align-items: center;
				gap: 15px;
				padding: 12px;
				background: rgba(255, 255, 255, 0.05);
				border-radius: 4px;

				.rank {
					width: 30px;
					height: 30px;
					line-height: 30px;
					text-align: center;
					background: #409eff;
					border-radius: 50%;
					font-weight: bold;
				}

				.name {
					flex: 1;
					font-size: 14px;
					color: #fff;
				}

				.count {
					font-size: 14px;
					color: #409eff;
					font-weight: 600;
				}
			}
		}
	}
}

@keyframes pulse {
	0%, 100% {
		opacity: 1;
		transform: translate(-50%, -50%) scale(1);
	}
	50% {
		opacity: 0.6;
		transform: translate(-50%, -50%) scale(1.2);
	}
}

// 滚动条样式
:deep(.el-scrollbar__bar) {
	opacity: 0.3;
}
</style>

