import * as api from './api';
import { UserPageQuery, AddReq, DelReq, EditReq, CreateCrudOptionsProps, CreateCrudOptionsRet, dict } from '@fast-crud/fast-crud';
import { shallowRef, ref, h } from 'vue';
import tableSelector from '/@/components/tableSelector/index.vue';
import { ElDialog, ElTable, ElTableColumn, ElPagination, ElCheckboxGroup, ElCheckbox, ElDivider } from 'element-plus';

export const createCrudOptions = function ({ crudExpose, context }: CreateCrudOptionsProps): CreateCrudOptionsRet {
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
						text: '新增任务',
					},
				},
			},
			search: {
				show: false, // 默认不展示搜索栏
			},
			rowHandle: {
				fixed: 'right',
				width: 280,
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
					workorders: {
						text: '对应工单',
						type: 'primary',
						show: true,
						click: (clickContext: any) => {
							// 打开工单列表对话框
							if (context && context.openWorkorderDialog) {
								context.openWorkorderDialog(clickContext.row);
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
							let index = context.index ?? 1;
							let pagination = crudExpose!.crudBinding.value.pagination;
							return ((pagination!.currentPage ?? 1) - 1) * pagination!.pageSize + index + 1;
						},
					},
				},
				id: {
					title: 'ID',
					type: 'number',
					search: {
						show: true,
					},
					column: {
						align: 'center',
						width: '80px',
					},
					form: {
						show: false,
					},
				},
				name: {
					title: '任务名称',
					type: 'input',
					search: {
						show: true,
						component: {
							props: {
								clearable: true,
							},
							placeholder: '请输入任务名称',
						},
					},
					column: {
						minWidth: 150,
					},
					form: {
						rules: [
							{ required: true, message: '请输入任务名称' },
						],
						component: {
							placeholder: '请输入任务名称',
						},
					},
				},
				manager: {
					title: '负责人',
					type: 'table-selector',
					search: {
						show: false,
					},
					column: {
						minWidth: 120,
						formatter: (context: any) => {
							// 显示负责人名称
							return context.row.manager_name || '-';
						},
					},
					form: {
						component: {
							name: shallowRef(tableSelector),
							props: {
								tableConfig: {
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
								},
							},
						},
					},
				},
				manager_name: {
					title: '负责人名称',
					type: 'text',
					column: {
						show: false,
					},
					form: {
						show: false,
					},
				},
				cycle: {
					title: '周期',
					type: 'dict-select',
					dict: dict({
						data: [
							{ label: '不重复', value: 'once' },
							{ label: '每日', value: 'daily' },
							{ label: '每周', value: 'weekly' },
							{ label: '每月', value: 'monthly' },
							{ label: '每年', value: 'yearly' },
							{ label: '自定义', value: 'custom' },
						],
					}),
					search: {
						show: true,
					},
					column: {
						minWidth: 100,
						align: 'center',
						// 直接显示中文值
						formatter: (context: any) => {
							// 后端返回的是中文值，直接显示
							return context.value || '-';
						},
					},
					form: {
						rules: [
							{ required: true, message: '请选择周期' },
						],
						component: {
							placeholder: '请选择周期',
						},
						// 接收数据时：将中文值转换为英文值用于表单编辑
						valueBuilder: (row: any, col: any) => {
							// 如果后端返回了 cycle_value（英文值），使用它
							// 否则根据中文值查找对应的英文值
							if (row.cycle_value) {
								row.cycle = row.cycle_value;
							} else if (row.cycle) {
								// 中文值到英文值的映射
								const cycleMap: { [key: string]: string } = {
									'不重复': 'once',
									'每日': 'daily',
									'每周': 'weekly',
									'每月': 'monthly',
									'每年': 'yearly',
									'自定义': 'custom',
								};
								row.cycle = cycleMap[row.cycle] || row.cycle;
							}
						},
						// 提交数据时：确保提交的是英文值
						valueResolve: (context: any) => {
							// 中文值到英文值的映射
							const cycleMap: { [key: string]: string } = {
								'不重复': 'once',
								'每日': 'daily',
								'每周': 'weekly',
								'每月': 'monthly',
								'每年': 'yearly',
								'自定义': 'custom',
							};
							
							// 获取当前值（可能是从 context.value 或 context.form.cycle）
							let value = context.value || context.form?.cycle;
							
							// 如果值是中文，转换为英文
							if (value && cycleMap[value]) {
								if (context.form) {
									context.form.cycle = cycleMap[value];
								}
								return cycleMap[value];
							}
							
							// 如果已经是英文值，直接返回
							const validValues = ['once', 'daily', 'weekly', 'monthly', 'yearly', 'custom'];
							if (value && validValues.includes(value)) {
								if (context.form) {
									context.form.cycle = value;
								}
								return value;
							}
							
							// 如果值无效，返回原值（让后端验证）
							return value;
						},
					},
				},
				cycle_value: {
					title: '周期值',
					type: 'text',
					column: {
						show: false, // 隐藏此列
					},
					form: {
						show: false, // 表单中也不显示
					},
				},
				time_range: {
					title: '时间范围',
					type: 'daterange',
					search: {
						show: true,
						component: {
							props: {
								'start-placeholder': '开始日期',
								'end-placeholder': '结束日期',
								'value-format': 'YYYY-MM-DD',
							},
						},
					},
					column: {
						minWidth: 280,
						align: 'center',
					},
					form: {
						rules: [
							{ required: true, message: '请选择时间范围' },
						],
						component: {
							props: {
								'start-placeholder': '开始日期',
								'end-placeholder': '结束日期',
								'value-format': 'YYYY-MM-DD',
							},
						},
					},
				},
				merchants: {
					title: '覆盖商户',
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
									url: '/api/merchant/',
									label: 'name',
									value: 'id',
									columns: [
										{ prop: 'name', label: '商户名称', width: 150 },
										{ prop: 'manager', label: '负责人', width: 120 },
										{ prop: 'phone', label: '联系电话', width: 150 },
									],
									isMultiple: true,
									pagination: true,
								},
							},
						},
					},
				},
				merchant_count: {
					title: '覆盖商户数',
					type: 'number',
					search: {
						show: true,
					},
					column: {
						minWidth: 120,
						align: 'center',
					},
					form: {
						show: false,
					},
				},
				check_items: {
					title: '检查项',
					type: 'text',
					column: {
						minWidth: 200,
						showOverflowTooltip: true,
					},
					form: {
						component: {
							// 自定义渲染：左侧类别，右侧具体检查项（分组多选）
							render({ form }: any) {
								// 统一的检查项配置
								const categories = [
									{
										key: 'safety_manage',
										label: '安全管理类',
										items: ['安全生产制度', '应急预案', '应急演练', '培训记录', '责任卡张贴'],
									},
									{
										key: 'gas',
										label: '燃气类',
										items: [
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
									},
									{
										key: 'fire',
										label: '消防类',
										items: [
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
									},
									{
										key: 'liquid_fuel',
										label: '液体燃料类',
										items: [
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
									},
								];

								// 内部使用的选中值数组，来源于 check_items（逗号分隔）
								if (!Array.isArray((form as any).check_items_list)) {
									const raw = form.check_items || '';
									(form as any).check_items_list = raw
										.split(',')
										.map((s: string) => s.trim())
										.filter((s: string) => s);
								}

								const selected = (form as any).check_items_list as string[];

								// 渲染左侧类别 + 右侧对应多选项
								return h('div', { style: 'display: flex; gap: 16px;' }, [
									// 左侧类别列表（仅展示，点击辅助定位）
									h(
										'div',
										{
											style:
												'width: 160px; border-right: 1px solid #ebeef5; padding-right: 8px;',
										},
										categories.map((cat) =>
											h(
												'div',
												{
													style:
														'padding: 6px 4px; cursor: pointer; font-weight: 500; color: #409EFF;',
												},
												cat.label
											)
										)
									),
									// 右侧各类别下的具体检查项多选
									h(
										'div',
										{ style: 'flex: 1; padding-left: 8px; max-height: 320px; overflow: auto;' },
										categories.map((cat, index) =>
											h('div', { style: 'margin-bottom: 12px;' }, [
												h(
													'div',
													{
														style:
															'margin-bottom: 4px; font-weight: 500; color: #303133;',
													},
													cat.label
												),
												h(
													ElCheckboxGroup,
													{
														modelValue: selected,
														'onUpdate:modelValue': (val: string[]) => {
															(form as any).check_items_list = val;
															form.check_items = val.join(',');
														},
													},
													() =>
														cat.items.map((item) =>
															h(
																ElCheckbox,
																{
																	label: item,
																	style:
																		'display: block; margin: 2px 0;',
																},
																() => item
															)
														)
												),
												index < categories.length - 1
													? h(ElDivider, {
															style: 'margin: 8px 0;',
													  })
													: null,
											])
										)
									),
								]);
							},
						},
						valueBuilder(form: any) {
							// 打开表单时，将后端的逗号分隔字符串转成数组
							const raw = form.check_items || '';
							form.check_items_list = raw
								.split(',')
								.map((s: string) => s.trim())
								.filter((s: string) => s);
						},
						valueResolve(context: any) {
							// 提交表单时，将数组再转回逗号分隔字符串
							const list = context.form.check_items_list || [];
							context.form.check_items = Array.isArray(list)
								? list.join(',')
								: context.form.check_items || '';
						},
					},
				},
				status: {
					title: '状态',
					type: 'dict-select',
					dict: dict({
						data: [
							{ label: '待执行', value: 0 },
							{ label: '执行中', value: 1 },
							{ label: '已完成', value: 2 },
							{ label: '已暂停', value: 3 },
							{ label: '已取消', value: 4 },
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
							placeholder: '请选择状态',
						},
					},
				},
			},
		},
	};
};

