import os
import wechat
import pipline



def main():
    wechat.start(pipline.on_msg)
    pass



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        os._exit(1)