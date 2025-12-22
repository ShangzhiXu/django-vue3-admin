<template>
	<el-select
		popper-class="popperClass"
		class="tableSelector"
		:multiple="props.tableConfig.isMultiple"
		:collapseTags="props.tableConfig.collapseTags"
		v-model="data"
		placeholder="请选择"
		@visible-change="visibleChange"
	>
		<template #empty>
			<div class="option">
				<el-input style="margin-bottom: 10px" v-model="search" clearable placeholder="请输入关键词" @change="getDict" @clear="getDict">
					<template #append>
						<el-button type="primary" icon="Search" />
					</template>
				</el-input>
				<el-table
					ref="tableRef"
					:data="tableData"
					:size="props.tableConfig.size"
					border
					row-key="id"
					:lazy="props.tableConfig.lazy"
					:load="props.tableConfig.load"
					:tree-props="props.tableConfig.treeProps"
					style="width: 600px"
					max-height="200"
					height="200"
					:highlight-current-row="!props.tableConfig.isMultiple"
					@selection-change="handleSelectionChange"
					@select="handleSelect"
					@selectAll="handleSelectionChange"
					@current-change="handleCurrentChange"
				>
					<el-table-column fixed type="selection" reserve-selection width="55" :selectable="getSelectable" />
					<el-table-column fixed type="index" label="#" width="50" />
					<el-table-column
						:prop="item.prop"
						:label="item.label"
						:width="item.width"
						v-for="(item, index) in props.tableConfig.columns"
						:key="index"
					/>
				</el-table>
				<el-pagination
					style="margin-top: 10px"
					background
					v-model:current-page="pageConfig.page"
					v-model:page-size="pageConfig.limit"
					layout="prev, pager, next"
					:total="pageConfig.total"
					@current-change="handlePageChange"
				/>
			</div>
		</template>
	</el-select>
</template>

<script setup lang="ts">
import { computed, defineProps, onMounted, reactive, ref, watch } from 'vue';
import XEUtils from 'xe-utils';
import { request } from '/@/utils/service';

const props = defineProps({
	modelValue: {
		type: Array || String || Number,
		default: () => [],
	},
	tableConfig: {
		type: Object,
		default: {
			url: null,
			label: null, //显示值
			value: null, //数据值
			isTree: false,
			lazy: true,
			size: 'default',
			load: () => {},
			data: [], //默认数据
			isMultiple: false, //是否多选
			collapseTags: false,
			treeProps: { children: 'children', hasChildren: 'hasChildren' },
			columns: [], //每一项对应的列表项
			extraParams: {}, //额外的动态参数
		},
	},
	displayLabel: {},
} as any);
console.log(props.tableConfig);

const emit = defineEmits(['update:modelValue']);
// tableRef
const tableRef = ref();
// template上使用data
const data = ref();
// 多选值
const multipleSelection = ref();
// 搜索值
const search = ref(undefined);
//表格数据
const tableData = ref([]);
// 分页的配置
const pageConfig = reactive({
	page: 1,
	limit: 10,
	total: 0,
});
// 防止循环更新的标志
const isUpdating = ref(false);

/**
 * 判断行是否可选（用于单选模式限制只能选一个）
 */
const getSelectable = (row: any, index: number) => {
	return true;
};

/**
 * 表格选择事件（单选模式下的处理）
 */
const handleSelect = (selection: any, row: any) => {
	const { tableConfig } = props;
	if (!tableConfig.isMultiple) {
		// 单选模式：如果选择了多个，清除其他选择，只保留当前点击的行
		if (selection.length > 1) {
			// 使用 nextTick 确保在 DOM 更新后执行
			setTimeout(() => {
				tableRef.value!.clearSelection();
				tableRef.value!.toggleRowSelection(row, true);
			}, 0);
		}
	}
};

/**
 * 表格多选
 * @param val:Array
 */
const handleSelectionChange = (val: any) => {
	// 如果正在更新中，跳过处理，避免循环
	if (isUpdating.value) {
		return;
	}
	
	const { tableConfig } = props;
	if (tableConfig.isMultiple) {
		// 多选模式
		const result = val.map((item: any) => {
			return item[tableConfig.value];
		});
		data.value = val.map((item: any) => {
			return item[tableConfig.label];
		});
		// 设置更新标志，防止触发 watch
		isUpdating.value = true;
		emit('update:modelValue', result);
		// 延迟重置标志，确保 watch 不会触发
		setTimeout(() => {
			isUpdating.value = false;
		}, 100);
	} else {
		// 单选模式：只取最后一个选择
		if (val && val.length > 0) {
			const selectedRow = val[val.length - 1]; // 取最后一个
			// 如果选择了多个，清除其他选择
			if (val.length > 1) {
				setTimeout(() => {
					tableRef.value!.clearSelection();
					tableRef.value!.toggleRowSelection(selectedRow, true);
				}, 0);
			}
			data.value = selectedRow[tableConfig.label];
			emit('update:modelValue', selectedRow[tableConfig.value]);
		} else {
			emit('update:modelValue', null);
		}
	}
};
/**
 * 表格单选（点击行时触发，保留作为备用）
 * @param val:Object
 */
const handleCurrentChange = (val: any) => {
	const { tableConfig } = props;
	if (!tableConfig.isMultiple && val) {
		// 如果通过点击行选择，也触发选择
		tableRef.value!.clearSelection();
		tableRef.value!.toggleRowSelection(val, true);
		handleSelectionChange([val]);
	}
};

/**
 * 获取字典值
 */
