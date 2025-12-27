import { RouteRecordRaw } from 'vue-router';
import { storeToRefs } from 'pinia';
import pinia from '/@/stores/index';
import { useUserInfo } from '/@/stores/userInfo';
import { useRequestOldRoutes } from '/@/stores/requestOldRoutes';
import { Session } from '/@/utils/storage';
import { NextLoading } from '/@/utils/loading';
import { dynamicRoutes, notFoundAndNoPower } from '/@/router/route';
import { formatTwoStageRoutes, formatFlatteningRoutes, router } from '/@/router/index';
import { useRoutesList } from '/@/stores/routesList';
import { useTagsViewRoutes } from '/@/stores/tagsViewRoutes';
import { useMenuApi } from '/@/api/menu/index';
import { handleMenu } from '../utils/menu';
import { BtnPermissionStore } from '/@/plugin/permission/store.permission';
import {SystemConfigStore} from "/@/stores/systemConfig";
import {useDeptInfoStore} from "/@/stores/modules/dept";
import {DictionaryStore} from "/@/stores/dictionary";
import {useFrontendMenuStore} from "/@/stores/frontendMenu";
import {toRaw} from "vue";
const menuApi = useMenuApi();

const layouModules: any = import.meta.glob('../layout/routerView/*.{vue,tsx}');
const viewsModules: any = import.meta.glob('../views/**/*.{vue,tsx}');
const greatDream: any = import.meta.glob('@great-dream/**/*.{vue,tsx}');

/**
 * 获取目录下的 .vue、.tsx 全部文件
 * @method import.meta.glob
 * @link 参考：https://cn.vitejs.dev/guide/features.html#json
 */
const dynamicViewsModules: Record<string, Function> = Object.assign({}, { ...layouModules }, { ...viewsModules }, { ...greatDream });

/**
 * 后端控制路由：初始化方法，防止刷新时路由丢失
 * @method NextLoading 界面 loading 动画开始执行
 * @method useUserInfo().setUserInfos() 触发初始化用户信息 pinia
 * @method useRequestOldRoutes().setRequestOldRoutes() 存储接口原始路由（未处理component），根据需求选择使用
 * @method setAddRoute 添加动态路由
 * @method setFilterMenuAndCacheTagsViewRoutes 设置路由到 vuex routesList 中（已处理成多级嵌套路由）及缓存多级嵌套数组处理后的一维数组
 */
export async function initBackEndControlRoutes() {
	// 界面 loading 动画开始执行
	if (window.nextLoading === undefined) NextLoading.start();
	// 无 token 停止执行下一步
	if (!Session.get('token')) return false;
	// 触发初始化用户信息 pinia
	// https://gitee.com/lyt-top/vue-next-admin/issues/I5F1HP
	await useUserInfo().getApiUserInfo();
	// 获取路由菜单数据
	const res = await getBackEndControlRoutes();
	console.log('[initBackEndControlRoutes] 获取到的菜单数据:', res.data);
	// 无登录权限时，添加判断
	// https://gitee.com/lyt-top/vue-next-admin/issues/I64HVO
	// if (res.data.length <= 0) return Promise.resolve(true);
	// 处理路由（component），替换 dynamicRoutes（/@/router/route）第一个顶级 children 的路由
	const {frameIn,frameOut} = handleMenu(res.data)
	console.log('[initBackEndControlRoutes] 处理后的路由:', frameIn);
	// 查找督办中心路由
	const supervisionRoute = frameIn.find((r: any) => r.path === '/supervision' || r.name === 'supervision');
	if (supervisionRoute) {
		console.log('[initBackEndControlRoutes] 找到督办中心路由:', supervisionRoute);
		console.log('[initBackEndControlRoutes] 督办中心组件路径:', supervisionRoute.component);
	}
	dynamicRoutes[0].children = await backEndComponent(frameIn);
	// 检查督办中心路由的组件是否已加载
	const supervisionAfterProcess = dynamicRoutes[0].children.find((r: any) => r.path === '/supervision');
	if (supervisionAfterProcess) {
		console.log('[initBackEndControlRoutes] 督办中心路由处理后的组件类型:', typeof supervisionAfterProcess.component);
		console.log('[initBackEndControlRoutes] 督办中心路由处理后的组件:', supervisionAfterProcess.component);
		console.log('[initBackEndControlRoutes] 督办中心路由完整信息:', {
			path: supervisionAfterProcess.path,
			name: supervisionAfterProcess.name,
			component: supervisionAfterProcess.component,
			meta: supervisionAfterProcess.meta
		});
	} else {
		console.error('[initBackEndControlRoutes] 未找到督办中心路由！所有路由:', dynamicRoutes[0].children.map((r: any) => ({ path: r.path, name: r.name })));
	}
	// 添加动态路由
	await setAddRoute();
	// 验证路由是否已添加
	const addedRoute = router.getRoutes().find(r => r.path === '/supervision');
	if (addedRoute) {
		console.log('[initBackEndControlRoutes] 督办中心路由已成功添加到路由器');
	} else {
		console.error('[initBackEndControlRoutes] 督办中心路由未成功添加到路由器！');
		console.log('[initBackEndControlRoutes] 所有已注册的路由:', router.getRoutes().map(r => ({ path: r.path, name: r.name })));
	}
	// 设置路由到 vuex routesList 中（已处理成多级嵌套路由）及缓存多级嵌套数组处理后的一维数组
	await setFilterMenuAndCacheTagsViewRoutes();
}

