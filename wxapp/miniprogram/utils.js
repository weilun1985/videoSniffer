const { hex_md5, str_md5 } = require('./md5')

function clear_temps(){
    const mydir=`${wx.env.USER_DATA_PATH}`;
    const fs = wx.getFileSystemManager();
    try{
        let files=fs.readdirSync(mydir);
        files.forEach(item=>{
            var path=`${mydir}/${item}`;
            try{
                fs.unlinkSync(path);
                console.log(`unlink file ok: ${path}`);
            }catch(err){
                console.log(`unlink file fail: ${path} ${err}`);
            }
        });
    }
    catch(err){
        // fs.mkdirSync(mydir,true);
        console.warn(err);
        
    }finally{
        
    }
}
/**
* 下载单个文件
*/
function downloadFile(type, url, completec,progressc,startc) {
    checkAuth(() => {
        // wx.showLoading({
        //     title: '文件下载中...',
        //     mask: true
        // })
    
        clear_temps();
        startc&&startc({type:type,url:url});
        downloadSaveFile(
            type,
            url,
            (path) => {
                wx.hideLoading();
                wx.showToast({
                    title: '下载成功',
                    icon: 'none',
                })
                completec && completec({success:true,path:path});
            },
            (errMsg) => {
                wx.hideLoading();
                wx.showModal({
                    title: errMsg,
                    icon: 'none',
                })
                completec && completec({success:false,errMsg:errMsg});
            },
            (prog)=>{
                progressc&&progressc(prog);
            }
        );
    })
}

/**
* 下载多个文件
*/
function downloadFiles(type, urls, completec,progressc,startc) {
    let success_cnt = 0;
    let fail_cnt = 0;
    let total_cnt = urls.length;
    let errMsgs = [];
    let progressL=new Array(urls.length);

    checkAuth(() => {
        // wx.showLoading({
        //     title: '文件下载中...',
        //     mask: true
        // })
        clear_temps();
        startc&&startc();
        for (let i = 0; i < urls.length; i++) {
            downloadSaveFile(
                type,
                urls[i],
                () => {
                    success_cnt++;
                    if (success_cnt + fail_cnt === total_cnt) {
                        saveCompleted(success_cnt, fail_cnt, completec, errMsgs);
                    }
                },
                (errMsg) => {
                    fail_cnt++;
                    errMsg && errMsgs.push(`${i}${errMsg}`);
                    if (success_cnt + fail_cnt === total_cnt) {
                        saveCompleted(success_cnt, fail_cnt, completec, errMsgs);
                    }
                },
                (prog)=>{
                    progressL[i]=prog;
                    progressc&&progressc(progressL);
                }
            );
        }
    })
}

//保存完成
function saveCompleted(success_cnt, fail_cnt, completec, errMsgs) {
    wx.hideLoading();
    let errMsg = null;
    if (errMsgs.length) {
        errMsg = errMsgs.join('\n');
    }
    var msg=`成功${success_cnt}项`+(fail_cnt>0?`,失败${fail_cnt}项`:'');
    if(fail_cnt>0&&errMsgs){
        msg+=`\r\n失败原因:\n${errMsg}`;
    }
    wx.showModal({
        title: `下载完成`,
        content: msg,
        showCancel: false,
        success(res) {
            if (res.confirm) {
                completec && completec({success_cnt:success_cnt,fail_cnt:fail_cnt,errMsg:errMsg});
            }
        }
    })
}
function getUrlFileName(url){
    let path=url.replace(/(\?.*)$/, '');
    let pathParts=path.split('/');
    let filename=pathParts[pathParts.length - 1];
    return filename;
}
function getUrlExtName(url){
    let filename=getUrlFileName(url);
    if (filename.indexOf('.')==-1){
        return;
    }
    let filenameParts = filename.split('.');
    let ext=filenameParts.pop().toLowerCase();
    return ext;
}
function getMediaType(url){
    let ext=getUrlExtName(url);
    if(!ext){
        return;
    }
    const videos=['mp4','avi','wmv','flv','mov','mkv','webm','3gp'];
    const pictures=['jpg','jpeg','png','gif','bmp','tiff','tif','webp','svg'];
    if(videos.indexOf(ext)!=-1){
        return'video';
    }else if(pictures.indexOf(ext)!=-1){
        return'picture'
    }
}
function timeSeqStr(){
    const now = new Date();
    // 提取年、月、日、时、分、秒
    const year = now.getFullYear();
    const month = ("0" + (now.getMonth() + 1)).slice(-2);
    const day = ("0" + now.getDate()).slice(-2);
    const hours = ("0" + now.getHours()).slice(-2);
    const minutes = ("0" + now.getMinutes()).slice(-2);
    const seconds = ("0" + now.getSeconds()).slice(-2);
    const ms=now.getMilliseconds();
    const formattedTimestamp = `${year}${month}${day}${hours}${minutes}${seconds}_${ms}`;
    return formattedTimestamp;
}

