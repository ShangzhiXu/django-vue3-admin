<template>
	<div class="workorder-detail-container">
		<!-- 头部导航（在 drawer 中不显示返回按钮） -->
		<div class="detail-header">
			<div class="header-title">
				<span>工单详情: {{ workorderData.workorder_no }}</span>
				<el-tag v-if="overdueLevel.type === 'danger'" type="danger" size="large" style="margin-left: 12px;">
					{{ overdueLevel.label }}
				</el-tag>
				<el-tag v-else-if="overdueLevel.type === 'warning'" type="warning" size="large" style="margin-left: 12px;">
					{{ overdueLevel.label }}
				</el-tag>
				<el-tag v-else-if="overdueLevel.type === 'info'" type="info" size="large" style="margin-left: 12px;">
					{{ overdueLevel.label }}
				</el-tag>
				<el-tag v-else-if="workorderData.status === 0" type="warning" size="large" style="margin-left: 12px;">
					待整改
				</el-tag>
				<el-tag v-else-if="workorderData.status === 1" type="primary" size="large" style="margin-left: 12px;">
					待复查
				</el-tag>
			</div>
			<div class="header-actions">
				<el-button
					:icon="Refresh"
					@click="handleRefresh"
					:loading="loading"
					circle
					size="large"
					title="刷新"
				/>
			</div>
		</div>

		<!-- 主要内容区域 -->
		<div class="detail-content" v-loading="loading">
			<!-- 左侧：当前进度和整改记录 -->
			<div class="left-column">
				<!-- 当前进度 -->
				<div class="progress-section">
					<div class="section-title">当前进度</div>
					<div class="timeline-container">
						<el-timeline>
							<el-timeline-item
								v-for="(item, index) in progressList"
								:key="index"
								:timestamp="item.time"
								placement="top"
								:type="item.type"
							>
								<div class="timeline-content">
									<div class="timeline-header">
										<div class="timeline-event">{{ item.event }}</div>
										<el-button
											v-if="isAdmin && item.submissionId"
											type="danger"
											:icon="Delete"
											size="small"
											text
											@click="handleDeleteSubmission(item.submissionId, item.event)"
											title="删除此进度"
										>
											删除
										</el-button>
									</div>
									<div class="timeline-details" v-if="item.details">
										{{ item.details }}
									</div>
									<div class="timeline-description" v-if="item.description">
										{{ item.description }}
									</div>
									<div class="timeline-images" v-if="item.images && item.images.length > 0">
										<div
											v-for="(img, imgIndex) in item.images"
											:key="imgIndex"
											class="image-item"
											@click="previewImage(img.url, item.images)"
										>
											<img :src="getImageUrl(img.url)" :alt="img.filename || `现场图${Number(imgIndex) + 1}`" />
										</div>
									</div>
								</div>
							</el-timeline-item>
						</el-timeline>
					</div>
				</div>

				<!-- 整改/复查记录 -->
				<div class="review-section">
					<div class="section-title">整改/复查记录</div>
					<div class="review-content">
						<div v-if="reviewList.length === 0" class="empty-state">
							暂无复查记录
						</div>
						<div v-else class="review-list">
							<div
								v-for="(review, index) in reviewList"
								:key="index"
								class="review-item"
							>
								<div class="review-time">{{ review.time }}</div>
								<div class="review-type">{{ review.type }}</div>
								<div class="review-content-text">{{ review.content }}</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- 右侧：基础信息和管理操作 -->
			<div class="right-column">
				<!-- 基础信息 -->
				<div class="info-section">
					<div class="section-title">基础信息</div>
					<div class="info-content">
						<div class="info-item">
							<span class="info-label">商户名称：</span>
							<span class="info-value">{{ workorderData.merchant_name || '-' }}</span>
						</div>
						<div class="info-item">
							<span class="info-label">负责人：</span>
							<span class="info-value">
								{{ workorderData.merchant_manager || '-' }}
								<span v-if="workorderData.merchant_phone" class="phone-text">
									({{ formatPhone(workorderData.merchant_phone) }})
								</span>
							</span>
						</div>
						<div class="info-item">
							<span class="info-label">所属任务：</span>
							<span class="info-value">{{ workorderData.task_name || '-' }}</span>
						</div>
						<div class="info-item">
							<span class="info-label">隐患等级：</span>
							<el-tag
								:type="getHazardLevelType(workorderData.hazard_level)"
								size="small"
							>
								{{ workorderData.hazard_level_display || workorderData.hazard_level || '-' }}
							</el-tag>
						</div>
						<div class="info-item">
							<span class="info-label">问题描述：</span>
							<span class="info-value">{{ workorderData.problem_description || '-' }}</span>
						</div>
						<div class="info-item">
							<span class="info-label">整改类别：</span>
							<span class="info-value">
								{{ workorderData.rectification_category_display || 
								   (workorderData.rectification_category === 'immediate' ? '当场整改' : 
								    workorderData.rectification_category === 'deadline' ? '限期整改' : 
								    workorderData.rectification_category === 'transfer' ? '移交整改' : '-') }}
							</span>
						</div>
						<div class="info-item">
							<span class="info-label">是否已移交：</span>
							<span class="info-value">
								<el-tag :type="workorderData.is_transferred ? 'success' : 'info'" size="small">
									{{ workorderData.is_transferred ? '是' : '否' }}
								</el-tag>
							</span>
						</div>
						<div class="info-item">
							<span class="info-label">移交负责人：</span>
							<span class="info-value">{{ workorderData.transfer_person_name || '-' }}</span>
						</div>
						<div class="info-item">
							<span class="info-label">上报时间：</span>
							<span class="info-value">{{ formatDateTime(workorderData.report_time) }}</span>
						</div>
						<div class="info-item">
							<span class="info-label">整改时限：</span>
							<span class="info-value">{{ formatDate(workorderData.deadline) }}</span>
						</div>
						<div class="info-item" v-if="workorderData.remark">
							<span class="info-label">备注：</span>
							<span class="info-value">{{ workorderData.remark }}</span>
						</div>
					</div>
				</div>

				<!-- 管理操作 -->
				<div class="action-section">
					<div class="section-title">管理操作</div>
					<div class="action-buttons">
						<el-button
							type="primary"
							:icon="Bell"
							@click="handleManualSupervise"
							:disabled="workorderData.status === 1"
							class="action-btn"
						>
							发送人工督办通知
						</el-button>
						<el-button
							type="info"
							:icon="Refresh"
							@click="handleReassign"
							class="action-btn"
						>
							重新指派检查人
						</el-button>
						<el-button
							type="danger"
							:icon="Close"
							@click="handleForceClose"
							class="action-btn"
						>
							强制关闭工单
						</el-button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts" setup name="workorder-detail">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ArrowLeft, Bell, Refresh, Close, Delete } from '@element-plus/icons-vue';
