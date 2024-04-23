import asyncio
import random
import queue
import time


async def task_to_run(a):
    # 这里是你的协程任务的代码
    print(f"Task {a} is running.")
    # 模拟耗时操作
    random_number = random.randint(1, 10)
    await asyncio.sleep(random_number)
    print(f"Task {a} finished. sleep:{random_number}")

task_queue=queue.Queue()

async def start():
    # 创建一个集合来管理任务
    tasks = set()
    async def wait_tasks():
        if len(tasks)>0:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                tasks.remove(task)

    while True:
        # 动态添加新的任务
        if len(tasks) < 10:  # 假设我们只运行最多5个任务
            a =task_queue.get_nowait() if not task_queue.empty() else None
            if a is not None:
                new_task = asyncio.create_task(task_to_run(a))
                tasks.add(new_task)
                print(f"task {a} added, currently running {len(tasks)} tasks.")
            else:
                await wait_tasks()
            # print(f"task {a} added, currently running {len(tasks)} tasks.")
        else:
            print('await task.')
            await wait_tasks()

        # 如果没有任务在运行，则退出循环
        if not tasks:
            time.sleep(1)

async def start2():
    queue = asyncio.Queue()
    # 定义一个协程函数来处理消息队列中的消息

    async def process_queue():
        while True:
            a = await queue.get()
            await task_to_run(a)
            queue.task_done()

    # 动态增加任务
    async def add_task(a):
        await queue.put(a)
        asyncio.create_task(process_queue())

    # 增加多个任务
    for i in range(10):
        await add_task(i)
    # 等待所有任务完成
    await queue.join()

if __name__ == '__main__':
    for i in range(10):
        task_queue.put(i)
    # 运行事件循环
    asyncio.run(start())