const getDict = async () => {
	const url = props.tableConfig.url;
	console.log(url);

	const params = {
		page: pageConfig.page,
		limit: pageConfig.limit,
		search: search.value,
		...(props.tableConfig.extraParams || {}), // 合并额外的动态参数
	};
	const { data, page, limit, total } = await request({
		url: url,
		params: params,
	});
	pageConfig.page = page;
	pageConfig.limit = limit;
	pageConfig.total = total;
	if (props.tableConfig.data === undefined || props.tableConfig.data.length === 0) {
		if (props.tableConfig.isTree) {
			tableData.value = XEUtils.toArrayTree(data, { parentKey: 'parent', key: 'id', children: 'children' });
		} else {
			tableData.value = data;
		}
	} else {
		tableData.value = props.tableConfig.data;
	}
};

// 获取节点值（用于回显已选择的值）
const getNodeValues = async () => {
	// 如果正在更新中，跳过处理，避免循环
	if (isUpdating.value) {
		return;
	}
	
	if (!props.modelValue) {
		return;
	}
	
	const ids = Array.isArray(props.modelValue) ? props.modelValue : [props.modelValue];
	if (ids.length === 0 || ids.every(id => id === null || id === undefined)) {
		return;
	}
	
	// 设置更新标志
	isUpdating.value = true;
	
	try {
		// 先通过 get_by_ids 接口获取已选择的数据
		const res = await request({
			url: props.tableConfig.url + 'get_by_ids/',
			method: 'post',
			data: { ids: ids },
		});
		
		if (res.data && res.data.length > 0) {
			// 设置显示值
			if (props.tableConfig.isMultiple) {
				data.value = res.data.map((item: any) => {
					return item[props.tableConfig.label];
				});
			} else {
				data.value = res.data[0][props.tableConfig.label];
			}
			
			// 等待表格数据加载完成后再选中
			await getDict();
			
					// 选中对应的行
					setTimeout(() => {
						if (tableRef.value && tableData.value.length > 0) {
							tableRef.value.clearSelection();
							res.data.forEach((row: any) => {
								// 在表格数据中查找对应的行
								const tableRow = tableData.value.find((item: any) => item.id === row.id);
								if (tableRow) {
									tableRef.value!.toggleRowSelection(tableRow, true, false);
								}
							});
						}
						// 重置更新标志
						isUpdating.value = false;
					}, 200);
				} else {
					isUpdating.value = false;
				}
			} catch (error) {
		// 如果 get_by_ids 接口不存在，尝试从当前表格数据中查找
		console.warn('获取节点值失败，尝试从当前数据中查找:', error);
		// 等待表格数据加载
		await getDict();
		// 从当前表格数据中查找并选中
		setTimeout(() => {
			if (tableRef.value && tableData.value.length > 0) {
				tableRef.value.clearSelection();
				const idsToFind = Array.isArray(props.modelValue) ? props.modelValue : [props.modelValue];
				idsToFind.forEach((id: any) => {
					const tableRow = tableData.value.find((item: any) => item.id === id);
					if (tableRow) {
						tableRef.value!.toggleRowSelection(tableRow, true, false);
						// 设置显示值
						if (props.tableConfig.isMultiple) {
							if (!Array.isArray(data.value)) {
								data.value = [];
							}
							if (!data.value.includes(tableRow[props.tableConfig.label])) {
								data.value.push(tableRow[props.tableConfig.label]);
							}
						} else {
							data.value = tableRow[props.tableConfig.label];
						}
					}
				});
			}
			// 重置更新标志
			isUpdating.value = false;
		}, 200);
	}
};

/**
 * 下拉框展开/关闭
 * @param bool
 */
const visibleChange = async (bool: any) => {
	if (bool) {
		// 先加载数据
		await getDict();
		// 如果有已选择的值，回显选中状态
		if (props.modelValue) {
			await getNodeValues();
		}
	}
};

/**
 * 分页
 * @param page
 */
const handlePageChange = (page: any) => {
	pageConfig.page = page;
	getDict();
};

// 监听 modelValue 变化，更新显示值
watch(
	() => props.modelValue,
	(newVal, oldVal) => {
		// 如果正在更新中，跳过处理，避免循环
		if (isUpdating.value) {
			return;
		}
		
		// 如果值没有变化，也跳过
		if (JSON.stringify(newVal) === JSON.stringify(oldVal)) {
			return;
		}
		
		if (newVal) {
			// 如果已经有值，需要获取对应的显示文本
			const ids = Array.isArray(newVal) ? newVal : [newVal];
			if (ids.length > 0 && !ids.every(id => id === null || id === undefined)) {
				// 延迟执行，确保组件已初始化
				setTimeout(() => {
					getNodeValues();
				}, 100);
			}
		} else {
			data.value = props.tableConfig.isMultiple ? [] : null;
		}
	},
	{ immediate: true }
);

// 监听 extraParams 变化，重新加载数据
watch(
	() => props.tableConfig.extraParams,
	(newParams, oldParams) => {
		// 如果参数发生变化，重新加载数据
		if (JSON.stringify(newParams) !== JSON.stringify(oldParams)) {
			pageConfig.page = 1; // 重置到第一页
			getDict();
		}
	},
	{ deep: true }
);

onMounted(() => {
	// 组件挂载后，如果有初始值，加载并回显
	if (props.modelValue) {
		setTimeout(() => {
			getNodeValues();
		}, 200);
	}
});
</script>

<style scoped>
.option {
	height: auto;
	line-height: 1;
	padding: 5px;
	background-color: #fff;
}
</style>
<style lang="scss">
.popperClass {
	height: 320px;
}

.el-select-dropdown__wrap {
	max-height: 310px !important;
}

.tableSelector {
	.el-icon,
	.el-tag__close {
		display: none;
	}
}
</style>
