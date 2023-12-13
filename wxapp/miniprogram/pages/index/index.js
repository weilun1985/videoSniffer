// index.js
// const app = getApp()
const { envList } = require('../../envList.js');
const { downloadFile, downloadFiles } = require('../../utils')

Page({
    data: {
        id:null
    },
    onLoad:function(options){
        console.log('on load: options='+JSON.stringify(options));
        if(options&&options.id){
            let id=options.id;
            this.setData({id:id});
            this.loadResInfo(id);
        }
    },
    submitResId(){
        var id=this.data.id;
        if(id&&id.length>0){
            console.log('To get res: '+id);
            url= `/pages/index/index?id=${id}`
            console.log(url)
            wx.redirectTo({
                url: url,
            })
        }else{
            console.warn('no id');
        }
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
                }else if(data.res_type==='picture'){
                    for(let i=0;i<data.image.urls.length;i++){
                        let url=data.image.urls[i];
                        if(url.startsWith('http://')){
                            url=url.replace('http://','https://');
                            data.image.urls[i]=url;
                        }
                    }
                }
                this.setData(data);
                // console.dir(data);
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
        if(this.data.video){
            downloadFile('video', this.data.video.url);
        }else if(this.data.image&&this.data.image.urls.length>0){
            downloadFiles('image',this.data.image.urls);
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
    onShareAppMessage() {
        var title=this.data.title;
        var path='/pages/index/index?resid='+this.data.id;
        return {
            title: title,
            path: path,
            imageUrl: 'http://example.com/share.jpg',
            desc: '这是分享备注信息'
        }
    },
    onShareTimeline() {
        return {
            title: '分享到朋友圈标题',
            imageUrl: '/image/share.jpg'
        }
    },
    jumpPage(e) {
        wx.navigateTo({
            url: `/pages/${e.currentTarget.dataset.page}/index?envId=${this.data.selectedEnv.envId}`,
        });
    }
});
