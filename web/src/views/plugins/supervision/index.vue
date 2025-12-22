<template>
	<div class="supervision-push-container">
		<!-- 页面头部 -->
		<div class="page-header">
			<div class="header-title">
				<h2>督办推送中心</h2>
				<p class="subtitle">统一筛选严重逾期工单,向监管单位发送正式督办通知</p>
			</div>
		</div>

		<!-- 筛选区域 -->
		<div class="filter-section">
			<el-form :inline="true" :model="filterForm" class="filter-form">
				<el-form-item label="逾期时长">
					<el-select v-model="filterForm.overdue_hours" placeholder="请选择" style="width: 200px">
						<el-option label="超过24小时" value="24" />
						<el-option label="超过48小时" value="48" />
						<el-option label="超过72小时" value="72" />
						<el-option label="超过7天" value="168" />
						<el-option label="全部" value="" />
					</el-select>
				</el-form-item>
				<el-form-item label="问题类型">
					<el-select v-model="filterForm.hazard_level" placeholder="请选择" style="width: 200px">
						<el-option label="全部" value="" />
						<el-option label="高" value="high" />
						<el-option label="中" value="medium" />
						<el-option label="低" value="low" />
					</el-select>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" @click="handleFilter">筛选待督办工单</el-button>
				</el-form-item>
			</el-form>
			<div class="push-button-wrapper">
				<el-button
					type="primary"
					:disabled="selectedWorkorders.length === 0"
					@click="handleBatchPush"
					style="margin-bottom: 10px"
				>
					<el-icon style="margin-right: 4px"><Promotion /></el-icon>
					一键推送选中项 ({{ selectedWorkorders.length }})
				</el-button>
			</div>
		</div>

		<!-- 工单列表 -->
		<div class="workorder-list" v-loading="loading">
			<div
				v-for="workorder in workorderList"
				:key="workorder.id"
				class="workorder-card"
				:class="{ selected: isSelected(workorder.id) }"
			>
				<div class="card-left">
					<el-checkbox
						:model-value="isSelected(workorder.id)"
						@change="(val: boolean) => handleSelectChange(workorder.id, val)"
						class="workorder-checkbox"
					/>
					<div class="workorder-info">
						<div class="workorder-title">
							{{ workorder.merchant_name }} - {{ workorder.problem_description || '无问题描述' }}
						</div>
						<div class="workorder-details">
							工单号:{{ workorder.workorder_no }} | 负责人:{{ workorder.project_manager_name || '未设置' }}
							{{ workorder.merchant_phone ? `(${workorder.merchant_phone})` : '' }}
						</div>
						<div class="workorder-status">
							<span class="overdue-text" :class="'overdue-' + workorder.lag_level.type">
								已逾期:{{ workorder.overdue_duration_display }}
							</span>
						</div>
						<div class="workorder-feedback">
							最后反馈:{{ workorder.last_feedback }}
						</div>
					</div>
				</div>
				<div class="card-right">
					<el-tag
						:type="workorder.lag_level.type === 'danger' ? 'danger' : workorder.lag_level.type === 'warning' ? 'warning' : 'info'"
						size="large"
						style="margin-bottom: 10px"
					>
						{{ workorder.lag_level.label }}
					</el-tag>
					<br />
					<el-link type="primary" @click="handleViewDetail(workorder.id)">查看详情</el-link>
				</div>
			</div>

			<!-- 空状态 -->
			<el-empty v-if="!loading && workorderList.length === 0" description="暂无待督办工单" />

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

<script lang="ts" setup name="supervision">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Promotion } from '@element-plus/icons-vue';
import * as api from './api';
import workorderDetail from '../workorder/detail.vue';

const detailDrawerVisible = ref(false);
const currentWorkorderId = ref<number | string | null>(null);

// 筛选表单
const filterForm = reactive({
	overdue_hours: '24', // 默认超过24小时
	hazard_level: '', // 全部
});

// 工单列表
const workorderList = ref<any[]>([]);
const loading = ref(false);
const selectedWorkorders = ref<number[]>([]);

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
		if (filterForm.overdue_hours) {
			params.overdue_hours = filterForm.overdue_hours;
		}
		if (filterForm.hazard_level) {
			params.hazard_level = filterForm.hazard_level;
		}
		const res = await api.GetWorkOrderList(params);
		if (res.code === 2000) {
			workorderList.value = res.data.list || [];
			pagination.total = res.data.total || 0;
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
	selectedWorkorders.value = [];
	loadWorkorders();
};

// 选择工单
const isSelected = (id: number) => {
	return selectedWorkorders.value.includes(id);
};

const handleSelectChange = (id: number, checked: boolean) => {
	if (checked) {
		if (!selectedWorkorders.value.includes(id)) {
			selectedWorkorders.value.push(id);
		}
	} else {
		const index = selectedWorkorders.value.indexOf(id);
		if (index > -1) {
			selectedWorkorders.value.splice(index, 1);
		}
	}
};

// 批量推送
const handleBatchPush = async () => {
	if (selectedWorkorders.value.length === 0) {
		ElMessage.warning('请先选择要推送的工单');
		return;
	}

	try {
		await ElMessageBox.confirm(
			`确定要向监管单位推送 ${selectedWorkorders.value.length} 个工单的督办通知吗？`,
			'确认推送',
			{
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);

		const res = await api.BatchPush({
			workorder_ids: selectedWorkorders.value,
			regulatory_unit: '监管单位', // 暂时写死，后续可以从配置或选择器获取
			push_method: 'system',
		});

		if (res.code === 2000) {
			ElMessage.success(res.msg || '推送成功');
			selectedWorkorders.value = [];
			loadWorkorders();
		} else {
			ElMessage.error(res.msg || '推送失败');
		}
	} catch (error: any) {
		if (error !== 'cancel') {
			ElMessage.error('推送失败');
			console.error(error);
		}
	}
};

// 查看详情
const handleViewDetail = (id: number) => {
	// 打开工单详情抽屉
	currentWorkorderId.value = id;
	detailDrawerVisible.value = true;
};

// 页面加载时获取数据
onMounted(() => {
	loadWorkorders();
});
</script>

<style scoped lang="scss">
.supervision-push-container {
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

	.filter-form {
		margin-bottom: 10px;
	}

	.push-button-wrapper {
		text-align: right;
	}
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

	&.selected {
		border-color: #409eff;
		background: #ecf5ff;
	}

	.card-left {
		display: flex;
		flex: 1;
		align-items: flex-start;

		.workorder-checkbox {
			margin-right: 12px;
			margin-top: 4px;
		}

		.workorder-info {
			flex: 1;

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

				.overdue-text {
					font-size: 14px;
					font-weight: 500;

					&.overdue-danger {
						color: #f56c6c;
					}

					&.overdue-warning {
						color: #e6a23c;
					}

					&.overdue-info {
						color: #909399;
					}
				}
			}

			.workorder-feedback {
				font-size: 14px;
				color: #909399;
			}
		}
	}

	.card-right {
		text-align: right;
		min-width: 120px;
	}
}

.pagination-wrapper {
	margin-top: 20px;
	text-align: right;
}
</style>

