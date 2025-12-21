<template>
	<fs-page>
		<fs-crud ref="crudRef" v-bind="crudBinding">
			<template #actionbar-right>
				<el-button type="primary" @click="handleBatchExport">
					批量导出
				</el-button>
				<importExcel api="api/task/" v-auth="'task:Import'">批量导入</importExcel>
			</template>
		</fs-crud>
		
		<!-- 工单列表对话框 -->
		<el-dialog
			v-model="workorderDialogVisible"
			title="对应工单"
			width="80%"
			:close-on-click-modal="false"
		>
			<div v-if="currentTask">
				<p style="margin-bottom: 15px;">
					<strong>任务名称：</strong>{{ currentTask.name }}
				</p>
			</div>
			<el-table
				v-loading="workorderLoading"
				:data="workorderList"
				border
				stripe
				style="width: 100%"
			>
				<el-table-column type="index" label="序号" width="70" align="center" />
				<el-table-column prop="workorder_no" label="工单号" min-width="150" align="center" />
				<el-table-column prop="merchant_name" label="商户名称" min-width="150" />
				<el-table-column prop="project" label="项目" min-width="120" />
				<el-table-column prop="hazard_level_display" label="隐患等级" width="100" align="center">
					<template #default="scope">
						<el-tag
							:type="scope.row.hazard_level === 'high' ? 'danger' : scope.row.hazard_level === 'medium' ? 'warning' : 'success'"
						>
							{{ scope.row.hazard_level_display || scope.row.hazard_level }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="status_display" label="状态" width="100" align="center">
					<template #default="scope">
						<el-tag
							:type="scope.row.status === 0 ? 'warning' : scope.row.status === 1 ? 'primary' : 'danger'"
						>
							{{ scope.row.status_display || scope.row.status }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="deadline" label="截止时间" width="120" align="center">
					<template #default="scope">
						{{ scope.row.deadline ? scope.row.deadline.split('T')[0] : '-' }}
					</template>
				</el-table-column>
				<el-table-column prop="report_time" label="上报时间" width="160" align="center">
					<template #default="scope">
						{{ scope.row.report_time ? scope.row.report_time.replace('T', ' ').substring(0, 19) : '-' }}
					</template>
				</el-table-column>
			</el-table>
			<div style="margin-top: 15px; text-align: right;">
				<el-pagination
					v-model:current-page="workorderPage"
					v-model:page-size="workorderPageSize"
					:total="workorderTotal"
					:page-sizes="[10, 20, 50, 100]"
					layout="total, sizes, prev, pager, next, jumper"
					@size-change="loadWorkorders"
					@current-change="loadWorkorders"
				/>
			</div>
		</el-dialog>
	</fs-page>
</template>

<script lang="ts" setup name="task">
import { ref, onMounted } from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import importExcel from '/@/components/importExcel/index.vue';
import { ElMessage } from 'element-plus';
import { downloadFile } from '/@/utils/service';
import * as taskApi from './api';

const workorderDialogVisible = ref(false);
const workorderLoading = ref(false);
const workorderList = ref([]);
const workorderPage = ref(1);
const workorderPageSize = ref(10);
const workorderTotal = ref(0);
const currentTask = ref<any>(null);

// 打开工单列表对话框
const openWorkorderDialog = async (task: any) => {
	currentTask.value = task;
	workorderDialogVisible.value = true;
	workorderPage.value = 1;
	await loadWorkorders();
};

// 加载工单列表
const loadWorkorders = async () => {
	if (!currentTask.value) return;
	
	workorderLoading.value = true;
	try {
		const res = await taskApi.GetTaskWorkorders(currentTask.value.id, {
			page: workorderPage.value,
			limit: workorderPageSize.value,
		});
		if (res.data) {
			workorderList.value = res.data.list || [];
			workorderTotal.value = res.data.total || 0;
		}
	} catch (error) {
		ElMessage.error('加载工单列表失败');
		console.error(error);
	} finally {
		workorderLoading.value = false;
	}
};

const context = {
	openWorkorderDialog,
};

const { crudBinding, crudRef, crudExpose } = useFs({ createCrudOptions, context });

// 批量导出
const handleBatchExport = async () => {
	try {
		// 获取当前的查询参数，用于导出筛选后的数据
		let query = {};
		if (crudExpose && typeof crudExpose.getSearchFormData === 'function') {
			query = crudExpose.getSearchFormData();
		}
		await downloadFile({
			url: '/api/task/export_data/',
			method: 'get',
			params: query,
			filename: '任务数据导出',
		});
		ElMessage.success('导出成功');
	} catch (error) {
		ElMessage.error('导出失败');
	}
};

// 页面打开后获取列表数据
onMounted(async () => {
	crudExpose.doRefresh();
});
</script>

