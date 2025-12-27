<template>
	<div class="transfer-center-container">
		<!-- 页面头部 -->
		<div class="page-header">
			<div class="header-title">
				<h2>移交中心</h2>
				<p class="subtitle">查看和管理已移交的工单</p>
			</div>
		</div>

		<!-- 筛选区域 -->
		<div class="filter-section">
			<el-form :inline="true" :model="filterForm" class="filter-form">
				<el-form-item label="隐患等级">
					<el-select v-model="filterForm.hazard_level" placeholder="全部" style="width: 200px" clearable>
						<el-option label="全部" value="" />
						<el-option label="高" value="high" />
						<el-option label="中" value="medium" />
						<el-option label="低" value="low" />
					</el-select>
				</el-form-item>
				<el-form-item label="工单状态">
					<el-select v-model="filterForm.status" placeholder="全部" style="width: 200px" clearable>
						<el-option label="全部" value="" />
						<el-option label="待整改" :value="0" />
						<el-option label="待复查" :value="1" />
						<el-option label="已完成" :value="2" />
						<el-option label="已逾期" :value="3" />
					</el-select>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" @click="handleFilter">筛选工单</el-button>
				</el-form-item>
			</el-form>
		</div>

		<!-- 工单列表 -->
		<div class="workorder-list" v-loading="loading">
			<div
				v-for="workorder in workorderList"
				:key="workorder.id"
				class="workorder-card"
			>
				<div class="card-left">
					<div class="workorder-info">
						<div class="workorder-title">
							{{ workorder.merchant_name }} - {{ workorder.problem_description || '无问题描述' }}
						</div>
						<div class="workorder-details">
							工单号:{{ workorder.workorder_no }} | 检查人:{{ workorder.inspector_name || '未设置' }} | 包保责任人:{{ workorder.responsible_person_name || '未设置' }} | 移交负责人:{{ workorder.transfer_person_name || '未设置' }}
							{{ workorder.merchant_phone ? `(${workorder.merchant_phone})` : '' }}
						</div>
						<div class="workorder-status" v-if="workorder.deadline">
							<span class="status-text" :class="getStatusClass(workorder)">
								{{ getStatusText(workorder) }}
							</span>
							<span v-if="workorder.overdue_duration_display" class="overdue-text">
								逾期:{{ workorder.overdue_duration_display }}
							</span>
						</div>
						<div class="workorder-transfer" v-if="workorder.transfer_remark">
							移交备注: {{ workorder.transfer_remark }}
						</div>
					</div>
				</div>
				<div class="card-right">
					<el-tag
						:type="getHazardLevelType(workorder.hazard_level)"
						size="large"
						style="margin-bottom: 10px"
					>
						{{ workorder.hazard_level_display || '未设置' }}
					</el-tag>
					<el-tag
						:type="getStatusTagType(workorder.status)"
						size="small"
						style="margin-bottom: 10px"
					>
						{{ getStatusDisplay(workorder.status) }}
					</el-tag>
					<br />
					<div class="card-actions">
						<el-button type="primary" link @click="handleViewDetail(workorder.id)">查看详情</el-button>
					</div>
				</div>
			</div>

			<!-- 空状态 -->
			<el-empty v-if="!loading && workorderList.length === 0" description="暂无已移交工单" />

			<!-- 分页 -->
			<div class="pagination-wrapper" v-if="workorderList.length > 0">
				<el-pagination
					v-model:current-page="pagination.page"
					v-model:page-size="pagination.limit"
					:total="pagination.total"
					:page-sizes="[10, 20, 50, 100]"
					layout="total, sizes, prev, pager, next, jumper"
					@size-change="loadWorkorders"
					@current-change="loadWorkorders"
				/>
			</div>
		</div>
		
		<!-- 工单详情抽屉 -->
		<el-drawer
			v-model="detailDrawerVisible"
			title="工单详情"
			direction="rtl"
			size="80%"
			:close-on-click-modal="false"
			destroy-on-close
		>
			<workorder-detail
				v-if="detailDrawerVisible && currentWorkorderId"
				:workorder-id="currentWorkorderId"
			/>
		</el-drawer>
	</div>
</template>

<script lang="ts" setup name="transfer">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import * as api from './api';
import workorderDetail from '../../workorder/detail.vue';

const detailDrawerVisible = ref(false);
const currentWorkorderId = ref<number | string | null>(null);

// 筛选表单
const filterForm = reactive({
	hazard_level: '', // 隐患等级
	status: '', // 工单状态
});

// 工单列表
const workorderList = ref<any[]>([]);
const loading = ref(false);

// 分页
const pagination = reactive({
	page: 1,
	limit: 10,
	total: 0,
});