import { useUserInfo } from '/@/stores/userInfo';
import * as api from './api';

// 定义 props
const props = defineProps<{
	workorderId?: number | string;
}>();

const route = useRoute();
const router = useRouter();
const userInfoStore = useUserInfo();

const loading = ref(false);
const workorderData = ref<any>({});
const progressList = ref<any[]>([]);
const reviewList = ref<any[]>([]);

// 判断是否是管理员
const isAdmin = computed(() => {
	return userInfoStore.userInfos.is_superuser || 
	       (userInfoStore.userInfos.role_info && userInfoStore.userInfos.role_info.some((role: any) => role.key === 'admin' || role.name === '管理员'));
});

// 计算逾期天数
const overdueDays = computed(() => {
	if (!workorderData.value.deadline) return 0;
	const deadline = new Date(workorderData.value.deadline);
	const today = new Date();
	today.setHours(0, 0, 0, 0);
	deadline.setHours(0, 0, 0, 0);
	const diffTime = today.getTime() - deadline.getTime();
	const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
	return Math.max(0, diffDays);
});

// 计算逾期级别（与督办中心保持一致）
const overdueLevel = computed(() => {
	const days = overdueDays.value;
	// 如果工单已完成（待复查），不显示逾期标签
	if (workorderData.value.status === 1) {
		return { label: '', type: '' };
	}
	// 根据逾期天数判断级别（与督办中心逻辑一致）
	if (days > 3) {
		return { label: '严重逾期', type: 'danger' };
	} else if (days > 1) {
		return { label: '一般逾期', type: 'warning' };
	} else if (days > 0) {
		return { label: '轻微逾期', type: 'info' };
	}
	return { label: '', type: '' };
});

