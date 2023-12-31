importScripts("/js/init.js");

// Service Worker 5分钟后会强制终止扩展
// https://bugs.chromium.org/p/chromium/issues/detail?id=1271154
// https://stackoverflow.com/questions/66618136/persistent-service-worker-in-chrome-extension/70003493#70003493
// chrome.webNavigation.onBeforeNavigate.addListener(function () { return; });
chrome.webNavigation.onHistoryStateUpdated.addListener(function () { return; });
chrome.runtime.onConnect.addListener(function (Port) {
    if (Port.name !== "HeartBeat") return;
    Port.postMessage("HeartBeat");
    Port.onMessage.addListener(function (message, Port) { return; });
    const interval = setInterval(function () {
        clearInterval(interval);
        Port.disconnect();
    }, 250000);
    Port.onDisconnect.addListener(function () {
        if (interval) { clearInterval(interval); }
    });
});

chrome.alarms.create("nowClear", { when: Date.now() + 3000 });  // 3秒后清理立即清理一次
chrome.alarms.create("clear", { periodInMinutes: 60 }); // 60分钟清理一次冗余数据
chrome.alarms.onAlarm.addListener(function (alarm) {
    if (alarm.name === "nowClear" || alarm.name === "clear") {
        clearRedundant();
        return;
    }
    if (alarm.name === "save") {
        chrome.storage.local.set({ MediaData: cacheData });
        return;
    }
});

const tabStatus={};
const tabReqCnt={};
function set_reqcnt_s(tabId){
    if(tabReqCnt[tabId]){
        let req_cnt_s=tabReqCnt[tabId][0];
        tabReqCnt[tabId][0]=req_cnt_s+1;

    }else{
        tabReqCnt[tabId]=[1,0];
    }
     return tabReqCnt[tabId];
}
function set_reqcnt_e(tabId){
    if(tabReqCnt[tabId]){
        let req_cnt_e=tabReqCnt[tabId][1];
        tabReqCnt[tabId][1]=req_cnt_e+1;
    }else{
        tabReqCnt[tabId]=[1,1];
    }
    return tabReqCnt[tabId];
}
// onBeforeRequest 浏览器发送请求之前使用正则匹配发送请求的URL
chrome.webRequest.onBeforeRequest.addListener(
    function (data) {
        if(['image','media'].includes(data.type)){
            set_reqcnt_s(data.tabId);
            // req_cnt_s++;
            // console.debug(`webRequest.onBeforeRequest: G.tabId=${G.tabId} data.tabId=${data.tabId} data.type=${data.type} data.requestId=${data.requestId} req-cnt=${req_cnt_s}/${req_cnt_e} ${data.url}`);
        }
        try { findMedia(data, true); } catch (e) { console.log(e); }
    }, { urls: ["<all_urls>"] }, ["requestBody"]
);
// 保存requestHeaders
chrome.webRequest.onSendHeaders.addListener(
    function (data) {
        // req_cnt_s++;
        const requestHeaders = getRequestHeaders(data);
        requestHeaders && G.requestHeaders.set(data.requestId, requestHeaders);
    }, { urls: ["<all_urls>"] }, ['requestHeaders',
        chrome.webRequest.OnBeforeSendHeadersOptions.EXTRA_HEADERS].filter(Boolean)
);
// onResponseStarted 浏览器接收到第一个字节触发，保证有更多信息判断资源类型
chrome.webRequest.onResponseStarted.addListener(
    function (data) {
        if(['image','media'].includes(data.type)) {
            // req_cnt_e++;
        }
        try {
            const requestHeaders = G.requestHeaders.get(data.requestId);
            if (requestHeaders) {
                data.requestHeaders = requestHeaders;
                G.requestHeaders.delete(data.requestId);
            }
            findMedia(data);
        } catch (e) { console.log(e, data); }
    }, { urls: ["<all_urls>"] }, ["responseHeaders"]
);
// 删除失败的requestHeadersData
chrome.webRequest.onErrorOccurred.addListener(
    function (data) {
         if(['image','media'].includes(data.type)) {
             se=set_reqcnt_e(data.tabId);
             // req_cnt_e++
             // console.debug(`webRequest.onErrorOccurred: G.tabId=${G.tabId} data.tabId=${data.tabId} data.type=${data.type} data.requestId=${data.requestId} req-cnt=${se[0]}/${se[1]} ${data.url}`);
         }
        G.requestHeaders.delete(data.requestId);
        G.blackList.delete(data.requestId);
    }, { urls: ["<all_urls>"] }
);
chrome.webRequest.onCompleted.addListener(
    function(data) {
         if(['image','media'].includes(data.type)) {
             se=set_reqcnt_e(data.tabId);
             // req_cnt_e++
             // console.debug(`webRequest.onCompleted: G.tabId=${G.tabId} data.tabId=${data.tabId} data.type=${data.type} data.requestId=${data.requestId} req-cnt=${se[0]}/${se[1]} ${data.url}`);
         }
    },
    {urls: ["<all_urls>"]},
    ["responseHeaders"]
);