function downloadSaveFile(type, url, successc, failc,progressc) {
    //判断URL的文件类型
    const mediaType=getMediaType(url);
    var ext=getUrlExtName(url);
    if(!ext){
        if(type=='video') 
            ext='mp4';
        else if(type=='picture')
            ext='jpg';
    }
    //const targetName=timeSeqStr()+(ext?`.${ext}`:'');
    const targetName=hex_md5(url)+(ext?`.${ext}`:'');
    console.debug('targetName:',targetName);
    const mydir=`${wx.env.USER_DATA_PATH}`;
    const targetPath=`${mydir}/${targetName}`;
    var dtask=wx.downloadFile({
        url: url,
        filePath:targetPath,
        timeout:600000,
        success:res=>{
            if (res.statusCode === 200) {
                console.log('下载成功:',res);
                if(type=='video'||mediaType=='video'){
                    wx.saveVideoToPhotosAlbum({
                        filePath:targetPath,
                        success:r1=>{
                            console.log('save video to photos album ok: ',r1);
                            successc && successc(r1.savedFilePath);
                        },
                        fail: r1 => {
                            console.warn('save video to photos album fail: ',r1);
                            failc && failc('保存失败:'+r1.errMsg);
                        }
                    });
                }else if(type=='picture'||mediaType=='picture'){
                    wx.saveImageToPhotosAlbum({
                        filePath:targetPath,
                        success:r1=>{
                            console.log('save picture to photos album ok: ',r1);
                            successc && successc(r1.savedFilePath);
                        },
                        fail: r1 => {
                            console.warn('save picture to photos album fail: ',r1);
                            failc && failc('保存失败:'+r1.errMsg);
                        }
                    });
                }else{
                    console.log('非图片视频类文件，保存路径:',targetPath);
                    successc && successc(targetPath);
                    wx.openDocument({
                        filePath: targetPath,
                      });
                }
            }else{
                msg=`下载失败: statusCode=${res.statusCode}`
                console.log(msg);
                failc && failc(msg);
            }

        },
        fail: res => {
            failc && failc('下载失败:'+res.errMsg);
        },
        complete:res=>{}
    })
    dtask.onProgressUpdate(res=>{
        // res.progress;res.totalBytesWritten;res.totalBytesExpectedToWrite;
        progressc&&progressc(res);
    })
}

