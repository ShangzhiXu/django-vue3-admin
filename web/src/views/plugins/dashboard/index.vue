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
				<!-- 今日概览 -->
				<div class="panel today-overview">
					<div class="panel-title">今日概览</div>
					<div class="overview-items">
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
					</div>
				</div>

				<!-- 问题类型分布 -->
				<div class="panel problem-distribution">
					<div class="panel-title">问题类型分布</div>
					<div class="problem-tabs">
						<div class="problem-tab" :class="{ active: activeTab === 'fire' }" @click="activeTab = 'fire'">
							消防
							<div class="tab-count">{{ dashboardData.problem_distribution?.fire || 0 }}</div>
						</div>
						<div class="problem-tab" :class="{ active: activeTab === 'health' }" @click="activeTab = 'health'">
							卫生
							<div class="tab-count">{{ dashboardData.problem_distribution?.health || 0 }}</div>
						</div>
						<div class="problem-tab" :class="{ active: activeTab === 'license' }" @click="activeTab = 'license'">
							证照
							<div class="tab-count">{{ dashboardData.problem_distribution?.license || 0 }}</div>
						</div>
						<div class="problem-tab" :class="{ active: activeTab === 'other' }" @click="activeTab = 'other'">
							其他
							<div class="tab-count">{{ dashboardData.problem_distribution?.other || 0 }}</div>
						</div>
					</div>
				</div>
			</div>

			<!-- 中间列 -->
			<div class="dashboard-center">
				<div class="panel heatmap-panel">
					<div class="panel-title">实时巡检热力图</div>
					<div class="heatmap-area">
						<div class="map-container">
							<!-- 模拟地图点位 -->
							<div class="map-dot dot-yellow" style="top: 20%; left: 50%;"></div>
							<div class="map-dot dot-red" style="top: 45%; left: 20%;"></div>
							<div class="map-dot dot-red" style="top: 75%; left: 80%;"></div>
							<div class="map-label">[GIS 地图区域]</div>
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

				<!-- 人员绩效Top5 -->
				<div class="panel performance-top5">
					<div class="panel-title">人员绩效 Top5</div>
					<div class="performance-list">
						<div 
							v-for="(item, index) in dashboardData.performance_top5" 
							:key="index"
							class="performance-item"
						>
							<div class="rank">{{ item.rank }}</div>
							<div class="name">{{ item.name }}</div>
							<div class="count">{{ item.count }} 家</div>
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
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import SvgIcon from '/@/components/svgIcon/index.vue';
import { GetDashboardData } from './api';
import { ElMessage } from 'element-plus';

const router = useRouter();
const activeTab = ref('fire');

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
});

// 加载大屏数据
const loadDashboardData = async () => {
	try {
		const res = await GetDashboardData();
		if (res.code === 2000 && res.data) {
			dashboardData.value = res.data;
		}
	} catch (error) {
		console.error('加载大屏数据失败:', error);
		ElMessage.error('加载大屏数据失败');
	}
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
	// 加载数据
	loadDashboardData();
	// 设置定时刷新（每30秒刷新一次）
	refreshInterval = setInterval(() => {
		loadDashboardData();
	}, 30000);
});

onUnmounted(() => {
	document.body.style.overflow = '';
	// 清除定时器
	if (refreshInterval) {
		clearInterval(refreshInterval);
		refreshInterval = null;
	}
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
	border-bottom: 1px solid rgba(255, 255, 255, 0.1);

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
	grid-template-columns: 350px 1fr 350px;
	gap: 20px;
	padding: 20px;
	height: calc(100vh - 80px);
	overflow: hidden;
}

.panel {
	background: rgba(0, 0, 0, 0.4);
	border: 1px solid rgba(255, 255, 255, 0.1);
	border-radius: 8px;
	padding: 20px;
	backdrop-filter: blur(10px);
	box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);

	.panel-title {
		font-size: 18px;
		font-weight: 600;
		margin-bottom: 20px;
		padding-bottom: 10px;
		border-bottom: 2px solid rgba(64, 158, 255, 0.5);
		color: #66b1ff;
	}
}

// 左侧列
.dashboard-left {
	display: flex;
	flex-direction: column;
	gap: 20px;
	overflow-y: auto;

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
				}
			}
		}
	}

	.problem-distribution {
		.problem-tabs {
			display: flex;
			flex-wrap: wrap;
			gap: 10px;

			.problem-tab {
				flex: 1;
				min-width: 80px;
				padding: 10px 15px;
				text-align: center;
				background: rgba(255, 255, 255, 0.1);
				border: 1px solid rgba(255, 255, 255, 0.2);
				border-radius: 4px;
				cursor: pointer;
				transition: all 0.3s;
				position: relative;

				.tab-count {
					font-size: 12px;
					margin-top: 5px;
					opacity: 0.8;
				}

				&:hover {
					background: rgba(64, 158, 255, 0.2);
					border-color: #409eff;
				}

				&.active {
					background: #409eff;
					border-color: #409eff;
					color: #fff;
				}
			}
		}
	}
}

// 中间列
.dashboard-center {
	.heatmap-panel {
		height: 100%;
		display: flex;
		flex-direction: column;

		.heatmap-area {
			flex: 1;
			position: relative;

			.map-container {
				width: 100%;
				height: 100%;
				background: rgba(0, 0, 0, 0.3);
				border-radius: 4px;
				position: relative;
				overflow: hidden;

				.map-dot {
					position: absolute;
					width: 20px;
					height: 20px;
					border-radius: 50%;
					transform: translate(-50%, -50%);
					animation: pulse 2s infinite;

					&.dot-yellow {
						background: #e6a23c;
						box-shadow: 0 0 20px rgba(230, 162, 60, 0.8);
					}

					&.dot-red {
						background: #f56c6c;
						box-shadow: 0 0 20px rgba(245, 108, 108, 0.8);
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

	.warning-dynamic {
		.warning-list {
			display: flex;
			flex-direction: column;
			gap: 15px;

			.warning-item {
				padding: 12px;
				background: rgba(255, 255, 255, 0.05);
				border-radius: 4px;
				border-left: 3px solid #f56c6c;

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

