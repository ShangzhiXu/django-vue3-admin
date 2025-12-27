import { request } from '/@/utils/service';
import { UserPageQuery } from '@fast-crud/fast-crud';

export const apiPrefix = '/api/workorder/';

// 获取已移交工单列表
export function GetTransferredWorkOrderList(query: UserPageQuery) {
	return request({
		url: apiPrefix + 'transferred-list/',
		method: 'get',
		params: query,
	});
}

