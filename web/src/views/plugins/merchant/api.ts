import { request } from '/@/utils/service';
import { UserPageQuery, AddReq, DelReq, EditReq, InfoReq } from '@fast-crud/fast-crud';

export const apiPrefix = '/api/merchant/';

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

export function GenerateQrcode(id: InfoReq) {
	return request({
		url: apiPrefix + id + '/generate_qrcode/',
		method: 'post',
	});
}

export function BatchGenerateQrcode(data?: { ids?: number[] }) {
	return request({
		url: apiPrefix + 'batch_generate_qrcode/',
		method: 'post',
		data: data || {},
	});
}

export function BatchExportQrcode(data: { ids: number[] }) {
	return request({
		url: apiPrefix + 'batch_export_qrcode/',
		method: 'post',
		data,
	});
}