function findMedia(data, isRegex = false, filter = false, timer = false) {
    // console.log("findeMedia:",data);
    if (timer) { return; }
    // Service Worker被强行杀死之后重新自我唤醒，等待全局变量初始化完成。
    if (!G || !G.initSyncComplete || !G.initLocalComplete || G.tabId == undefined || cacheData.init) {
        setTimeout(() => {
            findMedia(data, isRegex, filter, true);
        }, 233);
        return;
    }
    if (!G.enable) { return; }
    if (!isRegex && G.blackList.has(data.requestId)) {
        G.blackList.delete(data.requestId);
        return;
    }
    // 屏蔽特殊页面发起的资源
    if (data.initiator != "null" &&
        data.initiator != undefined &&
        isSpecialPage(data.initiator)) { return; }
    if (G.isFirefox &&
        data.originUrl &&
        isSpecialPage(data.originUrl)) { return; }
    // 屏蔽特殊页面的资源
    if (isSpecialPage(data.url)) { return; }
    const urlParsing = new URL(data.url);
    let [name, ext] = fileNameParse(urlParsing.pathname);

    //正则匹配
    if (isRegex && !filter) {
        for (let key in G.Regex) {
            if (!G.Regex[key].state) { continue; }
            G.Regex[key].regex.lastIndex = 0;
            let result = G.Regex[key].regex.exec(data.url);
            if (result == null) { continue; }
            if (G.Regex[key].blackList) {
                G.blackList.add(data.requestId);
                return;
            }
            data.extraExt = G.Regex[key].ext ? G.Regex[key].ext : undefined;
            if (result.length == 1) {
                findMedia(data, true, true);
                return;
            }
            result.shift();
            result = result.map(str => decodeURIComponent(str));
            if (!result[0].startsWith('https://') && !result[0].startsWith('http://')) {
                result[0] = urlParsing.protocol + "//" + data.url;
            }
            data.url = result.join("");
            findMedia(data, true, true);
            return;
        }
        return;
    }

    let header = {};
    if (!isRegex) {
        header = getResponseHeadersValue(data);
        // 通过视频范围计算完整视频大小
        if (header["range"]) {
            const size = header["range"].match(reRange);
            if (size) {
                header["size"] = parseInt(header["size"] * (size[3] / (size[2] - size[1])));
            }
        }
    }

    //检查后缀
    if (!isRegex && !filter && ext != undefined) {
        filter = CheckExtension(ext, header["size"]);
        if (filter == "break") { return; }
    }

    //检查类型
    if (!isRegex && !filter && header["type"] != undefined) {
        filter = CheckType(header["type"], header["size"]);
        if (filter == "break") { return; }
    }

    //查找附件
    if (!isRegex && !filter && header["attachment"] != undefined) {
        const res = header["attachment"].match(reFilename);
        if (res && res[1]) {
            [name, ext] = fileNameParse(decodeURIComponent(res[1]));
            filter = CheckExtension(ext, 0);
            if (filter == "break") { return; }
        }
    }

    //放过类型为media的资源
    if (!isRegex && data.type == "media") {
        filter = true;
    }

    if (!filter) { return; }

    data.tabId = data.tabId == -1 ? G.tabId : data.tabId;

    cacheData[data.tabId] ??= [];
    cacheData[G.tabId] ??= [];

    // 查重 避免CPU占用 大于500 强制关闭查重
    if (G.checkDuplicates && cacheData[data.tabId].length <= 500) {
        for (let item of cacheData[data.tabId]) {
            if (item.url.length == data.url.length &&
                item.cacheURL.pathname == urlParsing.pathname &&
                item.cacheURL.host == urlParsing.host &&
                item.cacheURL.search == urlParsing.search) { return; }
        }
    }
    // console.log('findMedia:',data);
    chrome.tabs.get(data.tabId, async function (webInfo) {
        if (chrome.runtime.lastError) { return; }
        const info = {
            name: name,
            url: data.url,
            size: header["size"],
            ext: ext,
            type: data.mime ?? header["type"],
            tabId: data.tabId,
            isRegex: isRegex,
            requestId: data.requestId ?? Date.now().toString(),
            extraExt: data.extraExt,
            initiator: data.initiator,
            // referer: data.referer,
            requestHeaders: data.requestHeaders,
            cacheURL: { host: urlParsing.host, search: urlParsing.search, pathname: urlParsing.pathname }
        };
        // 不存在 initiator 和 referer 使用web url代替initiator
        if (info.initiator == undefined || info.initiator == "null") {
            info.initiator = info.requestHeaders?.referer ?? webInfo?.url;
        }
        // 装载页面信息
        info.title = webInfo?.title ?? "NULL";
        info.favIconUrl = webInfo?.favIconUrl;
        info.webUrl = webInfo?.url;
        // 屏蔽资源
        if (!isRegex && G.blackList.has(data.requestId)) {
            G.blackList.delete(data.requestId);
            return;
        }
        // 发送到popup 并检查自动下载
        chrome.runtime.sendMessage(info, function () {
            if (G.featAutoDownTabId.size > 0 && G.featAutoDownTabId.has(info.tabId)) {
                const downDir = info.title == "NULL" ? "CatCatch/" : stringModify(info.title) + "/";
                chrome.downloads.download({
                    url: info.url,
                    filename: downDir + info.name
                });
            }
            if (chrome.runtime.lastError) { return; }
        });
        // 储存数据
        cacheData[info.tabId] ??= [];
        cacheData[info.tabId].push(info);

        // 当前标签媒体数量大于100 开启防抖 等待5秒储存 或 积累10个资源储存一次。
        if (cacheData[info.tabId].length >= 100 && debounceCount <= 10) {
            debounceCount++;
            clearTimeout(debounce);
            debounce = setTimeout(function () { save(info.tabId); }, 5000);
            return;
        }
        // 时间间隔小于500毫秒 等待2秒储存
        if (Date.now() - debounceTime <= 500) {
            clearTimeout(debounce);
            debounceTime = Date.now();
            debounce = setTimeout(function () { save(info.tabId); }, 2000);
            return;
        }
        save(info.tabId);
    });
}
// cacheData数据 储存到 chrome.storage.local
function save(tabId) {
    clearTimeout(debounce);
    debounceTime = Date.now();
    debounceCount = 0;
    chrome.storage.local.set({ MediaData: cacheData }, function () {
        chrome.runtime.lastError && console.log(chrome.runtime.lastError);
    });
    cacheData[tabId] && SetIcon({ number: cacheData[tabId].length, tabId: tabId });
    // console.log("save:",cacheData[tabId]);
    if(cacheData[tabId]&&cacheData[tabId].length>0){
        reportToServer(tabId);
    }
}