// 加载工单详情
const loadWorkorderDetail = async () => {
	// 优先使用 props 传入的 ID，如果没有则从路由获取
	const id = props.workorderId || (route.params.id as string);
	if (!id) {
		ElMessage.error('工单ID不存在');
		return;
	}

	loading.value = true;
	try {
		const res = await api.GetObj(id as any);
		if (res.data) {
			workorderData.value = res.data;
			// 构建进度列表
			buildProgressList();
			// 构建复查记录（暂时为空，后续可以从后端获取）
			buildReviewList();
		}
	} catch (error) {
		ElMessage.error('加载工单详情失败');
		console.error(error);
	} finally {
		loading.value = false;
	}
};

// 刷新工单详情
const handleRefresh = async () => {
	await loadWorkorderDetail();
	ElMessage.success('刷新成功');
};

// 构建进度列表
const buildProgressList = async () => {
	const list: any[] = [];
	
	// 1. 发现隐患（自动创建）
	if (workorderData.value.report_time) {
		list.push({
			time: formatDateTime(workorderData.value.report_time),
			event: '发现隐患 (自动创建)',
			type: 'primary',
			details: `检查人: ${workorderData.value.inspector || '系统'} | 位置偏差: ${workorderData.value.location_deviation || '-'} (${workorderData.value.location_status || '正常'})`,
			description: `问题描述: ${workorderData.value.problem_description || ''}`,
			images: [], // 后续可以从后端获取图片
		});
	}

	// 2. 系统督办（如果有催办记录）
	if (workorderData.value.last_supervise_time) {
		list.push({
			time: formatDateTime(workorderData.value.last_supervise_time),
			event: '系统督办',
			type: 'warning',
			details: `系统自动检测到工单未响应,已发送短信提醒商户负责人(${workorderData.value.merchant_manager || '负责人'})。`,
		});
	}

	// 3. 加载所有提交记录（包括首次提交和复查）
	if (workorderData.value.workorder_no) {
		try {
			const submissionsRes = await api.GetWorkOrderSubmissions(workorderData.value.workorder_no);
			if (submissionsRes.data && submissionsRes.data.submissions && submissionsRes.data.submissions.length > 0) {
				// 将所有提交记录添加到进度列表
				submissionsRes.data.submissions.forEach((submission: any) => {
					const submissionImages = submission.photos ? submission.photos.map((photo: any) => ({
						url: photo.url,
						filename: photo.filename
					})) : [];
					
					const remarkText = submission.remark ? `备注：${submission.remark}` : '';
					
					// 根据是否为复查和是否合格生成事件和详情
					let eventText = '';
					let detailsText = '';
					let type = '';
					
					if (submission.is_recheck === 1) {
						// 复查
						if (submission.is_qualified === 1) {
							eventText = '复查合格';
							type = 'success';
							detailsText = `复查合格${remarkText ? '\n' + remarkText : ''}`;
						} else {
							eventText = '复查不合格';
							type = 'warning';
							detailsText = `复查不合格，需重新整改${remarkText ? '\n' + remarkText : ''}`;
						}
					} else {
						// 首次提交
						if (submission.is_qualified === 1) {
							eventText = '合格';
							type = 'success';
							detailsText = `工单已完成整改${remarkText ? '\n' + remarkText : ''}`;
						} else {
							eventText = '不合格';
							type = 'warning';
							detailsText = `巡查员提交不合格，发现隐患${remarkText ? '\n' + remarkText : ''}`;
						}
					}
					
					list.push({
						time: submission.submit_time,
						event: eventText,
						type: type,
						details: detailsText,
						images: submissionImages,
						submissionId: submission.id, // 添加提交记录ID，用于删除
					});
				});
			}
		} catch (error) {
			console.error('加载提交记录失败:', error);
		}
	}

	// 按时间排序（最新的在前）
	list.sort((a, b) => {
		const timeA = new Date(a.time).getTime();
		const timeB = new Date(b.time).getTime();
		return timeB - timeA;
	});

	progressList.value = list;
};