//下载文件
function downloadSaveFile0(type, url, successc, failc) {
    //判断URL的文件类型
    const mediaType=getMediaType(url);
    var ext=getUrlExtName(url);
    if(!ext){
        if(type=='video') 
            ext='mp4';
        else if(type=='picture')
            ext='jpg';
    }
    const targetName=timeSeqStr()+(ext?`.${ext}`:'');
    console.debug('targetName:',targetName);
    const targetPath=`${wx.env.USER_DATA_PATH}/${targetName}`;
   
    wx.downloadFile({
      url: url,
      filePath:targetPath,
      success:res=>{
        if (res.statusCode === 200) {
            console.debug('download ok:',res);
            var op={
                filePath:res.tempFilePath,
                success: res => {
                    console.debug('op-res: ',res);
                    successc && successc(res.tempFilePath);
                },
                fail: res => {
                    failc && failc('保存失败'+res.errMsg);
                }
            }
            if(mediaType=='video'){
                console.debug('saveVideoToPhotosAlbum: ',res);
                wx.saveVideoToPhotosAlbum(op);
            }else if(mediaType=='picture'){
                console.debug('saveImageToPhotosAlbum: ',res);
                wx.saveImageToPhotosAlbum(op);
            }else{
                console.debug('saveFile: ',res);
                wx.saveFile({
                    filePath:targetPath,
                    tempFilePath:res.tempFilePath,
                    success: res => {
                        console.debug('save file ok: ',res);
                        var op1={
                            filePath: res.savedFilePath,
                            success:r=>{
                              console.debug('resave to photos Album ok:',r);
                              successc && successc(r);
                            },
                            fail:r=>{
                              failc && failc('保存失败'+r.errMsg);
                            }
                          }
                        if(type=='video'){
                            wx.saveVideoToPhotosAlbum(op1)
                        }
                        else if(type=='picture'){
                            wx.saveImageToPhotosAlbum(op1);
                        }else{
                            successc && successc(res.savedFilePath);
                        }
                    },
                    fail: res => {
                        failc && failc('保存失败'+res.errMsg);
                    }
                });
            }
        }else{
            failc && failc('状态码非200');
        }
      },
      fail: res => {
        failc && failc('下载失败:'+res.errMsg);
      },
      complete:res=>{}
    })
}

function checkAuth(gotc){
    wx.getSetting({
        success(res){
            if (res.authSetting['scope.writePhotosAlbum']) {
                // 已经获得授权
                gotc && gotc();
            }else if (res.authSetting['scope.writePhotosAlbum'] === undefined) {
                // 第一次运行，授权未定义，可以直接保存，系统会一次性询问用户权限
                gotc && gotc();
            }else{
                // 用户拒绝授权后，打开设置页可以看到授权提示开关
                wx.openSetting({
                    success(res){
                        if (res.authSetting['scope.writePhotosAlbum']) {  // 用户授权
                            gotc && gotc();
                        }else{ // 用户拒绝授权
                            wx.showToast({
                                title: '权限不足',
                            })
                        }
                    },
                    fail(res){
                        wx.showToast({
                            title: '相册权限设置失败',
                        })
                    }
                })
            }
        },
        fail(res){
            wx.showToast({
                title: '相册权限设置失败,获取设置',
            })
        }
    });
}

//检查权限
function checkAuth0(gotc) {
    //查询权限
    wx.showLoading({
        title: '检查授权情况',
        mask: true
    })
    wx.getSetting({
        success(res) {
            wx.hideLoading();
            if (!res.authSetting['scope.writePhotosAlbum']) {
                //请求授权
                wx.authorize({
                    scope: 'scope.writePhotosAlbum',
                    success() {
                        //获得授权，开始下载
                        gotc && gotc();
                    },
                    fail() {
                        wx.showModal({
                            title: '',
                            content: '保存到系统相册需要授权',
                            confirmText: '授权',
                            success(res) {
                                if (res.confirm) {
                                    wx.openSetting({
                                        success(res) {
                                            if (res.authSetting['scope.writePhotosAlbum'] === true) {
                                                gotc && gotc();
                                            }
                                        }
                                    })
                                }
                            },
                            fail() {
                                wx.showToast({
                                    title: '打开设置页失败',
                                    icon: 'none',
                                })
                            }
                        })
                    }
                })
            } else {
                //已有授权
                gotc && gotc();
            }
        },
        fail() {
            wx.hideLoading();
            wx.showToast({
                title: '获取授权失败',
                icon: 'none',
            })
        }
    })
}
//字节文本表示
function filesize_exp(size){
    if(!size||size==0){
        return '0';
    }
    var file_size_mode = ['B', 'KB', 'MB', 'GB'];
    var file_size_str=`${size}${file_size_mode[0]}`;
    for(var i=1;i<=file_size_mode.length;i++){
        var size1=size/Math.pow(1024,i);
        if(size1<1){
            break;
        }
        size1=size1.toFixed(1);
        file_size_str=`${size1}${file_size_mode[i]}`;
    }
    return file_size_str;
}
module.exports = {
    downloadFile,
    downloadFiles,
    filesize_exp
};