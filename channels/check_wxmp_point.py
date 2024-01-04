import time
from datetime import datetime
import os
import uiautomation as auto
import pyautogui as autogui


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def open_reswxapp():
    wxapp = auto.PaneControl(searchDepth=1, Name='照片去水印小助手', ClassName='Chrome_WidgetWin_0')
    auto.WaitForExist(wxapp, timeout=2)
    wxapp.SetActive(waitTime=0.1)
    return wxapp

def reswxapp_menu_click(wxapp):
    menuBtn = wxapp.ButtonControl(Name='菜单')
    auto.WaitForExist(menuBtn, timeout=2)
    boundR = menuBtn.BoundingRectangle
    l0, t0, r0, b0 ,w0 ,h0= boundR.left, boundR.top, boundR.right, boundR.bottom,boundR.width(),boundR.height()
    # 分享按钮的坐标
    # l1, t1, r1, b1 = l0 - 242, t0 + 166, r0 - 237, b0 + 216
    # x1, y1 = l1 + 10, t1 + 10
    x1=l0+int(-4.1*w0)+10
    y1=t0+int(3.0*h0)+10
    # 重载按钮的坐标
    # l2, t2, r2, b2 = l0 - 166, t0 + 307, r0 - 160, b0 + 358
    # x2, y2 = l2 + 10, t2 + 10
    x2 = l0+int(-2.8*w0)+10
    y2 = t0+int(5.6*h0)+10
    menuBtn.Click(simulateMove=False)

    # img_path_share = os.path.join(CURRENT_DIR, 'share.png')
    # img_path_reload = os.path.join(CURRENT_DIR, 'reload.png')
    # location_1 = autogui.locateOnScreen(img_path_share)
    # location_2 = autogui.locateOnScreen(img_path_reload)

    print(f'({l0},{t0},{r0},{b0}) [{w0},{h0}]')
    print(f'({x1},{y1})')
    print(f'({x2},{y2})')

    # print(f'({location_1.left},{location_1.top})')
    # print(f'({location_2.left},{location_2.top})')

    return x1,y1,x2,y2


def test_8():
    wxapp=open_reswxapp()
    x1,y1,x2,y2=reswxapp_menu_click(wxapp)
    autogui.moveTo(x2, y2)
    time.sleep(3)
    wxapp.SetActive()
    autogui.moveTo(x1, y1)

if __name__ == '__main__':
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'))
    test_8()
    pass