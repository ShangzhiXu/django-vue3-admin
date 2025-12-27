<template>
	<div class="supervision-container">
		<el-card class="box-card">
			<template #header>
				<div class="card-header">
					<span class="title">督办中心</span>
					<span class="subtitle">统一筛选严重逾期工单，向监管单位发送正式督办通知</span>
				</div>
			</template>

			<!-- 筛选区域 -->
			<el-form :inline="true" :model="filterForm" class="filter-form">
				<el-form-item label="逾期时长">
					<el-select v-model="filterForm.overdue_hours" placeholder="全部" style="width: 200px" clearable>
						<el-option label="全部" value="" />
						<el-option label="超过24小时" value="24" />
						<el-option label="超过48小时" value="48" />
						<el-option label="超过72小时" value="72" />
						<el-option label="超过7天" value="168" />
					</el-select>
				</el-form-item>
				<el-form-item label="隐患等级">
					<el-select v-model="filterForm.hazard_level" placeholder="请选择" style="width: 200px" clearable>
						<el-option label="全部" value="" />
						<el-option label="高" value="high" />
						<el-option label="中" value="medium" />
						<el-option label="低" value="low" />
					</el-select>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" @click="handleFilter">筛选</el-button>
					<el-button @click="handleReset">重置</el-button>
					<el-button type="success" @click="handleExport">导出</el-button>
				</el-form-item>
			</el-form>

			<!-- 批量操作 -->
			<div class="batch-actions" v-if="selectedWorkorders.length > 0">
				<el-button type="primary" @click="handleBatchPush" :loading="pushLoading">
					<el-icon><Promotion /></el-icon>
					批量推送 ({{ selectedWorkorders.length }})
				</el-button>
			</div>

			<!-- 工单列表 -->
			<div class="workorder-table" v-loading="loading">
				<el-table :data="workorderList" style="width: 100%" @selection-change="handleSelectionChange">
					<el-table-column type="selection" width="55" />
					<el-table-column prop="workorder_no" label="工单号" width="150" />
					<el-table-column prop="merchant_name" label="商户名称" min-width="150" />
					<el-table-column prop="problem_description" label="问题描述" min-width="200" show-overflow-tooltip />
					<el-table-column prop="inspector_name" label="检查人" width="100" />
					<el-table-column prop="responsible_person_name" label="包保责任人" width="120" />
					<el-table-column label="逾期时长" width="120">
						<template #default="scope">
							<span :style="{ color: getOverdueColor(scope.row) }">
								{{ scope.row.overdue_duration_display || '-' }}
							</span>
						</template>
					</el-table-column>
					<el-table-column label="滞后级别" width="100">
						<template #default="scope">
							<el-tag :type="getLagLevelType(scope.row)" size="small">
								{{ scope.row.lag_level?.label || '-' }}
							</el-tag>
						</template>
					</el-table-column>
					<el-table-column prop="last_feedback" label="最后反馈" min-width="150" show-overflow-tooltip />
					<el-table-column label="操作" width="150" fixed="right">
						<template #default="scope">
							<el-button type="primary" link size="small" @click="handleViewDetail(scope.row.id)">
								查看详情
							</el-button>
							<el-button type="warning" link size="small" @click="handleTransfer(scope.row)">
								移交
							</el-button>
						</template>
					</el-table-column>
				</el-table>

				<!-- 分页 -->
				<div class="pagination-wrapper" v-if="pagination.total > 0">
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

				<!-- 空状态 -->
				<el-empty v-if="!loading && workorderList.length === 0" description="暂无待督办工单" />
			</div>
		</el-card>

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

		<!-- 移交弹窗 -->
		<el-dialog v-model="transferDialogVisible" title="工单移交" width="500px" :close-on-click-modal="false">
			<el-form :model="transferForm" label-width="100px">
				<el-form-item label="移交负责人" required>
					<table-selector
						v-model="transferForm.transfer_person"
						:table-config="transferPersonTableConfig"
						placeholder="请选择移交负责人"
					/>
				</el-form-item>
				<el-form-item label="备注">
					<el-input
						v-model="transferForm.transfer_remark"
						type="textarea"
						placeholder="请输入备注（可选）"
						:rows="3"
						maxlength="500"
						show-word-limit
					/>
				</el-form-item>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="transferDialogVisible = false">取 消</el-button>
					<el-button type="primary" :loading="transferLoading" @click="submitTransfer">确 定</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<script lang="ts" setup name="supervision">
import { ref, reactive, onMounted, shallowRef } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Promotion } from '@element-plus/icons-vue';
import * as api from './api';
import workorderDetail from '../workorder/detail.vue';
import { request, downloadFile } from '/@/utils/service';
import tableSelector from '/@/components/tableSelector/index.vue';

