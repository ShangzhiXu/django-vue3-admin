import * as api from './api';
import { UserPageQuery, AddReq, DelReq, EditReq, CreateCrudOptionsProps, CreateCrudOptionsRet, dict } from '@fast-crud/fast-crud';
import { shallowRef, h, ref } from 'vue';
import tableSelector from '/@/components/tableSelector/index.vue';
import { ElMessage, ElMessageBox, ElSelect, ElOption } from 'element-plus';
import { request } from '/@/utils/service';

// 检查类别对应的问题配置
const CHECK_ITEMS_MAP: Record<string, string[]> = {
	safety_manage: ['安全生产制度', '应急预案', '应急演练', '培训记录', '责任卡张贴'],
	gas: [
		'燃气报警器、燃气自动切断装置',
		'厨房是否多种燃料',
		'是否使用调压阀',
		'软管品质、长度、接头',
		'管是否穿墙、门窗、棚顶、地面',
		'是否使用三通',
		'气罐是否倒置、加热',
		'熄火保护装置',
		'气罐距火源距离（大于0.5米）',
		'同一空间气罐个数',
		'是否有桌下罐',
	],
	fire: [
		'门窗防护网等',
		'装潢是否易燃物',
		'安全出口标识、应急灯',
		'灭火器情况',
		'空开情况',
		'烟罩烟道情况、是否有清洗记录',
		'电箱盖情况、电线是否需穿管',
		'插座、电线是否烧焦',
		'是否使用电热毯',
		'疏散通道、楼梯上杂物',
		'二楼情况（安全指示牌）',
		'楼梯间情况（垃圾、隐藏气罐等）',
	],
	liquid_fuel: [
		'灭火器在储油间门外或室外储罐周边3m范围内',
		'液体燃料供货商是否与饭店签订供应合同',
		'液体燃料使用安全操作规程，安全操作规程张贴于使用场所',
		'燃料储存间和使用场所应具备良好的通风条件、不应设置员工宿舍',
		'室内储罐、灶具周围1m处不应堆放可燃物',
		'不应对盛装或盛装过可燃液体且未采取安全置换措施的储存容器进行电焊等明火作业',
		'室外的金属储罐，应按规定做防雷接地',
		'灶台应配置2块灭火毯设有明显、统一的标识',
		'储罐和油泵出口设有紧急切断阀',
		'储罐在室内一、二级耐火等级的单独房间内，门采用甲级防火门',
	],
};

