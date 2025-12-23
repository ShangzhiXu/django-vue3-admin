import { request } from '/@/utils/service';

const apiPrefix = '/api/home/';

export function GetDashboardData() {
	return request({
		url: apiPrefix + 'dashboard/',
		method: 'get',
	});
}