// 监听来自popup 和 options的请求
chrome.runtime.onMessage.addListener(function (Message, sender, sendResponse) {
    if (!G.initLocalComplete || !G.initSyncComplete) {
        sendResponse("error");
        return true;
    }
    if (Message.Message == "pushData") {
        chrome.storage.local.set({ MediaData: cacheData });
        sendResponse("ok");
        return true;
    }
    if (Message.Message == "getAllData") {
        sendResponse(cacheData);
        return true;
    }
    // 图标设置
    if (Message.Message == "ClearIcon") {
        if (Message.type) {
            G.tabId && SetIcon({ tabId: G.tabId });
        } else {
            SetIcon({ tips: false });
        }
        sendResponse("ok");
        return true;
    }
    if (Message.Message == "enable") {
        G.enable = !G.enable;
        chrome.storage.sync.set({ enable: G.enable });
        chrome.action.setIcon({ path: G.enable ? "/img/icon.png" : "/img/icon-disable.png" });
        sendResponse(G.enable);
        return true;
    }
    Message.tabId = Message.tabId ?? G.tabId;
    if (Message.Message == "getData") {
        sendResponse(cacheData[Message.tabId]);
        console.log('getData: ',Message.tabId);
        return true;
    }
    if (Message.Message == "getButtonState") {
        let state = {
            MobileUserAgent: G.featMobileTabId.has(Message.tabId),
            AutoDown: G.featAutoDownTabId.has(Message.tabId),
            enable: G.enable,
        }
        G.scriptList.forEach(function (item, key) {
            state[item.key] = item.tabId.has(Message.tabId);
        });
        sendResponse(state);
        return true;
    }
    // 模拟手机
    if (Message.Message == "mobileUserAgent") {
        mobileUserAgent(Message.tabId, !G.featMobileTabId.has(Message.tabId));
        chrome.tabs.reload(Message.tabId, { bypassCache: true });
        sendResponse("ok");
        return true;
    }
    // 自动下载
    if (Message.Message == "autoDown") {
        if (G.featAutoDownTabId.has(Message.tabId)) {
            G.featAutoDownTabId.delete(Message.tabId);
        } else {
            G.featAutoDownTabId.add(Message.tabId);
        }
        chrome.storage.local.set({ featAutoDownTabId: Array.from(G.featAutoDownTabId) });
        sendResponse("ok");
        return true;
    }
    // 脚本
    if (Message.Message == "script") {
        if (!G.scriptList.has(Message.script)) {
            sendResponse("error no exists");
            return false;
        }
        const script = G.scriptList.get(Message.script);
        const scriptTabid = script.tabId;
        const refresh = Message.refresh ?? script.refresh;
        if (scriptTabid.has(Message.tabId)) {
            scriptTabid.delete(Message.tabId);
            refresh && chrome.tabs.reload(Message.tabId, { bypassCache: true });
            sendResponse("ok");
            return true;
        }
        scriptTabid.add(Message.tabId);
        if (refresh) {
            chrome.tabs.reload(Message.tabId, { bypassCache: true });
        } else {
            chrome.scripting.executeScript({
                target: { tabId: Message.tabId, allFrames: script.allFrames },
                files: ["catch-script/" + Message.script],
                injectImmediately: true,
                world: script.world
            });
        }
        sendResponse("ok");
        return true;
    }
    // Heart Beat
    if (Message.Message == "HeartBeat") {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            if (tabs[0] && tabs[0].id) {
                G.tabId = tabs[0].id;
            }
        });
        sendResponse("HeartBeat OK");
        return true;
    }
    // 清理数据
    if (Message.Message == "clearData") {
        // 当前标签
        if (Message.type) {
            delete cacheData[Message.tabId];
            chrome.storage.local.set({ MediaData: cacheData });
            clearRedundant();
            sendResponse("OK");
            return true;
        }
        // 其他标签
        for (let item in cacheData) {
            if (item == Message.tabId) { continue; }
            delete cacheData[item];
        }
        chrome.storage.local.set({ MediaData: cacheData });
        clearRedundant();
        sendResponse("OK");
        return true;
    }
    // 清理冗余数据
    if (Message.Message == "clearRedundant") {
        clearRedundant();
        sendResponse("OK");
        return true;
    }
    // 从 content-script 或 catch-script 传来的媒体url
    if (Message.Message == "addMedia") {
        chrome.tabs.query({}, function (tabs) {
            for (let item of tabs) {
                if (item.url == Message.href) {
                    findMedia({ url: Message.url, tabId: item.id, extraExt: Message.extraExt, mime: Message.mime, requestId: Message.requestId }, true, true);
                    return true;
                }
            }
            findMedia({ url: Message.url, tabId: -1, extraExt: Message.extraExt, mime: Message.mime, requestId: Message.requestId, initiator: Message.href }, true, true);
        });
        sendResponse("ok");
        return true;
    }
    // ffmpeg在线转码
    if (Message.Message == "catCatchFFmpeg") {
        const data = { Message: "ffmpeg", action: Message.action, media: Message.media, title: Message.title, url: Message.url, extra: Message.extra, tabId: Message.tabId };
        chrome.tabs.query({ url: ffmpeg.url }, function (tabs) {
            if (chrome.runtime.lastError || !tabs.length) {
                chrome.tabs.create({ url: ffmpeg.url }, function (tab) {
                    ffmpeg.tab = tab.id;
                    ffmpeg.data = data;
                });
                return true;
            }
            chrome.tabs.sendMessage(tabs[0].id, data);
        });
        sendResponse("ok");
        return true;
    }
    sendResponse("Error");
    return true;
});

