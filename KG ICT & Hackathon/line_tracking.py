import cv2
import numpy as np
from pymycobot.myagv import MyAgv
import threading
import time
import sys

agv = MyAgv("/dev/ttyAMA2", 115200)     # agv 포트 설정


# np.set_printoptions(threshold=sys.maxsize)

def white(image):        # 하얀색 선 감지(차세대 융합 해커톤 사용)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)


    lower_white = np.array([0, 0, 170])
    upper_white = np.array([180, 50, 255])


    white_mask = cv2.inRange(hsv_image, lower_white, upper_white)


    result = cv2.bitwise_and(image, image, mask=white_mask)
    return white_mask



def red(image):      # 빨간 선 감지(KG ICT 프로젝트 사용)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red = np.array([0, 50, 100], dtype=np.uint8)
    upper_red = np.array([10, 255, 255], dtype=np.uint8)
    red_mask1 = cv2.inRange(hsv, lower_red, upper_red)
    lower_red = np.array([170, 100, 100], dtype=np.uint8)
    upper_red = np.array([180, 255, 255], dtype=np.uint8)
    red_mask2 = cv2.inRange(hsv, lower_red, upper_red)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)


    return red_mask


def yellow(image):       # 노란 선 감지(KG ICT 프로젝트 사용)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([150, 200, 200], dtype=np.uint8)
    upper_yellow = np.array([255, 255, 255], dtype=np.uint8)
    yellow_mask1 = cv2.inRange(image, lower_yellow, upper_yellow)

    lower_yellow = np.array([10, 90, 90], dtype=np.uint8)
    upper_yellow = np.array([120, 210, 210], dtype=np.uint8)
    yellow_mask2 = cv2.inRange(hsv, lower_yellow, upper_yellow)
    lower_yellow = np.array([10, 80, 80], dtype=np.uint8)
    upper_yellow = np.array([50, 255, 255], dtype=np.uint8)
    yellow_mask3 = cv2.inRange(hsv, lower_yellow, upper_yellow)

    yellow_mask = cv2.bitwise_or(yellow_mask1, yellow_mask2)
    yellow_mask = cv2.bitwise_or(yellow_mask, yellow_mask3)

    return yellow_mask


