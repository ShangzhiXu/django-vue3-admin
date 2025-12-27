import {defineStore} from 'pinia';
import {FrontendMenu} from './interface';
import {Session} from '/@/utils/storage';
import {request} from '../utils/service';
import XEUtils from "xe-utils";
import {RouteRecordRaw} from "vue-router";
import {useKeepALiveNames} from "/@/stores/keepAliveNames";
import pinia from "/@/stores/index";


const layouModules: any = import.meta.glob('../layout/routerView/*.{vue,tsx}');
const viewsModules: any = import.meta.glob('../views/**/*.{vue,tsx}');


/**
 * 获取目录下的 .vue、.tsx 全部文件
 * @method import.meta.glob
 * @link 参考：https://cn.vitejs.dev/guide/features.html#json
 */
const dynamicViewsModules: Record<string, Function> = Object.assign({}, { ...layouModules }, { ...viewsModules });

/**
 * 后端路由 component 转换函数
 * @param dynamicViewsModules 获取目录下的 .vue、.tsx 全部文件
 * @param component 当前要处理项 component
 * @returns 返回处理成函数后的 component
 */
export function dynamicImport(dynamicViewsModules: Record<string, Function>, component: string) {
    if (!component) {
        console.error('dynamicImport: component 为空');
        return false;
    }
    
    const keys = Object.keys(dynamicViewsModules);
    // 处理组件路径：移除开头的斜杠，移除 plugins/ 前缀
    let newComponent = component.replace(/^\//, '').replace(/^plugins\//, "");
    
    // 调试信息
    if (component.includes('supervision')) {
        console.log(`[dynamicImport] 查找组件: ${component} -> ${newComponent}`);
        console.log(`[dynamicImport] 相关路径:`, keys.filter(k => k.includes('supervision')).slice(0, 5));
    }
    
    const matchKeys = keys.filter((key) => {
        // 移除 ../views 前缀
        let k = key.replace(/^\.\.\/views\//, '').replace(/^\.\.\//, '');
        // 移除文件扩展名
        k = k.replace(/\.(vue|tsx)$/, '');
        // 移除开头的斜杠
        k = k.replace(/^\//, '');
        
        // 匹配处理后的路径：精确匹配或路径结尾匹配
        // 例如：plugins/supervision/index 应该匹配到 ../views/plugins/supervision/index.vue
        // 处理后：supervision/index 应该匹配到 plugins/supervision/index
        const matches = k === newComponent || k.endsWith(`/${newComponent}`) || k === `plugins/${newComponent}` || k.endsWith(`/plugins/${newComponent}`);
        
        if (component.includes('supervision') && matches) {
            console.log(`[dynamicImport] 匹配成功: ${key} -> ${k} === ${newComponent}`);
        }
        
        return matches;
    });
    
    if (matchKeys?.length === 1) {
        const matchKey = matchKeys[0];
        if (component.includes('supervision')) {
            console.log(`[dynamicImport] 找到唯一匹配: ${component} -> ${matchKey}`);
        }
        return dynamicViewsModules[matchKey];
    }
    if (matchKeys?.length > 1) {
        console.warn(`[dynamicImport] 找到多个匹配的组件路径: ${component}`, matchKeys);
        // 优先选择最精确的匹配（路径最长的）
        const bestMatch = matchKeys.reduce((prev, curr) => {
            return curr.length > prev.length ? curr : prev;
        });
        console.log(`[dynamicImport] 选择最佳匹配: ${bestMatch}`);
        return dynamicViewsModules[bestMatch];
    }
    // 如果没有匹配到，尝试直接匹配完整路径
    if (matchKeys?.length === 0) {
        // 尝试多种匹配方式
        const directMatch = keys.find((key) => {
            // 方式1: 直接包含 supervision/index
            if (component.includes('supervision') && key.includes('supervision/index')) return true;
            // 方式2: 标准化后匹配 - 移除所有前缀和扩展名后精确匹配
            const normalizedKey = key.replace(/^\.\.\/views\//, '').replace(/\.(vue|tsx)$/, '');
            const normalizedComponent = component.replace(/^\//, '').replace(/^plugins\//, '');
            // 检查是否以 normalizedComponent 结尾
            if (normalizedKey.endsWith(normalizedComponent) || normalizedKey === normalizedComponent) return true;
            // 方式3: 检查是否包含完整路径
            if (normalizedKey.includes(normalizedComponent)) return true;
            return false;
        });
        if (directMatch) {
            console.warn(`[dynamicImport] 使用直接匹配找到组件: ${component} -> ${directMatch}`);
            return dynamicViewsModules[directMatch];
        }
        // 最后尝试：精确匹配 plugins/supervision/index 格式
        const componentWithPlugins = component.startsWith('plugins/') ? component : `plugins/${component}`;
        const finalMatch = keys.find((key) => {
            const normalizedKey = key.replace(/^\.\.\/views\//, '').replace(/\.(vue|tsx)$/, '');
            return normalizedKey === componentWithPlugins || normalizedKey.endsWith(`/${componentWithPlugins}`);
        });
        if (finalMatch) {
            console.warn(`[dynamicImport] 使用最终匹配找到组件: ${component} -> ${finalMatch}`);
            return dynamicViewsModules[finalMatch];
        }
        console.error(`[dynamicImport] 未找到匹配的组件: ${component}`, '可用路径:', keys.filter(k => k.includes('supervision')).slice(0, 10));
        return false;
    }
    return false;
}

/**
 * @description: 处理后端菜单数据格式
 * @param {Array} menuData
 * @return {*}
 */
export const handleMenu = (menuData: Array<any>) => {
    // 框架内路由
    const frameInRoutes:Array<any> = []
    // 框架外路由
    const frameOutRoutes:Array<any> = []
    // 需要缓存的路由
    const cacheList:Array<any> = []
    // 先处理menu meta数据转换
    const handleMeta = (item: any) => {
        item.path = item.web_path
        item.meta = {
            title: item.title,
            isLink: item.link_url,
            isHide: !item.visible,
            isKeepAlive: item.cache,
            isAffix: item.is_affix,
            isIframe: item.is_iframe,
            roles: ['admin'],
            icon: item.icon
        }
        // 只有在不是目录、不是链接的情况下才处理组件
        if (!item.is_catalog && !item.is_link && item.component) {
            const componentPath = item.component as string;
            if (componentPath.includes('supervision')) {
                console.log(`[handleMenu] 处理督办中心组件:`, componentPath, item);
            }
            // 如果 component 是字符串，需要转换为组件函数
            if (typeof item.component === 'string') {
                const importedComponent = dynamicImport(dynamicViewsModules, componentPath);
                if (importedComponent) {
                    item.component = importedComponent;
                    if (componentPath.includes('supervision')) {
                        console.log(`[handleMenu] 督办中心组件加载成功:`, item);
                    }
                } else {
                    console.error(`[handleMenu] 无法加载组件: ${componentPath}`, item);
                    // 组件加载失败时，设置一个错误组件，避免路由无法渲染
                    item.component = () => Promise.resolve({
                        default: {
                            template: '<div style="padding: 20px; text-align: center;"><h3 style="color: #f56c6c;">组件加载失败</h3><p>无法加载组件: ' + componentPath + '</p><p style="color: #909399; font-size: 12px;">请检查组件路径是否正确</p></div>'
                        }
                    });
                }
            }
        }
        if(item.is_catalog){
            // 对目录的处理
            const catalogComponent = dynamicImport(dynamicViewsModules, 'layout/routerView/parent');
            if (catalogComponent) item.component = catalogComponent;
        }
        if(item.is_link){
            // 对外链接的处理
            item.meta.isIframe = !item.is_iframe
            if(item.is_iframe){
                const iframeComponent = dynamicImport(dynamicViewsModules, 'layout/routerView/link');
                if (iframeComponent) item.component = iframeComponent;
            }else {
                const linkComponent = dynamicImport(dynamicViewsModules, 'layout/routerView/iframes');
                if (linkComponent) item.component = linkComponent;
            }
        }else{
            if(item.is_iframe){
                const route = JSON.parse(JSON.stringify(item))
                route.meta.isLink = ''
                route.path = `${item.web_path}`
                route.name =  `${item.name}`
                route.meta.isIframe = true
                route.meta.isKeepAlive = false
                route.meta.isIframeOpen = true
                route.component = item.component
                frameOutRoutes.push(route)
                item.path = `${item.web_path}FrameOut`
                item.name =  `${item.name}FrameOut`
                item.meta.isLink = item.web_path
                item.meta.isIframe = !item.is_iframe
                //item.meta.isIframeOpen = true
                const linkComponent = dynamicImport(dynamicViewsModules, 'layout/routerView/link.vue');
                if (linkComponent) item.component = linkComponent;
            }
        }
        item.children && handleMeta(item.children);
        if (item.meta.isKeepAlive && item.meta.isKeepAlive && item.component_name != "") {
            cacheList.push(item.name);
        }
        return item
    }
    menuData.forEach((val) => {
        frameInRoutes.push(handleMeta(val))
    })
    const stores = useKeepALiveNames(pinia);
    stores.setCacheKeepAlive(cacheList);
    const data = XEUtils.toArrayTree(frameInRoutes, {
        parentKey: 'parent',
        strict: true,
    })
    const dynamicRoutes = [
        {
            path: '/home', name: 'home',
            component: dynamicImport(dynamicViewsModules, '/system/home/index'),
            meta: {
                title: 'message.router.home',
                isLink: '',
                isHide: false,
                isKeepAlive: true,
                isAffix: true,
                isIframe: false,
                roles: ['admin'],
                icon: 'iconfont icon-shouye'
            }
        },
        ...data
    ]
    return {frameIn:dynamicRoutes,frameOut:frameOutRoutes}
}

export const useFrontendMenuStore = defineStore('frontendMenu',{
    state: (): FrontendMenu => ({
        arrayRouter: [],
        treeRouter: [],
        frameInRoutes:[],
        frameOutRoutes:[]
    }),
    actions:{
        async requestMenu(){
           return  request({
                url: '/api/system/menu/web_router/',
                method: 'get',
                params:{},
            }).then((res:any)=>{
                return res.data
           });
        },
        async handleRouter(){
            const menuData = await this.requestMenu();
            this.arrayRouter = menuData
            const {frameIn,frameOut} = handleMenu(menuData);
            this.treeRouter = [...frameIn,...frameOut]
            this.frameInRoutes=frameIn
            this.frameOutRoutes=frameOut
        },
        async getRouter(){
            await this.handleRouter()
            return {
                frameInRoutes:this.frameInRoutes,
                frameOutRoutes:this.frameOutRoutes,
                treeRouter:this.treeRouter
            }
        }
    }
})