// 选定标签 更新G.tabId
chrome.tabs.onHighlighted.addListener(function (activeInfo) {
    if (!activeInfo.tabId || activeInfo.tabId == -1) { return; }
    G.tabId = activeInfo.tabId;
});

// 切换标签，更新全局变量G.tabId 更新图标
chrome.tabs.onActivated.addListener(function (activeInfo) {
    G.tabId = activeInfo.tabId;
    if (cacheData[G.tabId] !== undefined) {
        SetIcon({ number: cacheData[G.tabId].length, tabId: G.tabId });
        return;
    }
    SetIcon({ tabId: G.tabId });
});

// 切换窗口，更新全局变量G.tabId
chrome.windows.onFocusChanged.addListener(function (activeInfo) {
    if (!activeInfo.tabId || activeInfo.tabId == -1) { return; }
    G.tabId = activeInfo.tabId;
}, { filters: ["normal"] });

// 标签更新 清理数据
chrome.tabs.onUpdated.addListener(function (tabId, changeInfo, tab) {
    if (isSpecialPage(tab.url) || tabId <= 0 || !G.initSyncComplete) { return; }
    // console.debug('changeInfo=',changeInfo,'tab=',tab);
    if (changeInfo.status && changeInfo.status == "loading" && G.autoClearMode == 2) {
        chrome.alarms.get("save", function (alarm) {
            if (!alarm) {
                delete cacheData[tabId];
                SetIcon({ tabId: tabId });
                chrome.alarms.create("save", { when: Date.now() + 1000 });
            }
        });
    }
    if(changeInfo.status) {
        tabStatus[tabId] = changeInfo.status;
    }
    if(changeInfo.status && changeInfo.status === "loading"){
        req_cnt_s=0;
        req_cnt_e=0;
    }

});