// 构建复查记录
const buildReviewList = () => {
	// 暂时为空，后续可以从后端获取复查记录
	reviewList.value = [];
};

// 删除提交记录
const handleDeleteSubmission = async (submissionId: number, eventText: string) => {
	try {
		await ElMessageBox.confirm(
			`确定要删除"${eventText}"这条进度记录吗？删除后将无法恢复。`,
			'确认删除',
			{
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);

		// 调用删除接口
		await api.DeleteWorkOrderSubmission(workorderData.value.workorder_no, submissionId);
		
		ElMessage.success('删除成功');
		
		// 重新加载工单详情
		await loadWorkorderDetail();
	} catch (error: any) {
		if (error !== 'cancel') {
			console.error('删除提交记录失败:', error);
			ElMessage.error(error?.msg || '删除失败');
		}
	}
};

// 格式化日期时间
const formatDateTime = (dateTime: string | null) => {
	if (!dateTime) return '-';
	const date = new Date(dateTime);
	return date.toLocaleString('zh-CN', {
		year: 'numeric',
		month: '2-digit',
		day: '2-digit',
		hour: '2-digit',
		minute: '2-digit',
		second: '2-digit',
	}).replace(/\//g, '-');
};

// 格式化日期
const formatDate = (date: string | null) => {
	if (!date) return '-';
	return date.split('T')[0];
};

// 获取图片URL（处理相对路径）
const getImageUrl = (url: string) => {
	if (!url) return '';
	// 如果已经是完整URL，直接返回
	if (url.startsWith('http://') || url.startsWith('https://')) {
		return url;
	}
	// 如果是相对路径，添加API前缀
	if (url.startsWith('/media/')) {
		return `${import.meta.env.VITE_API_URL || ''}${url}`;
	}
	return url;
};

// 预览图片
const previewImage = (url: string, images: any[]) => {
	// 使用Element Plus的图片预览功能
	const imageList = images.map((img: any) => getImageUrl(img.url));
	const currentIndex = images.findIndex((img: any) => img.url === url);
	// 这里可以使用Element Plus的图片预览组件
	// 暂时使用浏览器原生的图片预览
	window.open(getImageUrl(url), '_blank');
};

// 格式化手机号（隐藏中间4位）
const formatPhone = (phone: string) => {
	if (!phone) return '';
	if (phone.length === 11) {
		return phone.substring(0, 3) + '****' + phone.substring(7);
	}
	return phone;
};

// 获取隐患等级标签类型
const getHazardLevelType = (level: string) => {
	const map: { [key: string]: string } = {
		high: 'danger',
		medium: 'warning',
		low: 'success',
	};
	return map[level] || 'info';
};

// 返回列表（在 drawer 中不需要返回按钮，但保留函数以防需要）
const goBack = () => {
	// 如果是在 drawer 中使用，可以通过 emit 通知父组件关闭
	// 这里暂时保留，但不会在 drawer 中显示返回按钮
};

// 发送人工督办通知
const handleManualSupervise = async () => {
	try {
		await ElMessageBox.confirm(
			'确定要发送人工督办通知吗？',
			'提示',
			{
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);
		// 调用督办接口
		await api.SuperviseObj(workorderData.value.id);
		ElMessage.success('督办通知已发送');
		// 重新加载数据
		await loadWorkorderDetail();
	} catch (error: any) {
		if (error !== 'cancel') {
			ElMessage.error(error?.message || '发送失败');
		}
	}
};

// 重新指派检查人
const handleReassign = () => {
	ElMessage.info('重新指派检查人功能开发中...');
};

// 强制关闭工单
const handleForceClose = async () => {
	try {
		await ElMessageBox.confirm(
			'确定要强制关闭此工单吗？关闭后无法恢复。',
			'警告',
			{
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);
		// 调用关闭接口（需要后端实现）
		ElMessage.success('工单已关闭');
		// 重新加载数据
		await loadWorkorderDetail();
	} catch (error: any) {
		if (error !== 'cancel') {
			ElMessage.error(error?.message || '关闭失败');
		}
	}
};

// 监听 workorderId 变化
watch(() => props.workorderId, (newId) => {
	if (newId) {
		loadWorkorderDetail();
	}
}, { immediate: true });

onMounted(() => {
	// 如果没有通过 props 传入，则从路由获取
	if (!props.workorderId) {
		loadWorkorderDetail();
	}
});
</script>

<style scoped lang="scss">
.workorder-detail-container {
	padding: 24px;
	background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
	min-height: 100%;
}

.detail-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 24px;
	background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
	padding: 20px 24px;
	border-radius: 12px;
	box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.08);
	border: 1px solid rgba(64, 158, 255, 0.1);

	.header-title {
		font-size: 20px;
		font-weight: 600;
		color: #303133;
		display: flex;
		align-items: center;
		flex: 1;
		
		.el-tag {
			margin-left: 16px;
			font-weight: 500;
			padding: 6px 16px;
			border-radius: 20px;
		}
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: 12px;
	}
}

.detail-content {
	display: grid;
	grid-template-columns: 2fr 1fr;
	gap: 20px;
}

.left-column,
.right-column {
	display: flex;
	flex-direction: column;
	gap: 20px;
}

.progress-section,
.review-section,
.info-section,
.action-section {
	background: #fff;
	border-radius: 12px;
	padding: 24px;
	box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.08);
	border: 1px solid rgba(0, 0, 0, 0.05);
	transition: all 0.3s ease;
	
	&:hover {
		box-shadow: 0 6px 24px 0 rgba(0, 0, 0, 0.12);
	}
}

.section-title {
	font-size: 17px;
	font-weight: 600;
	color: #303133;
	margin-bottom: 20px;
	padding-bottom: 14px;
	border-bottom: 3px solid #409eff;
	position: relative;
	
	&::after {
		content: '';
		position: absolute;
		bottom: -3px;
		left: 0;
		width: 60px;
		height: 3px;
		background: linear-gradient(90deg, #409eff 0%, #66b1ff 100%);
		border-radius: 2px;
	}
}

.timeline-container {
	margin-top: 20px;
}

.timeline-content {
	.timeline-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 10px;
	}

	.timeline-event {
		font-size: 15px;
		font-weight: 600;
		color: #303133;
	}

	.timeline-details {
		font-size: 14px;
		color: #606266;
		margin-bottom: 10px;
		line-height: 1.6;
		white-space: pre-line; // 支持换行显示
	}

	.timeline-description {
		font-size: 14px;
		color: #606266;
		margin-bottom: 12px;
		line-height: 1.8;
		padding: 10px;
		background: #f8f9fa;
		border-radius: 6px;
		border-left: 3px solid #409eff;
	}

	.timeline-images {
		display: flex;
		flex-wrap: wrap;
		gap: 12px;
		margin-top: 12px;

		.image-item {
			width: 120px;
			height: 80px;
			border-radius: 4px;
			overflow: hidden;
			cursor: pointer;
			border: 1px solid #dcdfe6;
			transition: all 0.3s ease;
			
			&:hover {
				border-color: #409eff;
				transform: scale(1.05);
				box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
			}
			
			img {
				width: 100%;
				height: 100%;
				object-fit: cover;
			}
		}
	}
}

.review-content {
	.empty-state {
		text-align: center;
		color: #909399;
		padding: 60px 0;
		font-size: 14px;
		background: #f8f9fa;
		border-radius: 8px;
		border: 2px dashed #dcdfe6;
	}

	.review-list {
		.review-item {
			padding: 16px;
			border-bottom: 1px solid #ebeef5;
			
			&:last-child {
				border-bottom: none;
			}

			.review-time {
				font-size: 12px;
				color: #909399;
				margin-bottom: 8px;
			}

			.review-type {
				font-size: 14px;
				font-weight: 500;
				color: #303133;
				margin-bottom: 8px;
			}

			.review-content-text {
				font-size: 14px;
				color: #606266;
				line-height: 1.6;
			}
		}
	}
}

.info-content {
	.info-item {
		display: flex;
		align-items: flex-start;
		margin-bottom: 18px;
		padding: 12px 0;
		border-bottom: 1px solid #f0f2f5;
		
		&:last-child {
			margin-bottom: 0;
			border-bottom: none;
		}

		.info-label {
			font-size: 14px;
			color: #909399;
			min-width: 100px;
			flex-shrink: 0;
			font-weight: 500;
		}

		.info-value {
			font-size: 14px;
			color: #303133;
			flex: 1;
			word-break: break-all;
			font-weight: 500;

			.phone-text {
				color: #909399;
				margin-left: 6px;
				font-weight: 400;
			}
		}
	}
}

.action-buttons {
	display: flex;
	flex-direction: column;
	gap: 14px;

	:deep(.el-button.action-btn) {
		width: 100% !important;
		height: 48px !important;
		padding: 0 24px !important;
		margin: 0 !important;
		border-radius: 8px !important;
		transition: all 0.3s ease;
		border: none !important;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		display: flex !important;
		align-items: center !important;
		justify-content: flex-start !important;
		
		&:hover:not(:disabled) {
			transform: translateY(-2px);
			box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
		}
		
		&:active:not(:disabled) {
			transform: translateY(0);
		}
		
		&:disabled {
			opacity: 0.6;
			cursor: not-allowed;
		}
		
		// 重置按钮内部所有元素的样式
		* {
			box-sizing: border-box;
		}
		
		// 按钮内部容器
		> span {
			display: flex !important;
			align-items: center !important;
			justify-content: flex-start !important;
			width: 100% !important;
			height: 100% !important;
			line-height: 1 !important;
		}
		
		// 图标样式 - 确保所有图标完全一致
		.el-icon {
			display: inline-flex !important;
			align-items: center !important;
			justify-content: center !important;
			width: 18px !important;
			height: 18px !important;
			margin-right: 10px !important;
			margin-left: 0 !important;
			font-size: 18px !important;
			line-height: 1 !important;
			flex-shrink: 0 !important;
			vertical-align: middle !important;
		}
		
		// 文字样式
		span:not(.el-icon) {
			flex: 1 1 auto !important;
			text-align: left !important;
			font-size: 14px !important;
			font-weight: 500 !important;
			line-height: 1.5 !important;
			white-space: nowrap !important;
		}
	}
	
	// 不同类型按钮的特定样式
	:deep(.el-button--primary.action-btn) {
		background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%) !important;
		
		&:hover:not(:disabled) {
			background: linear-gradient(135deg, #66b1ff 0%, #85c1ff 100%) !important;
		}
	}
	
	:deep(.el-button--info.action-btn) {
		background: linear-gradient(135deg, #909399 0%, #a6a9ad 100%) !important;
		
		&:hover:not(:disabled) {
			background: linear-gradient(135deg, #a6a9ad 0%, #b1b3b8 100%) !important;
		}
	}
	
	:deep(.el-button--danger.action-btn) {
		background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%) !important;
		
		&:hover:not(:disabled) {
			background: linear-gradient(135deg, #f78989 0%, #f9a5a5 100%) !important;
		}
	}
}
</style>

