<template>
	<fs-page>
		<fs-crud ref="crudRef" v-bind="crudBinding">
			<template #header-middle>
				<el-tabs v-model="statusTab" @tab-click="onTabClick">
					<el-tab-pane label="全部" name="all"></el-tab-pane>
					<el-tab-pane label="待整改" name="pending"></el-tab-pane>
					<el-tab-pane label="待复查" name="review"></el-tab-pane>
					<el-tab-pane label="已逾期" name="overdue"></el-tab-pane>
					<el-tab-pane label="已完成" name="completed"></el-tab-pane>
				</el-tabs>
			</template>
			<template #actionbar-right>
				<el-button type="primary" @click="handleBatchExport">
					批量导出
				</el-button>
				<importExcel api="api/workorder/" v-auth="'workorder:Import'">批量导入</importExcel>
				<el-button type="warning" @click="handleBatchSupervise">
					<el-icon><Warning /></el-icon>
					批量一键督办
				</el-button>
			</template>
		</fs-crud>
		
		<!-- 工单详情抽屉 -->
		<el-drawer
			v-model="detailDrawerVisible"
			title="工单详情"
			direction="rtl"
			size="80%"
			:close-on-click-modal="true"
			destroy-on-close
		>
			<workorder-detail
				v-if="detailDrawerVisible && currentWorkorderId"
				:workorder-id="currentWorkorderId"
			/>
		</el-drawer>
	</fs-page>
</template>

<script lang="ts" setup name="workorder">
import { ref, onMounted } from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import { Warning } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import importExcel from '/@/components/importExcel/index.vue';
import { downloadFile } from '/@/utils/service';
import workorderDetail from './detail.vue';

const statusTab = ref('all');
const detailDrawerVisible = ref(false);
const currentWorkorderId = ref<number | string | null>(null);
const context: any = { 
	statusTab,
	openDetailDrawer: (id: number | string) => {
		currentWorkorderId.value = id;
		detailDrawerVisible.value = true;
	}
};

const { crudBinding, crudRef, crudExpose } = useFs({ createCrudOptions, context });

// 标签切换
const onTabClick = (tab: any) => {
	statusTab.value = tab.paneName;
	// 更新 context 中的 statusTab（确保响应式更新）
	context.statusTab = tab.paneName;
	// 刷新列表
	if (crudExpose) {
		crudExpose.doRefresh();
	}
};

// 批量导出
const handleBatchExport = async () => {
	try {
		// 获取当前的查询参数，用于导出筛选后的数据
		let query: any = {};
		if (crudExpose && typeof crudExpose.getSearchFormData === 'function') {
			query = crudExpose.getSearchFormData();
		}
		
		// 根据当前选中的标签添加状态筛选
		const statusMap: any = {
			all: undefined, // 全部，不筛选
			pending: 0, // 待整改
			review: 1, // 待复查
			overdue: 3, // 已逾期
			completed: 2, // 已完成
		};
		const statusValue = statusMap[statusTab.value];
		if (statusValue !== undefined) {
			query.status = statusValue;
		} else {
			// 全部时，确保不传status参数
			delete query.status;
		}
		
		await downloadFile({
			url: '/api/workorder/export_data/',
			method: 'get',
			params: query,
			filename: '工单数据导出',
		});
		ElMessage.success('导出成功');
	} catch (error) {
		ElMessage.error('导出失败');
	}
};

// 批量一键督办
const handleBatchSupervise = () => {
	const selectedRows = crudExpose.getSelectedRows();
	if (selectedRows.length === 0) {
		ElMessage.warning('请先选择要督办的工单');
		return;
	}
	ElMessage.success(`已对 ${selectedRows.length} 个工单执行批量督办`);
};

// 页面打开后获取列表数据
onMounted(async () => {
	crudExpose.doRefresh();
});
</script>

