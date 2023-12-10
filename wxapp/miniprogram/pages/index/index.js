// index.js
// const app = getApp()
const { envList } = require('../../envList.js');
const { downloadFile, downloadFiles } = require('../../utils')

Page({
    data: {
        //   videoUrl:'https://vd4.bdstatic.com/mda-pjsz90g40y6rt7eh/1080p/cae_h264/1698452902421847957/mda-pjsz90g40y6rt7eh.mp4?pd=-1&pt=1&cr=3&vt=0&cd=0&did=cfcd208495d565ef66e7dff9f98764da&logid=1168090665&vid=11310265590257684878&auth_key=1700639368-0-0-6ef6ba22abdc0ba6b3a3df0aaf6fa9e1&bcevod_channel=searchbox_feed',
        // title: '猫女机器人',
        // descp: '马斯克研发出了猫女机器人，准备量产，服务广大单身男性',
        // video: {
        //     url: 'https://sns-video-bd.xhscdn.com/stream/110/258/01e5594329b536aa010370038be4b08976_258.mp4',
        //     image:'',
        // },
        // image:{
        //     urls:[
        //         'http://sns-webpic-qc.xhscdn.com/202312100041/740a2137025190c1aeff5fb2e4893f97/1040g00830saeo364iq405p0taeg4i536rfbbn88!nd_whgt34_webp_wm_1',
        //         'http://sns-webpic-qc.xhscdn.com/202312100041/e61146a9bba4e93b6e1e6d5ccff65088/1040g00830saeo364iq3g5p0taeg4i5360qgl2f0!nd_whgt34_webp_wm_1',
        //     ],
        // },
        swiperCurrent:0,
        savePercent:0
    },
    onLoad:function(){
        console.log('on load.');
        this.loadResInfo();
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
    loadResInfo(){
        wx.showLoading({
          title: '资源信息正在加载中...',
          mask:true
        })
        wx.request({
          url: 'https://1e63211h01.yicp.fun/res?id=486846d69339a77cf6460b6ce74fe4b4',
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
