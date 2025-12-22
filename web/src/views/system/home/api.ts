import { request } from '/@/utils/service';

const apiPrefix = '/api/home/';

export function GetStatistics() {
	return request({
		url: apiPrefix + 'statistics/',
		method: 'get',
	});
}