// 响应式数据
const loading = ref(false);
const pushLoading = ref(false);
const detailDrawerVisible = ref(false);
const currentWorkorderId = ref<number | string | null>(null);
const transferDialogVisible = ref(false);
const transferLoading = ref(false);

// 筛选表单
const filterForm = reactive({
	overdue_hours: '',
	hazard_level: '',
});

// 工单列表
const workorderList = ref<any[]>([]);
const selectedWorkorders = ref<number[]>([]);

// 移交表单
const transferForm = reactive({
	workorderId: null as number | null,
	transfer_person: null as number | null,
	transfer_remark: '',
});

// 移交负责人选择的 tableConfig
const transferPersonTableConfig = {
	url: '/api/system/user/',
	label: 'name',
	value: 'id',
	columns: [
		{ prop: 'name', label: '姓名', width: 120 },
		{ prop: 'username', label: '账号', width: 120 },
		{ prop: 'mobile', label: '电话', width: 150 },
	],
	isMultiple: false,
	pagination: true,
	extraParams: {} as any,
};

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
			workorderList.value = res.data?.list || res.data?.results || [];
			pagination.total = res.data?.total || 0;
		} else {
			ElMessage.error(res.msg || res.message || '加载工单列表失败');
		}
	} catch (error: any) {
		console.error('督办中心加载错误:', error);
		ElMessage.error(error?.message || '加载工单列表失败');
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

// 重置
const handleReset = () => {
	filterForm.overdue_hours = '';
	filterForm.hazard_level = '';
	handleFilter();
};

// 选择变化
const handleSelectionChange = (selection: any[]) => {
	selectedWorkorders.value = selection.map((item: any) => item.id);
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

		pushLoading.value = true;
		const res = await api.BatchPush({
			workorder_ids: selectedWorkorders.value,
			regulatory_unit: '监管单位',
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
	} finally {
		pushLoading.value = false;
	}
};

// 查看详情
const handleViewDetail = (id: number) => {
	currentWorkorderId.value = id;
	detailDrawerVisible.value = true;
};

// 移交
const handleTransfer = (workorder: any) => {
	transferForm.workorderId = workorder.id;
	transferForm.transfer_person = workorder.transfer_person || null;
	transferForm.transfer_remark = '';
	transferDialogVisible.value = true;
};

// 确认移交
const submitTransfer = async () => {
	if (!transferForm.workorderId) return;
	if (!transferForm.transfer_person) {
		ElMessage.warning('请选择移交负责人');
		return;
	}
	transferLoading.value = true;
	try {
		const res = await api.TransferWorkorder(transferForm.workorderId, {
			transfer_person: transferForm.transfer_person,
			transfer_remark: transferForm.transfer_remark,
		});
		if (res.code === 2000) {
			ElMessage.success('移交成功');
			transferDialogVisible.value = false;
			loadWorkorders();
		} else {
			ElMessage.error(res.msg || '移交失败');
		}
	} catch (error) {
		ElMessage.error('移交失败');
		console.error(error);
	} finally {
		transferLoading.value = false;
	}
};

// 获取逾期颜色
const getOverdueColor = (row: any) => {
	if (row.lag_level?.type === 'danger') return '#f56c6c';
	if (row.lag_level?.type === 'warning') return '#e6a23c';
	return '#909399';
};

// 获取滞后级别类型
const getLagLevelType = (row: any) => {
	if (row.lag_level?.type === 'danger') return 'danger';
	if (row.lag_level?.type === 'warning') return 'warning';
	return 'info';
};

// 导出督办工单
const handleExport = async () => {
	try {
		const params: any = {};
		if (filterForm.overdue_hours) {
			params.overdue_hours = filterForm.overdue_hours;
		}
		if (filterForm.hazard_level) {
			params.hazard_level = filterForm.hazard_level;
		}
		await downloadFile({
			url: '/api/supervision/workorder-export/',
			method: 'get',
			params: params,
		});
		ElMessage.success('导出成功');
	} catch (error) {
		ElMessage.error('导出失败');
		console.error(error);
	}
};

// 页面加载时获取数据
onMounted(() => {
	console.log('[督办中心] 页面已加载');
	loadWorkorders();
});
</script>

<style scoped lang="scss">
.supervision-container {
	padding: 20px;
	background: #f5f5f5;
	min-height: calc(100vh - 60px);

	.box-card {
		.card-header {
			display: flex;
			flex-direction: column;
			gap: 8px;

			.title {
				font-size: 20px;
				font-weight: 500;
				color: #303133;
			}

			.subtitle {
				font-size: 14px;
				color: #909399;
			}
		}

		.filter-form {
			margin-bottom: 20px;
		}

		.batch-actions {
			margin-bottom: 20px;
			text-align: right;
		}

		.workorder-table {
			.pagination-wrapper {
				margin-top: 20px;
				text-align: right;
			}
		}
	}
}
</style>