// 加载工单列表
const loadWorkorders = async () => {
	loading.value = true;
	try {
		const params: any = {
			page: pagination.page,
			limit: pagination.limit,
		};
		if (filterForm.hazard_level) {
			params.hazard_level = filterForm.hazard_level;
		}
		if (filterForm.status !== '') {
			params.status = filterForm.status;
		}
		const res = await api.GetTransferredWorkOrderList(params);
		if (res.code === 2000) {
			workorderList.value = res.data.list || [];
			pagination.total = res.data.total || 0;
		} else {
			ElMessage.error(res.msg || '加载工单列表失败');
		}
	} catch (error) {
		ElMessage.error('加载工单列表失败');
		console.error(error);
	} finally {
		loading.value = false;
	}
};

// 筛选
const handleFilter = () => {
	pagination.page = 1;
	loadWorkorders();
};

// 查看详情
const handleViewDetail = (id: number) => {
	currentWorkorderId.value = id;
	detailDrawerVisible.value = true;
};

// 获取状态文本
const getStatusText = (workorder: any) => {
	if (workorder.status === 2) {
		return '已完成';
	} else if (workorder.status === 3) {
		return '已逾期';
	} else if (workorder.status === 1) {
		return '待复查';
	} else {
		return '待整改';
	}
};

// 获取状态样式类
const getStatusClass = (workorder: any) => {
	if (workorder.status === 2) {
		return 'status-success';
	} else if (workorder.status === 3) {
		return 'status-danger';
	} else if (workorder.status === 1) {
		return 'status-warning';
	} else {
		return 'status-info';
	}
};

// 获取状态显示文本
const getStatusDisplay = (status: number) => {
	const statusMap: Record<number, string> = {
		0: '待整改',
		1: '待复查',
		2: '已完成',
		3: '已逾期',
	};
	return statusMap[status] || '未知';
};

// 获取状态标签类型
const getStatusTagType = (status: number) => {
	const typeMap: Record<number, string> = {
		0: 'info',
		1: 'warning',
		2: 'success',
		3: 'danger',
	};
	return typeMap[status] || 'info';
};

// 获取隐患等级标签类型
const getHazardLevelType = (level: string) => {
	const typeMap: Record<string, string> = {
		high: 'danger',
		medium: 'warning',
		low: 'info',
	};
	return typeMap[level] || 'info';
};

// 页面加载时获取数据
onMounted(() => {
	loadWorkorders();
});
</script>

<style scoped lang="scss">
.transfer-center-container {
	padding: 20px;
	background: #f5f5f5;
	min-height: calc(100vh - 60px);
}

.page-header {
	margin-bottom: 20px;
	background: white;
	padding: 20px;
	border-radius: 4px;

	.header-title {
		h2 {
			margin: 0 0 8px 0;
			font-size: 20px;
			font-weight: 500;
			color: #303133;
		}

		.subtitle {
			margin: 0;
			font-size: 14px;
			color: #909399;
		}
	}
}

.filter-section {
	background: white;
	padding: 20px;
	border-radius: 4px;
	margin-bottom: 20px;
}

.workorder-list {
	background: white;
	padding: 20px;
	border-radius: 4px;
}

.workorder-card {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	padding: 20px;
	margin-bottom: 16px;
	border: 1px solid #e4e7ed;
	border-radius: 4px;
	background: #fff;
	transition: all 0.3s;

	&:hover {
		box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
	}

	.card-left {
		flex: 1;

		.workorder-info {
			.workorder-title {
				font-size: 16px;
				font-weight: 500;
				color: #303133;
				margin-bottom: 8px;
			}

			.workorder-details {
				font-size: 14px;
				color: #606266;
				margin-bottom: 8px;
			}

			.workorder-status {
				margin-bottom: 8px;
				display: flex;
				gap: 16px;
				align-items: center;

				.status-text {
					font-size: 14px;
					font-weight: 500;

					&.status-success {
						color: #67c23a;
					}

					&.status-danger {
						color: #f56c6c;
					}

					&.status-warning {
						color: #e6a23c;
					}

					&.status-info {
						color: #909399;
					}
				}

				.overdue-text {
					font-size: 14px;
					color: #f56c6c;
				}
			}

			.workorder-transfer {
				font-size: 14px;
				color: #909399;
				margin-top: 8px;
			}
		}
	}

	.card-right {
		text-align: right;
		min-width: 120px;
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 6px;

		.card-actions {
			display: flex;
			flex-direction: column;
			gap: 4px;
			align-items: flex-end;
		}
	}
}

.pagination-wrapper {
	margin-top: 20px;
	text-align: right;
}
</style>