export const createCrudOptions = function ({ crudExpose, context }: CreateCrudOptionsProps): CreateCrudOptionsRet {
	// 检查人选择的 tableConfig，动态更新 extraParams
	const inspectorTableConfig = ref({
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
	});
	
	// 包保责任人选择的 tableConfig，动态更新 extraParams
	const responsiblePersonTableConfig = ref({
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
	});
	
	// 移交负责人选择的 tableConfig
	const transferPersonTableConfig = ref({
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
	});
	
	const pageRequest = async (query: UserPageQuery) => {
		// 根据状态标签筛选
		const currentTab = context?.statusTab?.value || context?.statusTab;
		if (currentTab) {
			const statusMap: any = {
				all: undefined, // 全部，不筛选（不传status参数）
				pending: 0, // 待整改
				review: 1, // 待复查
				overdue: 3, // 已逾期
				completed: 2, // 已完成
			};
			const statusValue = statusMap[currentTab];
			// 只有当不是"全部"时才设置status筛选
			if (statusValue !== undefined) {
				query.status = statusValue;
			} else {
				// 全部时，确保不传status参数
				delete query.status;
			}
		}
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
						text: '新增工单',
					},
				},
			},
			search: {
				show: false, // 默认不展示搜索栏
			},
			table: {
				selection: {
					enabled: false,
				},
			},
			rowHandle: {
				fixed: 'right',
				width: 350,
				buttons: {
					view: {
						show: true,
						type: 'text',
						click: (clickContext: any) => {
							// 打开右侧抽屉显示工单详情
							if (context && context.openDetailDrawer) {
								context.openDetailDrawer(clickContext.row.id);
							}
						},
					},
					edit: {
						show: true,
						type: 'text',
					},
					remove: {
						show: true,
						type: 'text',
					},
					supervise: {
						text: '督办',
						type: 'warning',
						show: (context: any) => {
							// 待整改或已逾期状态可以督办
							return context.row.status === 0 || context.row.status === 3;
						},
						click: async (context: any) => {
							try {
								await ElMessageBox.confirm(
									`确定要对工单 ${context.row.workorder_no} 执行督办吗？`,
									'提示',
									{
										confirmButtonText: '确定',
										cancelButtonText: '取消',
										type: 'warning',
									}
								);
								await api.SuperviseObj(context.row.id);
								ElMessage.success('督办成功');
								crudExpose.doRefresh();
							} catch (error: any) {
								if (error !== 'cancel') {
									ElMessage.error(error?.message || '督办失败');
								}
							}
						},
					},
					complete: {
						text: '完成',
						type: 'success',
						show: (context: any) => {
							// 已完成状态不显示完成按钮
							return context.row.status !== 2;
						},
						click: async (context: any) => {
							try {
								await ElMessageBox.confirm(
									`确定要完成工单 ${context.row.workorder_no} 吗？`,
									'提示',
									{
										confirmButtonText: '确定',
										cancelButtonText: '取消',
										type: 'success',
									}
								);
								await api.CompleteObj(context.row.id);
								ElMessage.success('工单已完成');
								crudExpose.doRefresh();
							} catch (error: any) {
								if (error !== 'cancel') {
									ElMessage.error(error?.message || '完成操作失败');
								}
							}
						},
					},
				},
			},
			columns: {
				$checked: {
					title: '选择',
					form: { show: false },
					column: {
						show: false,
						type: 'selection',
					},
				},
				_index: {
					title: '序号',
					form: { show: false },
					column: {
						align: 'center',
						width: '70px',
						columnSetDisabled: true,
						formatter: (context: any) => {
							let index = context.index ?? 1;
							let pagination = crudExpose!.crudBinding.value.pagination;
							return ((pagination!.currentPage ?? 1) - 1) * pagination!.pageSize + index + 1;
						},
					},
				},
				search: {
					title: '工单号/商户名',
					column: {
						show: false,
					},
					search: {
						show: true,
						component: {
							props: {
								clearable: true,
							},
							placeholder: '请输入工单号或商户名称',
						},
					},
					form: {
						show: false,
					},
				},
				workorder_no: {
					title: '工单号',
					type: 'input',
					search: {
						show: false,
					},
					column: {
						minWidth: 180,
						align: 'center',
					},
					form: {
						show: false,
					},
				},
				merchant: {
					title: '商户',
					type: 'table-selector',
					search: {
						show: false,
					},
					column: {
						show: false,
					},
					form: {
						rules: [
							{ required: true, message: '请选择商户' },
						],
						component: {
							name: shallowRef(tableSelector),
							props: {
								tableConfig: {
									url: '/api/merchant/',
									label: 'name',
									value: 'id',
									columns: [
										{ prop: 'name', label: '商户名称', width: 150 },
										{ prop: 'manager', label: '负责人', width: 120 },
										{ prop: 'phone', label: '联系电话', width: 150 },
									],
									isMultiple: false,
									pagination: true,
									searchFields: [
										{
											prop: 'category',
											label: '场所类型',
											type: 'select',
											options: [
												{ label: '大型商超', value: 1 },
												{ label: '商业综合体', value: 2 },
												{ label: '大型餐饮饭店', value: 3 },
												{ label: '大型宾馆', value: 4 },
												{ label: '大型洗浴', value: 5 },
												{ label: '成品油市场', value: 6 },
												{ label: '再生资源回收利用', value: 7 },
												{ label: '新车，二手车销售', value: 8 },
												{ label: '洗车服务（不包括"汽车修理与维护"）', value: 9 },
												{ label: '托管班、"小饭桌"、自习室等校外托管服务场所（不包含课余辅导、教育培训）', value: 10 },
												{ label: '九小场所（小超市、小饭馆、小旅店、小美容洗浴）', value: 11 },
												{ label: '拍卖', value: 12 },
												{ label: '旧货流通', value: 13 },
												{ label: '报废机动车回收', value: 14 },
												{ label: '摄影服务（婚纱摄影）', value: 15 },
												{ label: '家用电器修理', value: 16 },
												{ label: '其他', value: 17 },
											]
										}
									]
								},
							},
						},
						valueChange: async (context: any) => {
							// 当商户改变时，从商户继承包保责任人
							const { form } = context;
							if (form.merchant) {
								try {
									// 获取商户详细信息
									const merchantRes = await request({
										url: `/api/merchant/${form.merchant}/`,
										method: 'get',
									});
									if (merchantRes && merchantRes.data && merchantRes.data.responsible_person) {
										// 如果商户有包保责任人，且工单未设置包保责任人，则自动填充
										if (!form.responsible_person) {
											form.responsible_person = merchantRes.data.responsible_person;
										}
									}
								} catch (error) {
									console.error('获取商户信息失败:', error);
								}
							}
						},
					},
				},
				deadline: {
					title: '整改时限',
					type: 'date',
					search: {
						show: true,
					},
					column: {
						minWidth: 120,
						align: 'center',
					},
					form: {
						component: {
							placeholder: '请选择整改时限',
							'value-format': 'YYYY-MM-DD',
						},
					},
				},
				check_category: {
					title: '检查类别',
					type: 'dict-select',
					dict: dict({
						data: [
							{ label: '安全管理类', value: 'safety_manage' },
							{ label: '燃气类', value: 'gas' },
							{ label: '消防类', value: 'fire' },
							{ label: '液体燃料类', value: 'liquid_fuel' },
						],
					}),
					search: {
						show: true,
					},
					column: {
						minWidth: 120,
						align: 'center',
					},
					form: {
						component: {
							placeholder: '请选择检查类别',
						},
						valueChange(context: any) {
							// 切换检查类别时，清空已选检查问题
							if (context && context.form) {
								context.form.check_item = undefined;
							}
						},
					},
				},
				check_item: {
					title: '检查问题',
					type: 'text',
					search: {
						show: true,
					},
					column: {
						minWidth: 260,
						showOverflowTooltip: true,
					},
					form: {
						component: {
							render({ form }: any) {
								const category = form.check_category as string | undefined;
								const options = category ? CHECK_ITEMS_MAP[category] || [] : [];
								const disabled = !category;
								return h(
									ElSelect,
									{
										modelValue: form.check_item || '',
										'onUpdate:modelValue': (val: string) => {
											form.check_item = val;
										},
										placeholder: category ? '请选择检查问题' : '请先选择检查类别',
										filterable: true,
										disabled,
										style: 'width: 100%;',
									},
									() =>
										options.map((item) =>
											h(ElOption, {
												label: item,
												value: item,
												key: item,
											})
										)
								);
							},
						},
					},
				},
				merchant_name: {
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
						show: false,
					},
				},
				problem_description: {
					title: '问题描述',
					type: 'textarea',
					column: {
						minWidth: 250,
						showOverflowTooltip: true,
					},
					form: {
						component: {
							placeholder: '请输入问题描述',
							props: {
								rows: 4,
							},
						},
					},
				},
				rectification_category: {
					title: '整改类别',
					type: 'dict-select',
					dict: dict({
						data: [
							{ label: '当场整改', value: 'immediate' },
							{ label: '限期整改', value: 'deadline' },
							{ label: '移交整改', value: 'transfer' },
						],
					}),
					search: {
						show: true,
					},
					column: {
						minWidth: 120,
						align: 'center',
						formatter: (context: any) => {
							// 优先使用后端返回的中文显示值
							if (context.row.rectification_category_display) {
								return context.row.rectification_category_display;
							}
							// 如果没有，则根据值映射
							const categoryMap: { [key: string]: string } = {
								'immediate': '当场整改',
								'deadline': '限期整改',
								'transfer': '移交整改',
							};
							return categoryMap[context.value] || context.value || '-';
						},
					},
					form: {
						component: {
							placeholder: '请选择整改类别',
						},
					},
				},
				is_transferred: {
					title: '是否已移交',
					type: 'dict-select',
					dict: dict({
						data: [
							{ label: '否', value: false },
							{ label: '是', value: true },
						],
					}),
					search: {
						show: true,
					},
					column: {
						minWidth: 120,
						align: 'center',
						formatter: (context: any) => (context.value ? '是' : '否'),
						component: {
							name: 'fs-dict-tag',
							props: {
								colors: {
									true: 'success',
									false: 'info',
								},
							},
						},
					},
					form: {
						value: false,
						component: {
							placeholder: '是否已移交',
						},
						valueChange({ form, value }: any) {
							if (!value) {
								form.transfer_person = null;
							}
						},
					},
				},
				inspector_dept: {
					title: '检查人部门',
					type: 'table-selector',
					search: {
						show: false,
					},
					column: {
						show: false,
					},
					form: {
						component: {
							name: shallowRef(tableSelector),
							props: {
								tableConfig: {
									url: '/api/system/dept/',
									label: 'name',
									value: 'id',
									columns: [
										{ prop: 'name', label: '部门名称', width: 200 },
									],
									isMultiple: false,
									pagination: true,
								},
							},
							span: 12,
							placeholder: '请先选择检查人部门',
						},
					},
					valueChange(context: any) {
						// 当部门改变时，清空检查人选择并更新过滤参数
						const { form } = context;
						if (form.inspector) {
							form.inspector = null;
						}
						// 更新检查人选择的过滤参数
						if (form.inspector_dept) {
							inspectorTableConfig.value.extraParams = { dept: form.inspector_dept, show_all: 1 };
						} else {
							inspectorTableConfig.value.extraParams = {};
						}
					},
				},
				inspector: {
					title: '检查人',
					type: 'table-selector',
					search: {
						show: false,
					},
					column: {
						minWidth: 120,
						align: 'center',
						formatter: (context: any) => {
							// 如果后端返回了检查人名称
							if (context.row.inspector_name) {
								return context.row.inspector_name;
							}
							// 如果后端返回了检查人对象
							if (context.row.inspector && typeof context.row.inspector === 'object') {
								return context.row.inspector.name || '-';
							}
							return context.value ? `用户ID: ${context.value}` : '-';
						},
					},
					form: {
						component: {
							name: shallowRef(tableSelector),
							props: {
								tableConfig: inspectorTableConfig,
							},
							span: 12,
							placeholder: '请先选择部门，再选择检查人（默认从任务继承）',
						},
					},
				},
				responsible_person_dept: {
					title: '包保责任人部门',
					type: 'table-selector',
					search: {
						show: false,
					},
					column: {
						show: false,
					},
					form: {
						component: {
							name: shallowRef(tableSelector),
							props: {
								tableConfig: {
									url: '/api/system/dept/',
									label: 'name',
									value: 'id',
									columns: [
										{ prop: 'name', label: '部门名称', width: 200 },
									],
									isMultiple: false,
									pagination: true,
								},
							},
							span: 12,
							placeholder: '请先选择包保责任人部门',
						},
					},
					valueChange(context: any) {
						// 当部门改变时，清空包保责任人选择并更新过滤参数
						const { form } = context;
						if (form.responsible_person) {
							form.responsible_person = null;
						}
						// 更新包保责任人选择的过滤参数
						if (form.responsible_person_dept) {
							responsiblePersonTableConfig.value.extraParams = { dept: form.responsible_person_dept, show_all: 1 };
						} else {
							responsiblePersonTableConfig.value.extraParams = {};
						}
					},
				},
				responsible_person: {
					title: '包保责任人',
					type: 'table-selector',
					search: {
						show: false,
					},
					column: {
						minWidth: 120,
						align: 'center',
						formatter: (context: any) => {
							// 如果后端返回了包保责任人名称
							if (context.row.responsible_person_name) {
								return context.row.responsible_person_name;
							}
							// 如果后端返回了包保责任人对象
							if (context.row.responsible_person && typeof context.row.responsible_person === 'object') {
								return context.row.responsible_person.name || '-';
							}
							return context.value ? `用户ID: ${context.value}` : '-';
						},
					},
					form: {
						component: {
							name: shallowRef(tableSelector),
							props: {
								tableConfig: responsiblePersonTableConfig,
							},
							span: 12,
							placeholder: '请先选择部门，再选择包保责任人',
						},
					},
				},
				transfer_person: {
					title: '移交负责人',
					type: 'table-selector',
					search: {
						show: false,
					},
					column: {
						minWidth: 120,
						align: 'center',
						formatter: (context: any) => {
							if (context.row.transfer_person_name) {
								return context.row.transfer_person_name;
							}
							if (context.row.transfer_person && typeof context.row.transfer_person === 'object') {
								return context.row.transfer_person.name || '-';
							}
							return context.value ? `用户ID: ${context.value}` : '-';
						},
					},
					form: {
						component: {
							name: shallowRef(tableSelector),
							props: {
								tableConfig: transferPersonTableConfig,
							},
							span: 12,
							placeholder: '请选择移交负责人（可选）',
						},
					},
				},
				remark: {
					title: '备注',
					type: 'textarea',
					column: {
						show: false,
					},
					form: {
						component: {
							placeholder: '请输入备注',
							props: {
								rows: 3,
							},
						},
					},
				},
				report_time: {
					title: '上报时间',
					type: 'datetime',
					search: {
						show: true,
						col: { span: 8 },
						component: {
							type: 'datetimerange',
							props: {
								'start-placeholder': '开始时间',
								'end-placeholder': '结束时间',
								'value-format': 'YYYY-MM-DD HH:mm:ss',
							},
						},
						valueResolve(context: any) {
							const { value } = context;
							if (value) {
								context.form.report_time_after = value[0];
								context.form.report_time_before = value[1];
								delete context.form.report_time;
							}
						},
					},
					column: {
						minWidth: 160,
						align: 'center',
					},
					form: {
						show: false,
					},
				},
				status: {
					title: '状态',
					type: 'dict-select',
					dict: dict({
						data: [
							{ label: '待整改', value: 0 },
							{ label: '待复查', value: 1 },
							{ label: '已完成', value: 2 },
							{ label: '已逾期', value: 3 },
						],
					}),
					search: {
						show: false, // 使用标签筛选，不在搜索栏显示
					},
					column: {
						minWidth: 120,
						align: 'center',
						formatter: (context: any) => {
							// 优先使用后端返回的中文显示值
							if (context.row.status_display) {
								return context.row.status_display;
							}
							// 如果没有，则根据值映射
							const statusMap: { [key: number]: string } = {
								0: '待整改',
								1: '待复查',
								2: '已完成',
								3: '已逾期',
							};
							return statusMap[context.value] || context.value || '-';
						},
						component: {
							name: 'fs-dict-tag',
							props: {
								colors: {
									0: 'warning',
									1: 'primary',
									2: 'success',
									3: 'danger',
								},
							},
						},
					},
					form: {
						value: 0, // 默认值为待整改
						component: {
							placeholder: '请选择状态',
						},
					},
				},
				task: {
					title: '关联任务',
					type: 'table-selector',
					search: {
						show: false,
					},
					column: {
						minWidth: 150,
						align: 'center',
						formatter: (context: any) => {
							// 如果后端返回了任务对象，显示任务名称
							if (context.row.task && typeof context.row.task === 'object') {
								return context.row.task.name || '-';
							}
							// 如果后端返回了任务名称字段
							if (context.row.task_name) {
								return context.row.task_name;
							}
							// 如果只是ID，显示ID或"-"
							return context.value ? `任务ID: ${context.value}` : '-';
						},
					},
					form: {
						component: {
							name: shallowRef(tableSelector),
							props: {
								tableConfig: {
									url: '/api/task/',
									label: 'name',
									value: 'id',
									columns: [
										{ prop: 'name', label: '任务名称', width: 200 },
										{ prop: 'cycle', label: '周期', width: 100 },
									],
									isMultiple: false,
									pagination: true,
								},
							},
						},
						valueChange(context: any) {
							// 当选择任务时，自动从任务继承检查人
							const { form, value } = context;
							if (value) {
								// 获取任务详情，提取负责人
								request({
									url: `/api/task/${value}/`,
									method: 'get',
								}).then((res: any) => {
									if (res.data && res.data.manager) {
										// 如果检查人为空，则自动填充
										if (!form.inspector) {
											form.inspector = res.data.manager;
										}
									}
								}).catch(() => {
									// 忽略错误
								});
							}
						},
					},
				},
				hazard_level: {
					title: '隐患等级',
					type: 'dict-select',
					dict: dict({
						data: [
							{ label: '高', value: 'high' },
							{ label: '中', value: 'medium' },
							{ label: '低', value: 'low' },
						],
					}),
					search: {
						show: true,
					},
					column: {
						minWidth: 100,
						align: 'center',
						formatter: (context: any) => {
							// 优先使用后端返回的中文显示值
							if (context.row.hazard_level_display) {
								return context.row.hazard_level_display;
							}
							// 如果没有，则根据值映射
							const levelMap: { [key: string]: string } = {
								'high': '高',
								'medium': '中',
								'low': '低',
							};
							return levelMap[context.value] || context.value || '-';
						},
						component: {
							name: 'fs-dict-tag',
							props: {
								colors: {
									high: 'danger',
									medium: 'warning',
									low: 'success',
								},
							},
						},
					},
					form: {
						component: {
							placeholder: '请选择隐患等级',
						},
					},
				},
			},
		},
	};
};