// 载入frame时
chrome.webNavigation.onCommitted.addListener(function (details) {
    console.debug('webNavigation.onCommitted',details.tabId);
    if (isSpecialPage(details.url) || details.tabId <= 0 || !G.initSyncComplete) { return; }

    // 刷新清理角标数
    if (details.frameId == 0 && (details.transitionType == "reload" || details.transitionType == "link") && G.autoClearMode == 1) {
        delete cacheData[details.tabId];
        chrome.storage.local.set({ MediaData: cacheData });
        SetIcon({ tabId: details.tabId });
    }

    // chrome内核版本 102 以下不支持 chrome.scripting.executeScript API
    if (G.version < 102) { return; }

    // catch-script 脚本
    G.scriptList.forEach(function (item, script) {
        if (!item.tabId.has(details.tabId) || !item.allFrames) { return true; }
        chrome.scripting.executeScript({
            target: { tabId: details.tabId, frameIds: [details.frameId] },
            files: [`catch-script/${script}`],
            injectImmediately: true,
            world: item.world
        });
    });

    // 模拟手机
    if (G.initLocalComplete && G.featMobileTabId.size > 0 && G.featMobileTabId.has(details.tabId)) {
        chrome.scripting.executeScript({
            args: [G.MobileUserAgent.toString()],
            target: { tabId: details.tabId, frameIds: [details.frameId] },
            func: function () {
                Object.defineProperty(navigator, 'userAgent', { value: arguments[0], writable: false });
            },
            injectImmediately: true,
            world: "MAIN"
        });
    }
});

