import { request } from '/@/utils/service';
import { UserPageQuery, AddReq, DelReq, EditReq, InfoReq } from '@fast-crud/fast-crud';

export const apiPrefix = '/api/workorder/';

export function GetList(query: UserPageQuery) {
	return request({
		url: apiPrefix,
		method: 'get',
		params: query,
	});
}

export function GetObj(id: InfoReq) {
	return request({
		url: apiPrefix + id + '/',
		method: 'get',
	});
}

export function AddObj(obj: AddReq) {
	return request({
		url: apiPrefix,
		method: 'post',
		data: obj,
	});
}

export function UpdateObj(obj: EditReq) {
	return request({
		url: apiPrefix + obj.id + '/',
		method: 'put',
		data: obj,
	});
}

export function DelObj(id: DelReq) {
	return request({
		url: apiPrefix + id + '/',
		method: 'delete',
		data: { id },
	});
}

export function exportData(params: any) {
	return request({
		url: apiPrefix + 'export_data/',
		method: 'get',
		params: params,
		responseType: 'blob',
	});
}

export function SuperviseObj(id: number) {
	return request({
		url: apiPrefix + id + '/supervise/',
		method: 'post',
	});
}

export function CompleteObj(id: number) {
	return request({
		url: apiPrefix + id + '/complete/',
		method: 'post',
	});
}

export function GetWorkOrderPhotos(workorderNo: string) {
	return request({
		url: `/api/mobile/workorders/${workorderNo}/photos/list`,
		method: 'get',
	});
}

export function GetWorkOrderRechecks(workorderNo: string) {
	return request({
		url: `/api/mobile/workorders/${workorderNo}/rechecks`,
		method: 'get',
	});
}

export function GetWorkOrderSubmissions(workorderNo: string) {
	return request({
		url: `/api/mobile/workorders/${workorderNo}/submissions`,
		method: 'get',
	});
}

export function DeleteWorkOrderSubmission(workorderNo: string, submissionId: number) {
	return request({
		url: `/api/mobile/workorders/${workorderNo}/submissions/${submissionId}`,
		method: 'delete',
	});
}