export async function setRouters(){
	const {frameInRoutes,frameOutRoutes} = await useFrontendMenuStore().getRouter()
	const frameInRouter = toRaw(frameInRoutes)
	const frameOutRouter = toRaw(frameOutRoutes)
	
	// 调试信息：检查督办中心路由
	const supervisionRoute = frameInRouter.find((r: any) => r.path === '/supervision' || r.name === 'supervision');
	if (supervisionRoute) {
		console.log('[setRouters] 找到督办中心路由:', supervisionRoute);
		console.log('[setRouters] 督办中心组件类型:', typeof supervisionRoute.component);
		console.log('[setRouters] 督办中心组件:', supervisionRoute.component);
	} else {
		console.warn('[setRouters] 未找到督办中心路由，所有路由:', frameInRouter.map((r: any) => ({ path: r.path, name: r.name, component: r.component })));
	}
	
	dynamicRoutes[0].children = frameInRouter
	dynamicRoutes.forEach((item:any)=>{
		router.addRoute(item)
	})
	frameOutRouter.forEach((item:any)=>{
		router.addRoute(item)
	})
	
	// 验证路由是否已添加
	const addedRoute = router.getRoutes().find(r => r.path === '/supervision');
	if (addedRoute) {
		console.log('[setRouters] 督办中心路由已成功添加到路由器:', addedRoute);
	} else {
		console.error('[setRouters] 督办中心路由未成功添加到路由器');
	}
	
	// 添加工单详情页路由（动态路由，不在菜单中显示）
	router.addRoute({
		path: '/workorder/detail/:id',
		name: 'workorderDetail',
		component: () => import('/@/views/plugins/workorder/detail.vue'),
		meta: {
			title: '工单详情',
			isHide: true, // 不在菜单中显示
			isKeepAlive: false,
			isAffix: false,
			isIframe: false,
			roles: ['admin'],
		},
	});
	const storesRoutesList = useRoutesList(pinia);
	storesRoutesList.setRoutesList([...dynamicRoutes[0].children,...frameOutRouter]);
	const storesTagsView = useTagsViewRoutes(pinia);
	storesTagsView.setTagsViewRoutes([...dynamicRoutes[0].children,...frameOutRouter])

}

/**
 * 设置路由到 vuex routesList 中（已处理成多级嵌套路由）及缓存多级嵌套数组处理后的一维数组
 * @description 用于左侧菜单、横向菜单的显示
 * @description 用于 tagsView、菜单搜索中：未过滤隐藏的(isHide)
 */
export function setFilterMenuAndCacheTagsViewRoutes() {
	const storesRoutesList = useRoutesList(pinia);
	storesRoutesList.setRoutesList(dynamicRoutes[0].children as any);
	setCacheTagsViewRoutes();
}