// 标签关闭 清除数据
chrome.tabs.onRemoved.addListener(function (tabId) {
    // 清理缓存数据
    chrome.alarms.get("nowClear", function (alarm) {
        !alarm && chrome.alarms.create("nowClear", { when: Date.now() + 1000 });
    });
});

// 快捷键
chrome.commands.onCommand.addListener(function (command) {
    if (command == "auto_down") {
        if (G.featAutoDownTabId.has(G.tabId)) {
            G.featAutoDownTabId.delete(G.tabId);
        } else {
            G.featAutoDownTabId.add(G.tabId);
        }
        chrome.storage.local.set({ featAutoDownTabId: Array.from(G.featAutoDownTabId) });
    } else if (command == "catch") {
        const scriptTabid = G.scriptList.get("catch.js").tabId;
        scriptTabid.has(G.tabId) ? scriptTabid.delete(G.tabId) : scriptTabid.add(G.tabId);
        chrome.tabs.reload(G.tabId, { bypassCache: true });
    } else if (command == "m3u8") {
        chrome.tabs.create({ url: "m3u8.html" });
    } else if (command == "clear") {
        delete cacheData[G.tabId];
        chrome.storage.local.set({ MediaData: cacheData });
        clearRedundant();
        SetIcon({ tabId: G.tabId });
    } else if (command == "enable") {
        G.enable = !G.enable;
        chrome.storage.sync.set({ enable: G.enable });
        chrome.action.setIcon({ path: G.enable ? "/img/icon.png" : "/img/icon-disable.png" });
    }
});

chrome.webNavigation.onCompleted.addListener(function (details) {
    if (ffmpeg.tab && details.tabId == ffmpeg.tab) {
        setTimeout(() => {
            chrome.tabs.sendMessage(details.tabId, ffmpeg.data);
            ffmpeg.data = undefined;
            ffmpeg.tab = 0;
        }, 500);
    }
    if(details.url!=='about:blank'){
        se=tabReqCnt[details.tabId];
        console.log(`webNavigation.onCompleted: req_cnt=${se[1]}/${se[0]}`)
        tabStatus[details.tabId] ='complete';
    }

});

chrome.webNavigation.onBeforeNavigate.addListener(function (details){
    console.debug('webNavigation.onBeforeNavigate',details.tabId,details.url);
    tabReqCnt[details.tabId]=[0,0];
});


chrome.tabs.onCreated.addListener(function(newTab) {
    // console.log("New tab created with ID: " + tab.id,tab);
    var info={tabId:newTab.id,url:newTab.pendingUrl,t:Date.now()};
    ws_send('tab_created',info);
});

//检查扩展名以及大小限制
function CheckExtension(ext, size) {
    const Ext = G.Ext.get(ext);
    if (!Ext) { return false; }
    if (!Ext.state) { return "break"; }
    if (Ext.size != 0 && size != undefined && size <= Ext.size * 1024) { return "break"; }
    return true;
}
//检查类型以及大小限制
function CheckType(dataType, dataSize) {
    const typeInfo = G.Type.get(dataType.split("/")[0] + "/*") || G.Type.get(dataType);
    if (!typeInfo) { return false; }
    if (!typeInfo.state) { return "break"; }
    if (typeInfo.size != 0 && dataSize != undefined && dataSize <= typeInfo.size * 1024) { return "break"; }
    return true;
}

