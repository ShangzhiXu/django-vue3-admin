import * as api from './api';
import { UserPageQuery, AddReq, DelReq, EditReq, CreateCrudOptionsProps, CreateCrudOptionsRet, dict } from '@fast-crud/fast-crud';
import { ElMessage, ElButton } from 'element-plus';
import { getBaseURL } from '/@/utils/baseUrl';
import { h } from 'vue';

export const createCrudOptions = function ({ crudExpose }: CreateCrudOptionsProps): CreateCrudOptionsRet {
	const pageRequest = async (query: UserPageQuery) => {
		return await api.GetList(query);
	};
	const editRequest = async ({ form, row }: EditReq) => {
		form.id = row.id;
		return await api.UpdateObj(form);
	};
	const delRequest = async ({ row }: DelReq) => {
		return await api.DelObj(row.id);
	};
	const addRequest = async ({ form }: AddReq) => {
		return await api.AddObj(form);
	};
	return {
		crudOptions: {
			request: {
				pageRequest,
				addRequest,
				editRequest,
				delRequest,
			},
			pagination: {
				pageSize: 10,
				pageSizes: [10, 20, 50, 100],
			},
			actionbar: {
				buttons: {
					add: {
						show: true,
						text: '新增商户',
					},
					import: {
						show: true,
						text: '批量导入',
						type: 'primary',
						icon: 'ele-Upload',
						tooltip: '批量导入商户数据',
						// 注意：实际导入功能通过 index.vue 中的 importExcel 组件实现
						// 此按钮作为配置展示，实际导入请使用右上角的"批量导入"按钮
						click: () => {
							// 可以在这里添加导入逻辑，或触发自定义事件
							// 实际使用时建议通过 index.vue 中的 importExcel 组件
						},
					},
				},
			},
			search: {
				show: false, // 默认不展示搜索栏
			},
			rowHandle: {
				fixed: 'right',
				width: 260,
				buttons: {
					view: {
						show: true,
						type: 'text',
					},
					edit: {
						show: true,
						type: 'text',
					},
					remove: {
						show: true,
						type: 'text',
					},
					generateQrcode: {
						text: '生成二维码',
						type: 'text',
						click: async (context: any) => {
							try {
								const res = await api.GenerateQrcode(context.row.id);
								if (res.code === 2000) {
									crudExpose.doRefresh();
									ElMessage.success('二维码生成成功');
								} else {
									ElMessage.error(res.msg || '二维码生成失败');
								}
							} catch (error) {
								ElMessage.error('二维码生成失败');
							}
						},
					},
				},
			},
			columns: {
				_index: {
					title: '序号',
					form: { show: false },
					column: {
						align: 'center',
						width: '70px',
						columnSetDisabled: true,
						formatter: (context: any) => {
							let index = (context.index ?? 0) + 1;
							let pagination = crudExpose!.crudBinding.value.pagination;
							return ((pagination!.currentPage ?? 1) - 1) * pagination!.pageSize + index;
						},
					},
				},
				id: {
					title: 'ID',
					type: 'number',
					search: {
						show: false,
					},
					column: {
						show: false,  // 隐藏数据库ID列
					},
					form: {
						show: false,
					},
				},
				merchant_code: {
					title: '商户标识码',
					type: 'input',
					search: {
						show: true,
						component: {
							props: {
								clearable: true,
							},
							placeholder: '请输入商户标识码',
						},
					},
					column: {
						align: 'center',
						minWidth: 180,
						copyable: true,  // 可以复制
					},
					form: {
						show: false,  // 表单中不显示，由系统自动生成
					},
				},
				name: {
					title: '商户名称',
					type: 'input',
					search: {
						show: true,
						component: {
							props: {
								clearable: true,
							},
							placeholder: '请输入商户名称',
						},
					},
					column: {
						minWidth: 150,
					},
					form: {
						rules: [
							{ required: true, message: '请输入商户名称' },
						],
						component: {
							placeholder: '请输入商户名称',
						},
					},
				},
				manager: {
					title: '负责人',
					type: 'input',
					search: {
						show: true,
						component: {
							props: {
								clearable: true,
							},
							placeholder: '请输入负责人',
						},
					},
					column: {
						minWidth: 120,
					},
					form: {
						component: {
							placeholder: '请输入负责人',
						},
					},
				},
				phone: {
					title: '联系电话',
					type: 'input',
					search: {
						show: true,
						component: {
							props: {
								clearable: true,
							},
							placeholder: '请输入联系电话',
						},
					},
					column: {
						minWidth: 130,
					},
					form: {
						rules: [
							{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码' },
						],
						component: {
							placeholder: '请输入联系电话',
						},
					},
				},
				address: {
					title: '地址',
					type: 'textarea',
					search: {
						show: true,
						component: {
							props: {
								clearable: true,
							},
							placeholder: '请输入地址',
						},
					},
					column: {
						minWidth: 200,
						showOverflowTooltip: true,
					},
					form: {
						component: {
							placeholder: '请输入地址',
							props: {
								rows: 3,
							},
						},
					},
				},
				gps_status: {
					title: 'GPS状态',
					type: 'dict-select',
					dict: dict({
						data: [
							{ label: '已开启', value: 1 },
							{ label: '已关闭', value: 0 },
						],
					}),
					search: {
						show: true,
					},
					column: {
						minWidth: 100,
						align: 'center',
						component: {
							name: 'fs-dict-tag',
						},
					},
					form: {
						value: 0,
						component: {
							placeholder: '请选择GPS状态',
						},
					},
				},
				qr_code: {
					title: '二维码',
					type: 'input',
					column: {
						minWidth: 150,
						align: 'center',
						formatter: ({ row }: any) => {
							if (row.merchant_code) {
								const qrCodeUrl = getBaseURL(`media/qrcode/merchant_qrcode_${row.merchant_code}.png`);
								return h('div', { style: 'display: flex; justify-content: center; align-items: center;' }, [
									h('img', {
										src: qrCodeUrl,
										style: 'width: 60px; height: 60px; object-fit: contain; cursor: pointer;',
										onClick: () => window.open(qrCodeUrl, '_blank'),
										onError: (e: any) => {
											e.target.style.display = 'none';
										},
									}),
								]);
							}
							return '-';
						},
					},
					form: {
						show: false,
						helper: {
							render({ form }: any) {
								// 如果已有merchant_code，显示二维码预览
								const qrCodeUrl = form.merchant_code 
									? getBaseURL(`media/qrcode/merchant_qrcode_${form.merchant_code}.png`)
									: null;
								
								return h('div', { style: 'margin-top: 8px;' }, [
									// 生成二维码按钮
									h(ElButton, {
										type: 'primary',
										size: 'small',
										onClick: async () => {
											if (form.id) {
												try {
													const res = await api.GenerateQrcode(form.id);
													if (res.code === 2000) {
														ElMessage.success('二维码生成成功');
														// 更新表单数据，触发重新渲染
														if (res.data && res.data.merchant_code) {
															form.merchant_code = res.data.merchant_code;
														}
														// 刷新列表数据
														await crudExpose.doRefresh();
														// 重新获取表单数据以确保二维码显示
														const formData = await api.GetObj(form.id);
														if (formData.data) {
															Object.assign(form, formData.data);
														}
													} else {
														ElMessage.error(res.msg || '二维码生成失败');
													}
												} catch (error) {
													ElMessage.error('二维码生成失败');
												}
											} else {
												ElMessage.warning('请先保存商户信息后再生成二维码');
											}
										},
									}, () => '生成二维码'),
									// 二维码预览区域
									form.merchant_code && qrCodeUrl ? h('div', { style: 'margin-top: 16px;' }, [
										h('div', { style: 'margin-bottom: 8px; color: #606266; font-size: 14px;' }, '二维码预览：'),
										h('div', { style: 'margin-bottom: 8px; color: #67C23A; font-size: 13px; font-weight: 500;' }, '✓ 生成成功'),
										h('div', { style: 'display: flex; align-items: center; gap: 12px;' }, [
											h('img', {
												src: qrCodeUrl,
												style: 'width: 120px; height: 120px; border: 1px solid #dcdfe6; border-radius: 4px; padding: 8px; background: #fff; cursor: pointer;',
												onClick: () => window.open(qrCodeUrl, '_blank'),
												onError: (e: any) => {
													e.target.style.display = 'none';
												},
											}),
											h('div', { style: 'display: flex; flex-direction: column; gap: 8px;' }, [
												h(ElButton, {
													type: 'success',
													size: 'small',
													onClick: () => {
														const link = document.createElement('a');
														link.href = qrCodeUrl;
														link.download = `merchant_qrcode_${form.merchant_code}.png`;
														document.body.appendChild(link);
														link.click();
														document.body.removeChild(link);
													},
												}, () => '下载二维码'),
												h(ElButton, {
													type: 'info',
													size: 'small',
													onClick: () => window.open(qrCodeUrl, '_blank'),
												}, () => '查看大图'),
											]),
										]),
									]) : !form.id ? h('div', {
										style: 'margin-top: 8px; color: #909399; font-size: 12px;',
									}, '提示：请先保存商户信息，然后点击按钮生成二维码') : null,
								]);
							},
						},
					},
				},
			},
		},
	};
};

