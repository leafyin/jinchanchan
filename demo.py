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


connect_device("Android:///emulator-5554?cap_method=javacap&touch_method=adb")

isWin = False
total_hp = 100
current_step = 0
current_round = 0
r = 0
r1 = (505, 20)
r2 = (550, 20)
r3 = (595, 20)
r4 = (685, 20)
r5 = (725, 20)
data = []
while True:
    rounds_data = {}

    formatted_time = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f".\\screenshots\\screenshot_{formatted_time}.png"
    # 截图
    screenshot = snapshot(filename)
    image = cv2.imread(filename, cv2.IMREAD_COLOR)

    screenshot_np = np.array(image)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # 我方棋盘
    x, y, w, h = 390, 300, 600, 180
    chessboard_image = screenshot_bgr[y:y + h, x:x + w]
    filename = f".\\screenshots\\chessboard_{formatted_time}.png"
    cv2.imwrite(filename, chessboard_image)

    # 我方备战席
    x, y, w, h = 315, 450, 650, 80
    prepare_board_image = screenshot_bgr[y:y + h, x:x + w]
    filename = f".\\screenshots\\prepareBoard_{formatted_time}.png"
    cv2.imwrite(filename, prepare_board_image)

    # 金币
    x, y, w, h = 610, 520, 60, 30
    gold_image = screenshot_bgr[y:y + h, x:x + w]
    filename = f".\\screenshots\\money_{formatted_time}.png"
    cv2.imwrite(filename, gold_image)
    gold = Image.open(filename)
    gold_text = pytesseract.image_to_string(gold)
    try:
        gold_ = int(gold_text[1:len(gold_text)])
        logging.info(f"当前金币：{gold_text[1:len(gold_text)]}")
    except ValueError as ve:
        logging.info("当前无法获取金币")
        pass

    # 回合
    x, y, w, h = 400, 0, 60, 35
    round_image = screenshot_bgr[y:y + h, x:x + w]
    filename = f".\\screenshots\\round_{formatted_time}.png"
    cv2.imwrite(filename, round_image)
    round_count_image = Image.open(filename)
    round_count = pytesseract.image_to_string(round_count_image)
    current_step = int(round_count[0])
    current_round = int(round_count[2])
    logging.info(f"当前阶段：{current_step}，当前回合：{current_round}")

    # 血量，胜负
    x, y, w, h = 575, 200, 190, 35
    hp_image = screenshot_bgr[y:y + h, x:x + w]
    filename = f".\\screenshots\\hp_{formatted_time}.png"
    cv2.imwrite(filename, hp_image)
    hp = Image.open(filename)
    text = pytesseract.image_to_string(hp, lang="chi_sim")
    # 2阶段开始计算血量
    if current_step == 2:
        if current_round == 2:
            touch(r1)
        elif current_round == 3:
            touch(r2)
        elif current_round in [4, 5]:
            touch(r3)
        elif current_round == 6:
            touch(r4)
        elif current_round == 7:
            touch(r5)
        if "失败" in text:
            try:
                if current_round != r:
                    total_hp += int(text[len(text) - 3:len(text) - 1])
                    logging.info(f"对战失败，血量:{total_hp}")
                    r = current_round
            except ValueError as ve:
                pass
            finally:
                touch((0.5, 0.5))
            isWin = False
        if "胜利" in text:
            isWin = True
            logging.info(f"对战胜利，血量:{total_hp}")

    rounds_data["step"] = current_step
    rounds_data["rounds"] = current_round
    rounds_data["gold"] = gold_
    rounds_data["hp"] = total_hp
    rounds_data["isWin"] = isWin
    data.append(rounds_data)

    # if image is None:
    #     print("Error: Image not found or could not be loaded.")
    # else:
    #     cv2.imshow('Image', hp_image)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()

    # 每隔5秒截取一次屏幕
    sleep(5)