// 获取文件名 后缀
function fileNameParse(pathname) {
    let fileName = decodeURI(pathname.split("/").pop());
    let ext = fileName.split(".");
    ext = ext.length == 1 ? undefined : ext.pop().toLowerCase();
    return [fileName, ext ? ext : undefined];
}
//获取Header属性的值
function getResponseHeadersValue(data) {
    const header = new Array();
    if (data.responseHeaders == undefined || data.responseHeaders.length == 0) { return header; }
    for (let item of data.responseHeaders) {
        switch (item.name.toLowerCase()) {
            case "content-length": header["size"] = item.value; break;
            case "content-type": header["type"] = item.value.split(";")[0].toLowerCase(); break;
            case "content-disposition": header["attachment"] = item.value; break;
            case "content-range": header["range"] = item.value; break;
        }
    }
    return header;
}
function getRequestHeaders(data) {
    if (data.requestHeaders == undefined || data.requestHeaders.length == 0) { return false; }
    const header = {};
    for (let item of data.requestHeaders) {
        item.name = item.name.toLowerCase();
        if (item.name == "referer") {
            header.referer = item.value.toLowerCase();
        }
        if (item.name == "origin") {
            header.origin = item.value.toLowerCase();
        }
    }
    if (Object.keys(header).length) {
        return header;
    }
    return false;
}
//设置扩展图标
function SetIcon(obj) {
    if (obj.tips != undefined) {
        obj.tips = obj.tips ? "/img/icon-tips.png" : "/img/icon.png";
        chrome.action.setIcon({ path: obj.tips });
    } else if (obj.number == 0 || obj.number == undefined) {
        chrome.action.setBadgeText({ text: "", tabId: obj.tabId }, function () { if (chrome.runtime.lastError) { return; } });
        chrome.action.setTitle({ title: "还没闻到味儿~", tabId: obj.tabId }, function () { if (chrome.runtime.lastError) { return; } });
    } else {
        obj.number = obj.number > 99 ? "99+" : obj.number.toString();
        chrome.action.setBadgeText({ text: obj.number, tabId: obj.tabId }, function () { if (chrome.runtime.lastError) { return; } });
        chrome.action.setTitle({ title: "抓到 " + obj.number + " 条鱼", tabId: obj.tabId }, function () { if (chrome.runtime.lastError) { return; } });
        console.log('set icon number: ',obj.number,obj.tabId);

    }
}

// 模拟手机端
function mobileUserAgent(tabId, change = false) {
    if (change) {
        G.featMobileTabId.add(tabId);
        chrome.storage.local.set({ featMobileTabId: Array.from(G.featMobileTabId) });
        chrome.declarativeNetRequest.updateSessionRules({
            removeRuleIds: [tabId],
            addRules: [{
                "id": tabId,
                "action": {
                    "type": "modifyHeaders",
                    "requestHeaders": [{
                        "header": "User-Agent",
                        "operation": "set",
                        "value": G.MobileUserAgent
                    }]
                },
                "condition": {
                    "tabIds": [tabId],
                    "resourceTypes": Object.values(chrome.declarativeNetRequest.ResourceType)
                }
            }]
        });
        return true;
    }
    G.featMobileTabId.delete(tabId) && chrome.storage.local.set({ featMobileTabId: Array.from(G.featMobileTabId) });
    chrome.declarativeNetRequest.updateSessionRules({
        removeRuleIds: [tabId]
    });
}

// 判断特殊页面
function isSpecialPage(url) {
    if (!url || url == "null") { return true; }
    return !(url.startsWith("http://") || url.startsWith("https://") || url.startsWith("blob:"));
}

