import json
import logging
import time
import cv2
import numpy as np
import pytesseract

from PIL import Image
from airtest.core.api import *
from datetime import datetime


# 配置日志设置
logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
    handlers=[
        logging.FileHandler("app.log"),  # 输出到文件
        logging.StreamHandler()  # 输出到控制台
    ]
)


def show_image(image):
    cv2.imshow('Image', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def screenshot_cut(x, y, w, h, bgr, filename: str):
    """
    简单封装一下裁剪图片代码，（x，y，w，h）定义裁剪区域
    :param x: 起始x坐标
    :param y: 起始y坐标
    :param w: 裁剪以x坐标为初始值的宽度，一般向右为正整数，向左为负整数
    :param h: 裁剪以y坐标为初始值的高度，一般向上为负整数，向下为正整数
    :param bgr: 截图转换为 NumPy 的数组
    :param filename: 给裁剪后的截图命名
    :return: 返回裁剪后的图片 Image类型
    """
    cut_image = bgr[y:y + h, x:x + w]
    filename_ = f".\\screenshots\\{filename}.png"
    cv2.imwrite(filename_, cut_image)
    return Image.open(filename_)


def run():
    connect_device("Android:///emulator-5554?cap_method=javacap&touch_method=adb")

    isWin = None
    total_hp = 100
    total_gold = 0
    current_step = 0
    current_round = 0
    r = 0
    # 这五个坐标是一个阶段内五个对战回合，用来查看输赢、失败扣除的血量
    r1 = (505, 20)
    r2 = (550, 20)
    r3 = (595, 20)
    r4 = (685, 20)
    r5 = (725, 20)
    data = []
    while True:
        rounds_data = {}

        formatted_time = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f".\\screenshots\\screenshot.png"
        # 这里调用的是airtest设备屏幕截图
        snapshot(filename)
        image = cv2.imread(filename, cv2.IMREAD_COLOR)

        screenshot_np = np.array(image)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        # 检查点
        x, y, w, h = 580, 590, 120, 40
        out = screenshot_cut(x, y, w, h, screenshot_bgr, "out")
        out_text = pytesseract.image_to_string(out, lang="chi_sim")
        print(out_text)
        if "现在退出" in out_text:
            with open("data.json", "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            break

        # 我方棋盘
        x, y, w, h = 390, 300, 600, 180
        my_chessboard = screenshot_cut(x, y, w, h, screenshot_bgr, "chessboard")

        # 我方备战席
        x, y, w, h = 315, 450, 650, 80
        my_prepareBoard = screenshot_cut(x, y, w, h, screenshot_bgr, "prepareBoard")

        # 回合
        x, y, w, h = 400, 0, 60, 35
        round_count_image = screenshot_cut(x, y, w, h, screenshot_bgr, "round")
        round_count = pytesseract.image_to_string(round_count_image)
        try:
            # 记录当前阶段、回合数
            current_step = int(round_count[0])
            current_round = int(round_count[2])
            logging.info(f"当前阶段：{current_step}，当前回合：{current_round}")
        except IndexError as ie:
            logging.error("1阶段或者在选择海克斯强化")
            continue
        except ValueError as ve:
            continue

        # 2阶段开始计算血量
        if 2 <= current_round != r:
            if current_round == 2:
                touch(r1)
            elif current_round == 3:
                touch(r2)
            elif current_round == 4:
                touch(r3)
            elif current_round == 6:
                touch(r4)
            elif current_round == 7:
                touch(r5)

            # 血量，胜负
            x, y, w, h = 575, 200, 190, 35
            hp = screenshot_cut(x, y, w, h, screenshot_bgr, "hp")
            isWin_text = pytesseract.image_to_string(hp, lang="chi_sim")
            if "失败" in isWin_text:
                try:
                    total_hp += int(isWin_text[len(isWin_text) - 3:len(isWin_text) - 1])
                    logging.info(f"对战失败，血量:{total_hp}")
                    r = current_round
                except ValueError as ve:
                    logging.error(ve)
                finally:
                    touch((0.5, 0.5))
                isWin = False
            elif "胜利" in isWin_text:
                isWin = True
                r = current_round
                logging.info(f"对战胜利，血量:{total_hp}")
            else:
                isWin = None
            # ---
            # 金币
            x, y, w, h = 610, 520, 60, 30
            gold = screenshot_cut(x, y, w, h, screenshot_bgr, "gold")
            gold_text = pytesseract.image_to_string(gold)
            try:
                gold_ = int(gold_text[1:len(gold_text)])
                total_gold = gold_
                logging.info(f"当前金币：{gold_text[1:len(gold_text)]}")
            except ValueError as ve:
                logging.error(ve)

        if isWin is not None:
            rounds_data["step"] = current_step
            rounds_data["rounds"] = current_round
            rounds_data["gold"] = total_gold
            rounds_data["hp"] = total_hp
            rounds_data["isWin"] = isWin
            data.append(rounds_data)

        # 每隔5秒截取一次屏幕
        sleep(5)


run()