/**
 * 缓存多级嵌套数组处理后的一维数组
 * @description 用于 tagsView、菜单搜索中：未过滤隐藏的(isHide)
 */
export function setCacheTagsViewRoutes() {
	const storesTagsView = useTagsViewRoutes(pinia);
	storesTagsView.setTagsViewRoutes(formatTwoStageRoutes(formatFlatteningRoutes(dynamicRoutes))[0].children);
}

/**
 * 处理路由格式及添加捕获所有路由或 404 Not found 路由
 * @description 替换 dynamicRoutes（/@/router/route）第一个顶级 children 的路由
 * @returns 返回替换后的路由数组
 */
export function setFilterRouteEnd() {
	let filterRouteEnd: any = formatTwoStageRoutes(formatFlatteningRoutes(dynamicRoutes));
	// notFoundAndNoPower 防止 404、401 不在 layout 布局中，不设置的话，404、401 界面将全屏显示
	// 关联问题 No match found for location with path 'xxx'
	filterRouteEnd[0].children = [...filterRouteEnd[0].children, ...notFoundAndNoPower];
	return filterRouteEnd;
}

/**
 * 添加动态路由
 * @method router.addRoute
 * @description 此处循环为 dynamicRoutes（/@/router/route）第一个顶级 children 的路由一维数组，非多级嵌套
 * @link 参考：https://next.router.vuejs.org/zh/api/#addroute
 */
export async function setAddRoute() {
	const routes = setFilterRouteEnd();
	console.log('[setAddRoute] 准备添加的路由数量:', routes.length);
	// 查找督办中心路由
	const supervisionRoute = routes[0]?.children?.find((r: any) => r.path === '/supervision');
	if (supervisionRoute) {
		console.log('[setAddRoute] 找到督办中心路由，准备添加:', supervisionRoute);
		console.log('[setAddRoute] 督办中心组件类型:', typeof supervisionRoute.component);
	} else {
		console.warn('[setAddRoute] 未找到督办中心路由！所有路由:', routes[0]?.children?.map((r: any) => ({ path: r.path, name: r.name })));
	}
	routes.forEach((route: RouteRecordRaw) => {
		router.addRoute(route);
	});
	// 验证督办中心路由是否已添加
	const addedSupervisionRoute = router.getRoutes().find(r => r.path === '/supervision');
	if (addedSupervisionRoute) {
		console.log('[setAddRoute] 督办中心路由已成功添加');
	} else {
		console.error('[setAddRoute] 督办中心路由添加失败！');
		console.log('[setAddRoute] 所有已注册的路由:', router.getRoutes().map(r => ({ path: r.path, name: r.name })));
	}
	// 添加工单详情页路由（动态路由，不在菜单中显示）
	router.addRoute({
		path: '/workorder/detail/:id',
		name: 'workorderDetail',
		component: () => import('/@/views/plugins/workorder/detail.vue'),
		meta: {
			title: '工单详情',
			isHide: true, // 不在菜单中显示
			isKeepAlive: false,
			isAffix: false,
			isIframe: false,
			roles: ['admin'],
		},
	});
}

/**
 * 请求后端路由菜单接口
 * @description isRequestRoutes 为 true，则开启后端控制路由
 * @returns 返回后端路由菜单数据
 */
export function getBackEndControlRoutes() {
	//获取所有的按钮权限
	BtnPermissionStore().getBtnPermissionStore();
	// 获取系统配置
	SystemConfigStore().getSystemConfigs()
	// 获取所有部门信息
	useDeptInfoStore().requestDeptInfo()
	// 获取字典信息
	DictionaryStore().getSystemDictionarys()
	return menuApi.getSystemMenu();
}

/**
 * 重新请求后端路由菜单接口
 * @description 用于菜单管理界面刷新菜单（未进行测试）
 * @description 路径：/src/views/system/menu/component/addMenu.vue
 */
export function setBackEndControlRefreshRoutes() {
	getBackEndControlRoutes();
}

/**
 * 后端路由 component 转换
 * @param routes 后端返回的路由表数组
 * @returns 返回处理成函数后的 component
 */
