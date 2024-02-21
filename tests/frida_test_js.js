
function searchForString(startAddress, size, searchString) {
    const searchStringBytes = Memory.allocUtf8String(searchString);
    const searchStringLength = searchStringBytes.length;

    for (let address = startAddress; address < startAddress + size - searchStringLength; address++) {
        let match = true;
        for (let j = 0; j < searchStringLength; j++) {
            if (Memory.readU8(address + j) !== searchStringBytes[j]) {
                match = false;
                break;
            }
        }

        if (match) {
            console.log('Found string at address:', address);
        }
    }
}
function printStack(){
    // 获取当前线程的堆栈跟踪信息
    var thread = Java.use('java.lang.Thread').currentThread();
    var stackTraceElementArray = thread.getStackTrace();
    // 打印堆栈信息
    var logger=`Call Stack [thread=${thread.getId()}]:`;
    for (var i = 2; i < stackTraceElementArray.length; i++) {
        var element = stackTraceElementArray[i];
        logger+="\n\t" + (i-2 + 1) + ". " + element.getClassName() + "." + element.getMethodName() + " (" + element.getFileName() + ":" + element.getLineNumber() + ")";
    }
    console.log(logger);
}
function exceptWrapper(fn){
    var fn_wrapper=function (...args){
        try{
            return fn.apply(null,args);
        }catch (e){
            console.error(e);
        }
    }
    return fn_wrapper();
}
function printJavaObject(javaObject,deep) {
    var fields=javaObject.class.getDeclaredFields();
    var logger=`class=${javaObject} fields-cnt:${fields.length}`;
    var a=1;
    fields.forEach(function(field) {
        field.setAccessible(true);
        var value = field.get(javaObject);
        logger+=`\n\t${a++}. ${field.getName()} = ${value}}`;

    });
    console.log(logger);
}