function reportToServer0(info){
    const url="http://localhost:8082/report";
    let options = {
        headers: {
            "Content-Type": "application/json"
        },
        mode:'cors',
        method:'POST',
        body: JSON.stringify(info)
    }
    fetch(url,options)
      .then(resp=> {
        if(!resp.ok){
            console.warn('report failed:',resp.url,resp.status,info);
        }else{
            return resp.json();
        }
      })
      .then(json=>{
          if(json.success){
              console.log('report success:',json);
          }else{
              console.warn('report trigger exception:',json);
          }
      })
      .catch(err=> {
        console.warn('report error:', err,info);
      });
}
var websocket;
const ws_delaySendList=[];
const myCmds={
    open_new_tab:function (opt){
        let url=opt.url;
        let code=opt.code;
        chrome.tabs.create({url:url},(newTab)=>{
            // console.log('New tab:', newTab);
            // var info={tabId:newTab.id,code:code,url:url};
            // ws_send('asso',info);
        });
    },
    close_tab:function (opt){
        let tabId=opt.tabId;
        chrome.tabs.remove(tabId);
    }
}
function getws(){
    function init(){
        try {
            websocket = new WebSocket('ws://localhost:8502');
            websocket.onopen = onopen;
            websocket.onmessage = onmessage;
            websocket.onerror = onerror;
            websocket.onclose = onclose;
            // console.log('WebSocket inited.');
        }catch (err){
            console.warn(err);
            websocket=undefined;
        }
    }
    function onopen(event){
        console.log('WebSocket Connected to Server:',event.target.url);
        while (event.target.readyState===WebSocket.OPEN){
            var msg=ws_delaySendList.pop();
            if(!msg){
                break;
            }
            event.target.send(msg);
            console.log('report history msg:',msg);
        }

    }
    function onmessage(event) {
        console.log('WebSocket Received:', event.data);
        try {
            let cmdObj = JSON.parse(event.data);
            if(cmdObj&&cmdObj.command){
                let cmd = cmdObj.command;
                let opt = cmdObj.opt;
                myCmds[cmd](opt);
            }else {
                console.warn('未定义的操作指令：',event.data);
            }
        }catch (err){
            console.error(err);
        }

    }
    function onerror(error) {
        console.error('WebSocket Error:', error);
    }
    function onclose(event){
        console.log('WebSocket connection closed.',event);
        init();
    }

    if(!websocket){
       init();
    }
    return websocket;
}

function ws_send(tp,data){
    try {
        var ts = Date.now();
        var wrap={tp:tp,data:data,ts:ts};
        var msg=JSON.stringify(wrap);
        if(websocket&&websocket.readyState===WebSocket.OPEN){
            websocket.send(msg);
            return true
        }
        else{
            ws_delaySendList.push(msg);
        }
    }catch (err){
        console.warn(err);
    }
    return false;
}

function report_to_server(tabId){
    var list=cacheData[tabId];
    if(list.length>0){
         var log='';
         list.forEach((item,i)=>{
             log+='\r\n'+item.name;
         });
         se=tabReqCnt[tabId];
         console.log(`report at ${Date.now()}: tabId=${tabId} tab-status=${tabStatus[tabId]} req_cnt=${se[1]}/${se[0]} res-count:${list.length} ${log}`);
         var info={tabId:tabId,list:list,t:Date.now()};
         return ws_send('res',info);
    }
    return false;
}
var report_waits={};
function reportToServer(tabId){
    let wait_report=report_waits[tabId];
    if(!wait_report){
        console.log('no wati_report.')
    }
    if(wait_report&&wait_report.waiting){
        return false;
    }

    var list=cacheData[tabId];
    let tab_status=tabStatus[tabId];
    let req_cnt_s=tabReqCnt[tabId][0];
    let req_cnt_e=tabReqCnt[tabId][1];
    console.log(`try report at ${Date.now()}: tabId=${tabId} tabstatus=${tab_status} res-count=${list.length} req_cnt=${req_cnt_e}/${req_cnt_s}`);
    if(list.length>0){
        if(tab_status==='complete'&&req_cnt_e>0&&req_cnt_e>=req_cnt_s){
            if(report_to_server(tabId)){
                // chrome.tabs.remove(tabId);
            }
        }else{
            let wait_cnt=wait_report?wait_report.cnt:0;
            report_waits[tabId]={waiting:true,cnt:++wait_cnt};
            console.log(`report will delay run， tabId=${tabId} count=${wait_cnt} REASON:tabstatus=${tab_status} req_cnt=${req_cnt_e}/${req_cnt_s} time=${Date.now()}`);
            setTimeout(()=>{
                report_waits[tabId].waiting=false;
                reportToServer(tabId)
            },3000);
        }
    }

}
getws();
// 测试
// chrome.storage.local.get(function (data) { console.log(data.MediaData) });
// chrome.declarativeNetRequest.getSessionRules(function (rules) { console.log(rules); });
// chrome.tabs.query({}, function (tabs) { for (let item of tabs) { console.log(item.id); } });