export function backEndComponent(routes: any) {
	if (!routes) return;
	return routes.map((item: any) => {
		// 特殊处理：如果 is_catalog 为 true 但有 component 路径，说明配置错误，应该当作普通页面处理
		const hasComponentPath = item.component && typeof item.component === 'string' && item.component.trim() !== '';
		if (item.is_catalog && hasComponentPath) {
			console.warn(`[backEndComponent] 检测到菜单 ${item.name || item.path} 被标记为目录但有组件路径，自动修复为普通页面`, item);
			item.is_catalog = false;
		}
		
		if (item.component) {
			// 如果 component 是字符串，需要转换为组件函数
			if (typeof item.component === 'string') {
				const componentPath = item.component as string;
				// 调试督办中心组件加载
				if (componentPath.includes('supervision')) {
					console.log(`[backEndComponent] 开始加载督办中心组件: ${componentPath}`, item);
				}
				const importedComponent = dynamicImport(dynamicViewsModules, componentPath);
				if (importedComponent) {
					item.component = importedComponent;
					if (componentPath.includes('supervision')) {
						console.log(`[backEndComponent] 督办中心组件加载成功:`, item);
					}
				} else {
					console.error(`[backEndComponent] 无法加载组件: ${componentPath}`, item);
					// 组件加载失败时，设置一个错误组件，避免路由无法渲染
					item.component = () => Promise.resolve({
						default: {
							template: '<div style="padding: 20px; text-align: center;"><h3 style="color: #f56c6c;">组件加载失败</h3><p>无法加载组件: ' + componentPath + '</p><p style="color: #909399; font-size: 12px;">请检查组件路径是否正确</p></div>'
						}
					});
				}
			}
		}
		// 只有在没有组件路径的情况下，才将目录设置为 parent 组件
		if(item.is_catalog && !hasComponentPath){
			// 对目录的处理
			const catalogComponent = dynamicImport(dynamicViewsModules, 'layout/routerView/parent');
			if (catalogComponent) item.component = catalogComponent;
		}
		if(item.is_link){
			// 对外链接的处理
			if(item.is_iframe){
				const iframeComponent = dynamicImport(dynamicViewsModules, 'layout/routerView/iframes');
				if (iframeComponent) item.component = iframeComponent;
			}else {
				const linkComponent = dynamicImport(dynamicViewsModules, 'layout/routerView/link');
				if (linkComponent) item.component = linkComponent;
			}
		}else{
			if(item.is_iframe){
				// const iframeRoute:RouteRecordRaw = {
				// 	...item
				// }
				// router.addRoute(iframeRoute)
				item.meta.isLink = item.link_url
				// item.path = `${item.path}Link`
				// item.name = `${item.name}Link`
				// item.meta.isIframe = item.is_iframe
				// item.meta.isKeepAlive = false
				// item.meta.isIframeOpen = true
				const linkComponent = dynamicImport(dynamicViewsModules, 'layout/routerView/link.vue');
				if (linkComponent) item.component = linkComponent;
			}
		}
		item.children && backEndComponent(item.children);
		return item;
	});
}

/**
 * 后端路由 component 转换函数
 * @param dynamicViewsModules 获取目录下的 .vue、.tsx 全部文件
 * @param component 当前要处理项 component
 * @returns 返回处理成函数后的 component
 */
