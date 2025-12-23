import { request } from '/@/utils/service';
import { UserPageQuery } from '@fast-crud/fast-crud';

export const apiPrefix = '/api/supervision/';

// 获取待督办工单列表
export function GetWorkOrderList(query: UserPageQuery) {
	return request({
		url: apiPrefix + 'workorder-list/',
		method: 'get',
		params: query,
	});
}

// 工单移交
export function TransferWorkorder(id: number, data: { transfer_person: number; transfer_remark?: string }) {
	return request({
		url: `/api/workorder/${id}/transfer/`,
		method: 'post',
		data,
	});
}

// 批量推送督办通知
export function BatchPush(data: { workorder_ids: number[]; regulatory_unit?: string; push_method?: string }) {
	return request({
		url: apiPrefix + 'batch-push/',
		method: 'post',
		data: data,
	});
}

// 获取推送历史列表
export function GetPushHistory(query: UserPageQuery) {
	return request({
		url: apiPrefix + 'history/',
		method: 'get',
		params: query,
	});
}