def camera_thread():     # open cv 영상처리 시작
    flag = 0
    history = []
    cap = cv2.VideoCapture(0)

    times = 0

    while cap.isOpened():
        ret, frame = cap.read()
        frame1 = np.copy(frame)
        speed = 1
        times2 = 0.05
        if not ret:
            break

        height, width, channel = frame.shape

        mask0 = np.zeros_like(frame)
        mask1 = np.zeros_like(frame)


        roi_side = np.array([[(0, 250), (width, 250), (width, height), (0, height)]])  #화면 1/3크기의 ROI를 화면에 그림

        cv2.fillPoly(mask1, roi_side, (255, 255, 255))
        # cv2.line(mask0, (width // 2 - 40, height-1), (width // 2 + 40, height-1), (255, 255, 255), 2)
        # cv2.line(mask0, (width // 2 - 40, height), (width // 2 + 40, height), (255, 255, 255), 2)
        cv2.line(mask0, (0, height), (width, height), (255, 255, 255), 2)      #선분 크기의 ROI,너비는 1*640를 화면에 그림
        cv2.line(frame1, (width // 2 - 40, height), (width // 2 + 40, height), (255, 255, 255), 2)  #선분 크기의 ROI,너비는 1*80 화면에 그림

        # mask1[250:,width // 2 - 40:width // 2 + 40,:]=0

        roi_bottom = cv2.bitwise_and(mask0, frame)
        roi_side = cv2.bitwise_and(mask1, frame)



        # red_mask0 = red(roi)           #빨간색 라인 인식
        red_mask123 = red(roi_side)      #빨간색 커브길 인식 혹은 신호등 인식할 때 사용

        #red_mask0 = yellow(roi_bottom)  #노란색 라인 인식
        #red_mask1 = yellow(roi_side)    #노란색 커브길 인식

        red_mask0 = white(roi_bottom)    #하얀색 라인 인식
        red_mask1 = white(roi_side)      #하얀색 커브길 인식

       #라인 인식 함수는 하나의 색에 관한 함수만 적용해야함. 단 신호등 인식을 위해 빨간색 감지 함수를 따로 적용했음


        roi_center = red_mask0[height - 1:, width // 2 - 40:width // 2 + 40][0]    #선분 크기의 ROI(너비 1*80)에 마스크적용

        right = red_mask0[height - 1:, width // 2:width // 2 + 40][0]       #선분 크기의 ROI(너비 1*80)의 중앙선 기준 오른쪽
        left = red_mask0[height - 1:, width // 2 - 40:width // 2][0]        #선분 크기의 ROI(너비 1*80)에 중앙선 기준 왼쪽

        right_out = red_mask0[height - 1:, width // 2 + 41:][0]
        left_out = red_mask0[height - 1:,: width // 2 - 40][0]
        # center = red_mask0[height - 1:, width // 2 - 40:width // 2 + 40][0]

        representative_value = np.sum(roi_center) // roi_center.shape[0]     #선분 크기의 ROI(너비 1*80) 픽셀 값에 평균값 적용
        # curve_right = red_mask1[height - 1:, width // 2 + 40:][0]
        cv2.line(frame1, (width // 2 + 40, height - 1), (width, height), (255, 0, 0), 2)

        #curve_left = red_mask1[height - 1:, :width // 2 - 40][0]



        # print(red_mask0[height:, width // 2 - 40:width // 2 + 40].shape[-1])
        # right_value = np.sum(red_mask0[height-1:, width // 2 + 20:width // 2 + 40] // (red_mask0[height:, width // 2 + 20:width // 2 + 40].shape[-1]))
        # left_value = np.sum(red_mask0[height-1:, width // 2 - 40:width // 2 - 20] // (red_mask0[height:, width // 2 - 40:width // 2 - 20].shape[-1]))


        if 255 in red_mask1:  #커브길 인식시 history 리스트에 저장하는 조건문
            background = np.zeros_like(frame1)
            # background= cv2.bitwise_and(background[:,:,0],red_mask1)

            contours1, _ = cv2.findContours(red_mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            max_contour1 = max(contours1, key=cv2.contourArea)
            cv2.drawContours(background, [max_contour1], -1, (255, 255, 255), thickness=-1)
            back = cv2.resize(background, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
            cv2.imshow("background", back)
            # print(background.shape)
            if len(contours1) >= 1:
                M = cv2.moments(max_contour1)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])

                if 255 in background[:, :, 0][height - 1:, width // 2 - 40:width // 2 + 40][0]:

                    if cx <= width // 2 - 80:
                        print("curve detected. curve center x point:", cx)
                        history.append('l')
                    elif (width // 2) + 80 <= cx:
                        print("curve detected. curve center x point:", int(M["m10"] / M["m00"]))
                        history.append('r')
                    if np.any(red_mask1[250:251, :width][0] == 255) and (width // 2) - 80 <= cx <= width // 2 + 80:
                        history.clear()

                elif np.any(left_out == 255) or np.any(right_out == 255):
                    if (abs(cx - width // 2) >= 400):
                        speed = 35
                        times = 0.2
                        times2=0.1

                        '''if np.any(roi_side_up == 255):
                            speed = 3
                            times = 0.6'''


                    elif (abs(cx - width // 2) >= 290):
                        speed = 25
                        times = 0.15
                        times2 = 0.07
                    elif (abs(cx - width // 2) >= 250):
                        speed = 15
                        times = 0.15

                    elif 180 < abs(cx - width // 2) < 250:
                        speed = 10
                        times = 0.15

                    else:
                        speed = 10
                        times = 0.1


        if len(history) >= 200:
            history = history[50:]

        if 255 in red_mask123 and cv2.countNonZero(red_mask123)>25: #신호등 인식 조건문
            agv.stop()

        elif len(np.argwhere(roi_center == 255)) > 0:
            flag = 0

            if representative_value / 255 > 0.85:
                print("GO")
                print("flag", flag)
                agv.move_control(129, 128, 128)
                time.sleep(0.03)

            elif np.sum(right > 0) > np.sum(left > 0):

                print("LEFT1")
                agv.move_control(128, 128, 127)
                time.sleep(0.02)
                agv.move_control(129, 128, 128)
                time.sleep(0.01)

            elif np.sum(left > 0) > np.sum(right > 0):

                print("RIGHT1")
                agv.move_control(128, 128, 129)
                time.sleep(0.02)
                agv.move_control(129, 128, 128)
                time.sleep(0.01)





        else:    #차량 제어
            # if history.count(history[-1])==max(history.count('l') , history.count('R')):
            if history.count('l') > history.count('R'):
                print("LINE NOT DETECTED TURN RIGHT")
                print("cx", abs(cx - width // 2))
                print(speed)
                print("l,r", history.count('l'), history.count("r"))

                flag = 1

                agv.move_control(128, 128, 128 + speed)
                time.sleep(times)
                agv.move_control(129, 128, 128)
                time.sleep(times)

            elif history.count('r') > history.count('l'):
                print("LINE NOT DETECTED TURN LEFT")

                print("cx",abs(cx - width // 2))

                flag = 1

                agv.move_control(128, 128, 128 - speed)
                time.sleep(times)
                agv.move_control(129, 128, 128)
                time.sleep(times)

            elif np.sum(right_out > 0) > np.sum(left_out > 0):

                print("LEFT")
                agv.move_control(128, 128, 127)
                time.sleep(0.02)
                agv.move_control(129, 128, 128)
                time.sleep(0.01)


            elif np.sum(left_out > 0) > np.sum(right_out > 0):

                print("RIGHT")

                agv.move_control(128, 128, 129)
                time.sleep(0.02)
                agv.move_control(129, 128, 128)
                time.sleep(0.01)

            else:


                print("STOP2")
                print("np.sum(left_out > 0),np.sum(right_out > 0)", np.sum(left_out > 0), np.sum(right_out > 0))
                print(np.any(roi_center == 255))
                agv.stop()

        # print(red_mask0[height:, width // 2:width // 2 +40])
        # print(np.all(red_mask0[height:, width // 2:width // 2 +40] >0))
        half_frame = cv2.resize(frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        cv2.imshow("half_frame", half_frame)
        # cv2.imshow("ORG", frame1)
        # cv2.imshow("mask0", red_mask0)
        cv2.imshow("mask1", red_mask1)
        # print(red_mask0[height - 1:, width // 2 +40:])
        # print("right", np.sum(right>0))
        # print("left",255 in left)
        # print("center",255 in center)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            return 0

    cap.release
    cv2.destroyAllWindows()


if __name__ == "__main__":
    camera_thread = threading.Thread(target=camera_thread)

    camera_thread.start()

    camera_thread.join()