export function dynamicImport(dynamicViewsModules: Record<string, Function>, component: string) {
	if (!component) {
		console.error('[backEnd.dynamicImport] component 为空');
		return false;
	}
	
	const keys = Object.keys(dynamicViewsModules);
	// 处理组件路径：移除开头的斜杠，移除 plugins/ 前缀
	let newComponent = component.replace(/^\//, '').replace(/^plugins\//, "");
	
	// 调试信息
	if (component.includes('supervision') || component.includes('home')) {
		console.log(`[backEnd.dynamicImport] 查找组件: ${component} -> ${newComponent}`);
		console.log(`[backEnd.dynamicImport] 可用路径数量: ${keys.length}`);
		console.log(`[backEnd.dynamicImport] 包含supervision的路径:`, keys.filter(k => k.includes('supervision')));
	}
	
	const matchKeys = keys.filter((key) => {
		// 移除 ../views 前缀
		let k = key.replace(/^\.\.\/views\//, '').replace(/^\.\.\//, '');
		// 移除 node_modules/@great-dream/ 前缀
		k = k.replace(/^node_modules\/@great-dream\//, '');
		// 移除文件扩展名
		k = k.replace(/\.(vue|tsx)$/, '');
		// 移除开头的斜杠
		k = k.replace(/^\//, '');
		
		// 匹配处理后的路径：精确匹配或路径结尾匹配
		// 例如：plugins/supervision/index 应该匹配到 ../views/plugins/supervision/index.vue
		// 处理后：supervision/index 应该匹配到 plugins/supervision/index
		const matches = k === newComponent || k.endsWith(`/${newComponent}`) || k === `plugins/${newComponent}` || k.endsWith(`/plugins/${newComponent}`);
		
		if ((component.includes('supervision') || component.includes('home')) && matches) {
			console.log(`[backEnd.dynamicImport] 匹配成功: ${key} -> ${k} === ${newComponent}`);
		}
		
		return matches;
	});
	
	if (matchKeys?.length === 1) {
		const matchKey = matchKeys[0];
		if (component.includes('supervision') || component.includes('home')) {
			console.log(`[backEnd.dynamicImport] 找到唯一匹配: ${component} -> ${matchKey}`);
		}
		return dynamicViewsModules[matchKey];
	}
	if (matchKeys?.length > 1) {
		console.warn(`[backEnd.dynamicImport] 找到多个匹配的组件路径: ${component}`, matchKeys);
		// 优先选择最精确的匹配（路径最长的）
		const bestMatch = matchKeys.reduce((prev, curr) => {
			return curr.length > prev.length ? curr : prev;
		});
		console.log(`[backEnd.dynamicImport] 选择最佳匹配: ${bestMatch}`);
		return dynamicViewsModules[bestMatch];
	}
	// 如果没有匹配到，尝试直接匹配完整路径
	if (matchKeys?.length === 0) {
		// 尝试多种匹配方式
		const directMatch = keys.find((key) => {
			// 方式1: 直接包含 supervision/index 或 system/home/index
			if ((component.includes('supervision') && key.includes('supervision/index')) ||
			    (component.includes('system/home') && key.includes('system/home/index'))) return true;
			// 方式2: 标准化后匹配 - 移除所有前缀和扩展名后精确匹配
			const normalizedKey = key.replace(/^\.\.\/views\//, '').replace(/^node_modules\/@great-dream\//, '').replace(/\.(vue|tsx)$/, '');
			const normalizedComponent = component.replace(/^\//, '').replace(/^plugins\//, '');
			// 检查是否以 normalizedComponent 结尾
			if (normalizedKey.endsWith(normalizedComponent) || normalizedKey === normalizedComponent) return true;
			// 方式3: 检查是否包含完整路径
			if (normalizedKey.includes(normalizedComponent)) return true;
			return false;
		});
		if (directMatch) {
			console.warn(`[backEnd.dynamicImport] 使用直接匹配找到组件: ${component} -> ${directMatch}`);
			return dynamicViewsModules[directMatch];
		}
		// 最后尝试：精确匹配 plugins/supervision/index 格式
		const componentWithPlugins = component.startsWith('plugins/') ? component : `plugins/${component}`;
		const finalMatch = keys.find((key) => {
			const normalizedKey = key.replace(/^\.\.\/views\//, '').replace(/\.(vue|tsx)$/, '');
			return normalizedKey === componentWithPlugins || normalizedKey.endsWith(`/${componentWithPlugins}`);
		});
		if (finalMatch) {
			console.warn(`[backEnd.dynamicImport] 使用最终匹配找到组件: ${component} -> ${finalMatch}`);
			return dynamicViewsModules[finalMatch];
		}
		console.error(`[backEnd.dynamicImport] 未找到匹配的组件: ${component}`, '可用路径:', keys.filter(k => k.includes('supervision') || k.includes('home')).slice(0, 10));
		return false;
	}
	return false;
}