function f0(){
    console.log("this is f0...");
    console.log("pageSize:",Memory.pageSize,"pageSizeCount:",Process.pageSizeCount);
    const totalMemory = Memory.pageSize * Process.pageSizeCount;
    console.log('总内存大小：',totalMemory);
    // for (let address = 0; address < totalMemory; address += Memory.pageSize) {
    //     // 读取一页内存
    //     const page = Memory.readByteArray(ptr(address), Memory.pageSize);
    //
    //     // 在这里检查每一页内存中是否包含你想要查找的字符串或其他数据模式
    //     if (searchInPage(page, 'your_string_to_search')) {
    //         console.log('Found string at address:', address);
    //     }
    // }
}
function f1() {
    console.log("this is f1...");
    // 获取要 hook 的类
    try {
        // var CsoLoader = Java.use('com.tencent.cso.CsoLoader'); // 替换为实际的CsoLoader类名
        // if (CsoLoader.initialize) {
        //     CsoLoader.initialize(); // 调用初始化方法
        // } else {
        //     console.log("CsoLoader.initialize not found. Ensure the class and method name are correct.");
        // }
        var targetClass = Java.use('com.tencent.wcdb.database.SQLiteDatabase');
        var targetMethodName="insertWithOnConflict";
        // console.log("targetClass:", targetClass);
        // 获取要 hook 的方法
        var targetMethod = targetClass[targetMethodName];
        // console.log("targetMethod:", targetMethod);
        // 定义新的实现（hook）
        targetMethod.implementation = function (...args) {
            var p0 = args[0];
            if(p0==='message'){
                console.log(`this is: ${targetMethodName}`);
                for(var i=0;i<args.length;i++){
                    var itm=args[i];
                    console.log(`\tp${i}= ${itm.toString()}`);
                }

            }

            // 调用原始的方法
            var result = this[targetMethodName].apply(this,args);

            // 在方法执行后添加自己的逻辑，如：打印结果
            console.log(`method ${targetMethodName} "${p0}" call is: ${result}`);
            if(p0==='message'){
                printStack();
            }
            // 返回原始方法的结果
            return result;
        };
    } catch (e) {
        console.error(e);
    }

}
function f2(){
    console.log("this is f2...");
    var packageName = 'com.tencent.wcdb.database.SQLiteDatabase'; // 替换为你想监控的包名
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.startsWith(packageName)) { // 检查类是否属于目标包
                var clazz = Java.use(className);
                console.log(className);
                // clazz.$methods.forEach(function (method) {
                //     method.implementation = function () {
                //         var stack = Thread.backtrace(this.context, Backtracer.ACCURATE)
                //                      .map(DebugSymbol.fromAddress)
                //                      .join('\n');
                //
                //         console.log("[*] " + className + "." + method.name);
                //         console.log("Call Stack:\n" + stack);
                //
                //         return this[method.name].apply(this, arguments); // 调用原始方法
                //     };
                // });
            }
        },
        onComplete: function() {}
    });
}
function f3(){
    console.log("this is f3...");
    var utils = Java.use("com.tencent.wcdb.database.SQLiteDatabase"); // 类的加载路径
    utils.openDatabase.overload('java.lang.String',
        '[B', 'com.tencent.wcdb.database.SQLiteCipherSpec',
        'com.tencent.wcdb.database.SQLiteDatabase$CursorFactory',
        'int', 'com.tencent.wcdb.DatabaseErrorHandler', 'int')
        .implementation = function(a,b,c,d,e,f,g){
        console.log("Hook start......");
        var JavaString = Java.use("java.lang.String");
        var database = this.openDatabase(a,b,c,d,e,f,g);
        console.log('a=',a);
        console.log('b=',JavaString.$new(b));
        console.log("Hook ending......");
        return database;
    };
}
function f4(){
    console.log("this is f4...");
    var utils = Java.use("com.tencent.wcdb.database.SQLiteDatabase"); // 类的加载路径
    utils.openDatabase
        .overload('java.lang.String',
        '[B', 'com.tencent.wcdb.database.SQLiteCipherSpec',
        'com.tencent.wcdb.database.SQLiteDatabase$CursorFactory',
        'int', 'com.tencent.wcdb.DatabaseErrorHandler', 'int')
        .implementation = function (...args) {
        console.log("Hook start......");
        console.log('a=',args[0]);
        console.log('b=',args[1]);
        console.log("Hook ending......");
        var database = this.openDatabase.apply(this,args);
        return database;
    };
}
function f5(){
    console.log("this is f5...");
     var SQLiteDatabaseClass = Java.use('com.tencent.wcdb.database.SQLiteDatabase');
     var methods=SQLiteDatabaseClass.class.getMethods();
     console.log("methods cnt:",methods.length);
     // 遍历类中所有的公共方法（包括继承的方法）
     methods.forEach(function(method) {
         console.log("method=",method.getName());
        // // 检查是否是实例方法
        // if (method.isInstanceMethod) {
        //     console.log('Hooking method: ' + method.name);
        //
        //     // 创建钩子函数
        //     method.implementation = function(...args) {
        //         console.log('Called method:', method.name);
        //         console.log('Arguments:', args);
        //
        //         // 保留原始方法的调用
        //         var result = this[method.name].apply(this, args);
        //
        //         console.log('Return value:', result);
        //         return result;
        //     };
        // }
    });
}
function f6(){
    console.log("this is f6...");
    var packageName='com.tencent.mm.ui.chatting.'
    // var allClasses = Java.enumerateLoadedClassesSync();
    // console.log('class-cnt:',allClasses.length);
    // allClasses.forEach(function(className) {
    //     if (!className.startsWith(packageName)){
    //         return;
    //     }
    //     console.log(className);
    //     // 获取类对象
    //     // var clazz = Java.use(className);
    //     // 遍历并挂钩所有实例方法
    //     // clazz.class.getDeclaredMethods().forEach(function (method) {
    //     //     if (!method.isConstructor && !method.isStatic) {
    //     //         method.implementation = function (...args) {
    //     //             console.log(`Hooking ${className}.${method.name}`);
    //     //             // 原始方法执行
    //     //             var result = this[method.name].apply(this, args);
    //     //             // 在这里添加你的分析代码
    //     //             return result;
    //     //         };
    //     //     }
    //     // });
    // });
}
const chats_map=new Map();
function f7(){
    console.log("this is f7...");
    var targetClass = Java.use('com.tencent.mm.ui.chatting.v5');
    try {


        // 获取类的构造函数并设置钩子
        var constructor = targetClass.$init;
        if (constructor) {
            console.log("Hooking constructor of " + targetClass.$className);
            // 拦截构造函数并定义新的实现
            constructor.implementation = function (...args) {
                try {
                    console.log(`[+] Constructor called with ${args.length} arguments: `, args);
                    console.log('this='+this);
                    // printStack();
                    // 保存原始构造函数的返回值
                    const result = this.$init(args[0],args[1],args[2]);
                    // 在这里可以添加你自己的逻辑，如记录日志、分析参数等
                    let talker=args[2];
                    chats_map.set(talker,this);
                    return result; // 返回原始构造函数的结果以确保对象正确创建
                }catch (e){
                    console.error(e);
                }
            };
        } else {
            console.log("Constructor not found for class " + targetClass.$className);
        }
    }catch (e){
        console.error(e);
    }

    var targetMethodName="c";
    // 获取要 hook 的方法
    var targetMethod = targetClass[targetMethodName];
    // 定义新的实现（hook）
    targetMethod.implementation = function (...args) {
        console.log(`this is: ${targetMethodName}`);
        for(var i=0;i<args.length;i++){
            var itm=args[i];
            console.log(`\tp${i}= ${itm.toString()}`);
        }

        // 调用原始的方法
        var result = this[targetMethodName].apply(this,args);
        // 在方法执行后添加自己的逻辑，如：打印结果
        // result=this[targetMethodName].apply(this,['this is append...']);
        printJavaObject(this);
        console.log(`method ${targetMethodName} call is: ` + result);
        // printStack();
        console.log("------");
        // 返回原始方法的结果
        return result;
    };
}
function f8(){
    console.log('this is f8...');
    var targetClass = Java.use('com.tencent.mm.ui.LauncherUI');
    var targetMethodName="startChatting";
    var targetMethod = targetClass[targetMethodName];
    targetMethod.implementation = function (...args) {
        console.log(`this is: ${targetMethodName}`);
        for(var i=0;i<args.length;i++){
            var itm=args[i];
            console.log(`\tp${i}= ${itm.toString()}`);
        }
        // printJavaObject(args[1]);
        // 调用原始的方法
        var result = this[targetMethodName].apply(this,args);
        // 在方法执行后添加自己的逻辑，如：打印结果
        // result=this[targetMethodName].apply(this,['this is append...']);

        console.log(`method ${targetMethodName} call is: ` + result);
        printStack();
        // printStack();
        console.log("------");
        // 返回原始方法的结果
        return result;
    };

}
function sendMsg(talker,message){
    if(!chats_map.has(talker)){
        console.warn(`There are no Talker=${talker}`);
        return false;
    }
    var v5=chats_map.get(talker);
    v5['c'](message);
}
function main() {
    Java.perform(f8);
    // Java.perform(f7);
}


setTimeout(main,3000);