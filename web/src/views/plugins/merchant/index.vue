<template>
	<fs-page>
		<fs-crud ref="crudRef" v-bind="crudBinding">
			<template #actionbar-right>



				<el-button type="primary" @click="handleBatchExportAll">
					批量导出全部
				</el-button>
				<el-button type="success" @click="handleBatchGenerateQrcode">
					批量生成二维码
				</el-button>
				<el-button type="warning" @click="handleBatchExportQrcode">
					批量导出二维码
				</el-button>
				<el-text type="info" size="small" style="padding-left: 8px;">
  					生成二维码后请刷新网页，可右键点击二维码下载
				</el-text>

				<importExcel api="api/merchant/" v-auth="'merchant:Import'">批量导入</importExcel>
			</template>
		</fs-crud>
	</fs-page>
</template>

<script lang="ts" setup name="merchant">
import { onMounted } from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import importExcel from '/@/components/importExcel/index.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import * as api from './api';
import { downloadFile, request } from '/@/utils/service';

const { crudBinding, crudRef, crudExpose } = useFs({ createCrudOptions });

// 批量导出全部
const handleBatchExportAll = async () => {
	try {
		await downloadFile({
			url: '/api/merchant/export_data/',
			method: 'get',
			filename: '商户数据导出',
		});
		ElMessage.success('导出成功');
	} catch (error) {
		ElMessage.error('导出失败');
	}
};

// 批量生成二维码（默认生成全部）
const handleBatchGenerateQrcode = async () => {
	try {
		await ElMessageBox.confirm(
			'确定要为所有商户生成二维码吗？',
			'批量生成二维码',
			{
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);
		
		// 不传ids参数，后端会处理全部数据
		const res = await api.BatchGenerateQrcode({ ids: [] });
		if (res.code === 2000) {
			ElMessage.success(res.msg || '批量生成二维码成功，请刷新页面查看');
			crudExpose.doRefresh();
		} else {
			ElMessage.error(res.msg || '批量生成二维码失败');
		}
	} catch (error: any) {
		if (error !== 'cancel') {
			ElMessage.error('批量生成二维码失败');
		}
	}
};

// 批量导出二维码（默认导出全部）
const handleBatchExportQrcode = async () => {
	try {
		// 不传ids参数，后端会处理全部数据
		// 使用request直接处理zip文件下载
		const res = await request({
			url: '/api/merchant/batch_export_qrcode/',
			method: 'post',
			data: {},
			responseType: 'blob',
		});
		
		// 检查响应类型
		if (res.headers && res.headers['content-type'] === 'application/json') {
			// JSON响应，说明有错误
			const text = await res.data.text();
			const jsonData = JSON.parse(text);
			ElMessage.error(jsonData.msg || '二维码导出失败');
			return;
		}
		
		// 处理zip文件下载
		const blob = new Blob([res.data], { type: 'application/zip' });
		const url = window.URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		
		// 从响应头获取文件名，如果没有则使用默认名称
		let filename = `商户二维码_${new Date().getTime()}.zip`;
		if (res.headers && res.headers['content-disposition']) {
			const disposition = res.headers['content-disposition'];
			// 支持 filename*=UTF-8'' 格式和 filename= 格式
			let filenameMatch = disposition.match(/filename\*=UTF-8''(.+)/);
			if (filenameMatch) {
				filename = decodeURIComponent(filenameMatch[1]);
			} else {
				filenameMatch = disposition.match(/filename="?([^";]+)"?/);
				if (filenameMatch) {
					filename = decodeURIComponent(filenameMatch[1]);
				}
			}
		}
		
		link.download = filename;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		window.URL.revokeObjectURL(url);
		
		ElMessage.success('二维码导出成功');
	} catch (error: any) {
		if (error?.response?.data) {
			// 尝试解析错误消息
			try {
				const blob = error.response.data;
				const text = await blob.text();
				const jsonData = JSON.parse(text);
				ElMessage.error(jsonData.msg || '二维码导出失败');
			} catch {
				ElMessage.error('二维码导出失败');
			}
		} else {
			ElMessage.error('二维码导出失败');
		}
	}
};

// 页面打开后获取列表数据
onMounted(async () => {
	crudExpose.doRefresh();
});
</script>
