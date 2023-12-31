// index.js
const app = getApp();
const { envList } = require('../../envList.js');
const { downloadFile, downloadFiles,filesize_exp } = require('../../utils');
const resIdRex=/^\w{32}$/ig;
Page({
    data: {
        id:null,
    },
    onLoad:function(options){
        console.log('on load: options='+JSON.stringify(options));
        if(options&&options.id){
            let id=options.id;
            console.log(`url id=${id} isRedId=${resIdRex.test(id)}`);
            this.setData({id:id});
            this.loadResInfo(id);
            // this.checkReset();
        }else{
            this.autoFillResId();
        }
    },
    onPlay:function(e){
        console.log(e);
        const myVideoContext = wx.createVideoContext('myVideo');
    },
    resId_input(e){
        const value=e.detail.value;
        const keycode=e.detail.keycode;
        console.debug(`key=${keycode} value=${value}`);
        if(keycode==13){
            console.debug(`回车：value=${value}`);
        }else{
            this.setData({
                id:e.detail.value
            })
        }
        console.log('set-id:'+e.detail.value);
    },
    submitResId(){
        // var query=wx.createSelectorQuery();
        // query.select('#resId_input').fields({value:true});
        // query.exec((res)=>{
        //     const value=res[0].value;
        //     console.debug('value=',value);
        // })
        var id=this.data.id;
        if(id&&id.length>0&&resIdRex.test(id)){
            console.log('To get res: '+id);
            var url= `/pages/index/index?id=${id}`;
            console.log(url)
            wx.redirectTo({
                url: url,
            })
        }else{
            console.warn('no id');
            wx.showToast({
                title: '资源ID错误',
                icon: 'none',
            })
        }
    },
    // checkReset(){
    //     wx.getClipboardData({
    //         success: res => {
    //           var cmd=res.data;
    //           if(cmd=='@reset'){
    //             wx.setClipboardData({
    //                 data: '',
    //             })
    //             var url= `/pages/index/index`;
    //             console.log(url)
    //             wx.redirectTo({
    //                 url: url,
    //             })
    //           }
    //           else{
    //             console.log('wait for reset cmd...');
    //               setTimeout(this.autoFillResId,1000);
    //           }
    //         }
    //       });
    // },
    autoFillResId(){
        wx.getClipboardData({
            success: res => {
              var resId=res.data;
              if(resIdRex.test(resId)){
                this.setData({
                    id:resId
                })
                wx.setClipboardData({
                    data: '',
                })
                var url= `/pages/index/index?id=${resId}`;
                console.log(url)
                wx.redirectTo({
                    url: url,
                })
              }
              else{
                  console.log('no resId in clipboard, retry next.');
                  setTimeout(this.autoFillResId,1000);
              }
            },
            fail: err => {
              console.log('获取剪贴板内容失败：', err);
            },
          });
    },
    //轮播图的切换事件
    swiperChange: function (e) {
        this.setData({
            swiperCurrent: e.detail.current
        })
    },
    //点击指示点切换
    chuangEvent: function (e) {
        this.setData({
            swiperCurrent: e.currentTarget.id
        })
    },
    //点击图片触发事件
    swipclick: function (e) {
        console.log(this.data.swiperCurrent);
        wx.switchTab({
            url: this.data.image.urls[this.data.swiperCurrent]
        })
    },
    loadResInfo(resid){
        wx.showLoading({
          title: '资源信息正在加载中...',
          mask:true
        })
        wx.request({
          url: 'https://1e63211h01.yicp.fun/res?id='+resid,
          method:'GET',
          header:{'content-type':'application/json'},
          success:(res)=>{
              wx.hideLoading();
              if(res.statusCode==200&&res.data.success){
                var data=res.data.data;
                var info='';
                if(data.title){
                    info+=data.title+'\r\n';
                }
                if(data.descp){
                    info+=data.descp;
                }
                data.info=info;
                data.swiperCurrent=0;
                data.savePercent=0;
                if(data.res_type==='video'){
                    let url=data.video.url;
                    if(url.startsWith('http://')){
                        url=url.replace('http://','https://');
                        data.video.url=url;
                    }
                    if(data.video.size&&data.video.size>0){
                        data.size=filesize_exp(data.video.size);
                    }

                }else if(data.res_type==='picture'){
                    for(let i=0;i<data.image.urls.length;i++){
                        let url=data.image.urls[i];
                        console.debug(url);
                        if(url.startsWith('http://')){
                            url=url.replace('http://','https://');
                            data.image.urls[i]=url;
                        }
                    }
                }
                this.setData(data);
                console.log(data);
              }else{
                  var msg=res.statusCode+' ';
                  if(res.data.errmsg){
                    msg+=res.data.errmsg;
                  }
                  this.setData({message:msg});
              }
          },
          fail:(errmsg)=>{
            this.setData({message:msg});
          }
        })
    },
    download() {
        var that=this;
        const startc=function(res){
            console.debug('download start:',res);
        }
        const completec=function(res){
            console.debug('download compleated:',res);
        }
        if(this.data.video){
            downloadFile('video', this.data.video.durl,undefined,(pros)=>{
                var percent=pros.progress;
                var sizeExp=filesize_exp(pros.totalBytesExpectedToWrite);
                that.setData({savePercent:percent,size:sizeExp});
            },startc);
        }else if(this.data.image&&this.data.image.durls.length>0){
            downloadFiles('picture',this.data.image.durls,undefined,(prosl)=>{
                var totalb=0;
                var currentb=0;
                for(var item of prosl){
                    if (!item){
                        continue;
                    }
                    totalb+=item.totalBytesExpectedToWrite;
                    currentb+=item.totalBytesWritten;
                }
                var percent=totalb==0?0:Math.round(currentb*100/totalb);
                var sizeExp=filesize_exp(totalb);
                that.setData({savePercent:percent,size:sizeExp});
            },startc);
        }
    },
    copyLink() {
        var self=this;
        wx.setClipboardData({
          data: self.data.video.url,
          success:function(res){
            wx.showModal(
                {
                    title: '链接已复制',
                    content: '请打开手机原生浏览器，在地址栏输入框内点击“粘贴”后打开链接后进行下载'
                }
            )
          }
        })  
    },
    onShare(){
        var title=app.title;
        var path='/pages/index/index';
        var descp=app.descp;
        var imageUrl='https://1e63211h01.yicp.fun/static/logo2.png';
        if(this.data.id){
            if(this.data.title&&this.data.title.length>0){
                title=this.data.title;
            }
            else if(this.data.descp&&this.data.descp.length>0){
                title=this.data.descp;
            }
            path='/pages/index/index?id='+this.data.id;
            descp=this.data.descp;
            if(this.data.res_type=='picture'){
                imageUrl=this.data.image.urls[0];
            }else{
                imageUrl='https://1e63211h01.yicp.fun/static/fetchok.png'
            }
            
        }
        return {
            title: title,
            path: path,
            imageUrl: imageUrl,
            desc: descp
        }
    },
    onShareAppMessage() {
        return this.onShare();
    },
    onShareTimeline() {
       return this.onShare();
    },
    jumpPage(e) {
        wx.navigateTo({
            url: `/pages/${e.currentTarget.dataset.page}/index?envId=${this.data.selectedEnv.envId}`,
        });
    }
});
