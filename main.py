import multiprocessing

from wechat_processor import run as wechat_run
from thief_processor import run as thief_run








def start():
    print('start create process...')
    process_list=[]
    process_list.append(multiprocessing.Process(target=thief_run))
    process_list.append(multiprocessing.Process(target=wechat_run))
    for process in process_list:
        process.start()
        print('\t',process.name,process.ident)
    for process in process_list:
        process.join()

    pass



if __name__ == '__main__':
    start()
    pass