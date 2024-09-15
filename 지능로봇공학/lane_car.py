# -*- coding: utf8 -*-
import struct
import cv2
import numpy as np
import time
import socket
import sys
import random

IP_ADDRESS = '172.30.1.44' # 차량의 CLCD에 출력되는 IP를 입력하세요.
motor_power = 150 #직진시 모터 출력
rotate_motor_power = 50 # 회전시 모터 출력
rotate_motor_stop = int(rotate_motor_power*2/3)
turn_deviation = 50 # 중심점이 이 이상 오차가 발생할 경우 회전
center_coord = 320
traffic_sign_roi = np.array([[(50, 100), (250, 100), (250, 350), (50, 350)]])

def DetectTrafficSign(image):
    src = image

    # 관심 영역 설정
    mask = np.zeros_like(src) #image 파일 배열 초기화, 마스크 파일은 검은색
    cv2.fillPoly(mask, traffic_sign_roi, (255,255,255)) #신호등 관심 영역을 흰색으로 처리, 마스크 파일은 검은 색 배경에 관심영역은 흰색
    src = cv2.bitwise_and(src, mask) #원본파일과 마스크파일을 and 연산하여 원본 파일에 관심영역을 제외한 나머지 영역을 검은 색으로 처리후 src에 저장

    lower_orange = (80, 40, 170) # BGR     #노란색 최대 값을 bgr로 설정
    upper_orange = (150, 130, 255) # BGR   #노란색 최대 값을 bgr로 설정
    img_mask = cv2.inRange(src, lower_orange, upper_orange)   #src 파일에서  lower_orange이상  upper_orange이하의 값이 있다면 그 값을 img_mask에 저장
    src = cv2.bitwise_and(src, src, mask=img_mask)   # src 에 img_mask를 적용하여 관심역역 안의 노란색 값이 나오게 됨
    src = cv2.GaussianBlur(src, ksize=(5, 5), sigmaX=0) #블러 처리
    src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)   #해당 src 영상을 그레이 스케일으로 변환
    _, src = cv2.threshold(src,0,255,cv2.THRESH_BINARY | cv2.THRESH_OTSU) #회색의 SRC에서 0을 임계값으로 해서 그 이상이면 흰색으로 변환. 즉, 노란색 값이 흰색으로 나옴
    #cv2.imshow('traffic2', src)

    circles = cv2.HoughCircles(src, cv2.HOUGH_GRADIENT, 1, 100, param1 = 5, param2 = 5, minRadius = 0, maxRadius = 20)#src 파일에서 원 검출하고 값으로 처리하여 circles에 저장
    src = cv2.cvtColor(src, cv2.COLOR_GRAY2BGR)  #해당 src 영상을 그레이 스케일으로 변환
    cv2.polylines(src,traffic_sign_roi,False,(255,0,255),1) #신호등 영역을 윤곽선으로 그려진 채로 영상에 출력됨
    if ( circles is not None ) :
        for i in circles[0]:  #원 개수 만큼 반복
            cv2.circle(src, (int(i[0]), int(i[1])), int(i[2]), (0, 0, 255), 2) #주황색이 인지 되었지만, 영상에 원 도형이 없다면 신호등 안의 신호의 원을 빨간색으로 그림
    #cv2.imshow('traffic', src)
    if ( circles is not None ) : #주황색인지 되었으면 False 값 반환한다.
        return False
    return True





def DetectLineSlope(image):
    left_power = 0
    right_power = 0
    src = image
#    cv2.imshow('ORIGINAL', image)
    
    # 노이즈 제거를 위한 부드러운 이미지로 변환
    # ksize
    # Using cv2.blur() method 
    ksize = (5, 5)
    image = cv2.blur(src, ksize) 
#    cv2.imshow('BLUR', image)

    # 흑백 이미지로 전환
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #cv2.imshow('GRAY', image)

    cv2.rectangle(image,(0,0),(640,380-20),(0,0,0),-1)
    cv2.rectangle(image,(0,480+20),(640,480),(0,0,0),-1)

    # 외곽선 추출
    image = cv2.Canny(image, 50, 200, None, 3)
    #cv2.imshow('CANNY', image)

    # 관심 영역 설정
    rectangle = np.array([[(0, 480), (100, 380), (540, 380), (640, 480)]])
    mask = np.zeros_like(image)
    cv2.fillPoly(mask, rectangle, 255)
    image = cv2.bitwise_and(image, mask)
   # cv2.imshow('MASKED', image)

    ccan = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    cv2.imshow('img1', ccan)

    line_arr = cv2.HoughLinesP(image, 1, np.pi / 180, 20, minLineLength=10, maxLineGap=10)

    # 중앙을 기준으로 오른쪽, 왼쪽 직선 분리
    line_R = np.empty((0, 5), int)  
    line_L = np.empty((0, 5), int)  

    if line_arr is not None:
        line_arr2 = np.empty((len(line_arr), 5), int)
        for i in range(0, len(line_arr)):
            #시작점의 Y좌표가 큰 좌표(하단)이 되도록 수정
            if line_arr[i][0][1] < line_arr[i][0][3]:
                temp = line_arr[i][0][0], line_arr[i][0][1]
                line_arr[i][0][0], line_arr[i][0][1] = line_arr[i][0][2], line_arr[i][0][3]
                line_arr[i][0][2], line_arr[i][0][3] = temp
           #추출된 선의 좌표에 각도를 추가하여 저장
            l = line_arr[i][0]
            line_arr2[i] = np.append(line_arr[i], np.array((np.arctan2(l[2] - l[0], l[1] - l[3]) * 180) / np.pi))
#            print(l)
            val = (np.arctan2(l[2] - l[0], l[1] - l[3]) * 180) / np.pi
            cv2.line(src, (l[0], l[1]), (l[2], l[3]), (255, random.randint(0,255), random.randint(0,255)), 2, cv2.LINE_AA)
            #중앙을 기준으로 좌우로 분리저장
            if line_arr2[i][0] < center_coord :
                line_L = np.append(line_L, line_arr2[i])
            else :
                line_R = np.append(line_R, line_arr2[i])

    line_L = line_L.reshape(int(len(line_L) / 5), 5)
    line_R = line_R.reshape(int(len(line_R) / 5), 5)

    len_l = len(line_L)
    len_r = len(line_R)
    avg_l = 0
    avg_r = 0
    sum_l = 0
    sum_r = 0
    sum_angle = 0
    avg_angle = 0

    mid_point = -1000
    # 양측차선 인식된 경우 중앙점으로 제어
    if ( len_l != 0 ) & ( len_r != 0 ) :
        #좌측 차선 x 평균값
        for i in range(0,len_l) :
            sum_l = sum_l + line_L[i][0]
        avg_l = sum_l / len(line_L)
        #우측 차선 x 평균값
        for i in range(0,len_r) :
            sum_r = sum_r + line_R[i][0]
        avg_r = sum_r / len(line_R)

        mid_point = ( avg_l + avg_r ) / 2 - center_coord
        if ( mid_point < -turn_deviation ) :
            left_power = rotate_motor_stop
            right_power = rotate_motor_power
#            print("left")
        elif ( mid_point > turn_deviation ) :
            left_power = rotate_motor_power
            right_power = rotate_motor_stop
#            print("right")
        else :
            left_power = motor_power
            right_power = motor_power
#            print("front")
            
    # 한쪽 차선만 인식된 경우 기울기로 제어
    elif ( len_l != 0 ) | ( len_r != 0 ) :

        for i in range(0, len(line_arr)):
            sum_angle = sum_angle + line_arr2[i][4]
        avg_angle = sum_angle / len(line_arr)
        print(avg_angle)
        if ( avg_angle > 0 ) : 
            left_power = rotate_motor_power
            right_power = 0 #-rotate_motor_power
#            print("right")
        else:
            left_power = 0 #-rotate_motor_power
            right_power = rotate_motor_power
#            print("left")
        print(line_arr2[i][4])
    else :
        left_power = 0
        right_power = 0
        print("stop")

    cv2.line(src, (center_coord, rectangle[0][1][1]), (center_coord, rectangle[0][0][1]), (255, 0, 0), 1, cv2.LINE_AA) # 중심선 파란색
    cv2.line(src, (center_coord+turn_deviation, rectangle[0][1][1]), (center_coord+turn_deviation, rectangle[0][0][1]), (0, 0, 255), 1, cv2.LINE_AA) # 회전 경계선 빨간색
    cv2.line(src, (center_coord-turn_deviation, rectangle[0][1][1]), (center_coord-turn_deviation, rectangle[0][0][1]), (0, 0, 255), 1, cv2.LINE_AA) # 회전 경계선 빨간색
    cv2.circle(src,(int(center_coord+mid_point),int(rectangle[0][1][1]/2+rectangle[0][0][1]/2)),5,(0,0,255),-1)
    cv2.polylines(src,rectangle,False,(0,0,255),1)
    cv2.line(src, (rectangle[0][0]), (rectangle[0][3]), (0, 0, 255), 1, cv2.LINE_AA) # 회전 경계선 빨간색
    cv2.polylines(src, traffic_sign_roi, False, (255, 0, 255), 1)
    cv2.line(src, (traffic_sign_roi[0][0]), (traffic_sign_roi[0][3]), (255, 0, 255), 1, cv2.LINE_AA)

    cv2.imshow('view', src)
    return image, left_power, right_power

#esp32 cam과 통신 소켓
client_socket = socket.socket()
client_socket.connect((IP_ADDRESS,2021))

cur_time = 0

while True:
    #초기 신호 2바이트 수신
    id1 = client_socket.recv(1)
    id2 = client_socket.recv(1)

    #수신 신호가 초기 신호가 맞으면
    if ( id1[0] == 20 ) & ( id2[0] == 21 ) :
        #데이타 길이 수신
        length = client_socket.recv(2)
        int_len = int.from_bytes(length,"little")
        jpgdata = bytearray()
        received_len = 0
        
        #데이타 수신(원한는 길이 만큼 수신될때까지)
        while len(jpgdata) < int_len :
            packet = client_socket.recv(int_len - len(jpgdata))
            jpgdata.extend(packet)
        if True:
            if True:
                image = cv2.imdecode(np.frombuffer(jpgdata, dtype=np.uint8), cv2.IMREAD_COLOR)
                #상하 좌우 미러
#                image = cv2.flip(image,0)
#                image = cv2.flip(image,1)

                b = DetectTrafficSign(image)
                a = DetectLineSlope(image)
                image, l, r = a[0], a[1], a[2]

                if (b == False):
                    l = 0
                    r = 0
    
    print(l,r)
    mode = 1
    if mode == 0 :
        if ( time.time() - cur_time) > 0.200 : 
            cur_time = time.time()
            client_socket.send(struct.pack("B",20))
            if ( l > 0 ):
                client_socket.send(struct.pack("B",0))
                client_socket.send(struct.pack("B",l))
            else :
                client_socket.send(struct.pack("B",1))
                client_socket.send(struct.pack("B",-l))
                
            if ( r > 0 ):
                client_socket.send(struct.pack("B",0))
                client_socket.send(struct.pack("B",r))
            else :
                client_socket.send(struct.pack("B",1))
                client_socket.send(struct.pack("B",-r))
            time.sleep(0.1)
            client_socket.send(struct.pack("B",20))
            client_socket.send(struct.pack("B",0))
            client_socket.send(struct.pack("B",0))
            client_socket.send(struct.pack("B",0))
            client_socket.send(struct.pack("B",0))

    if mode == 1 :
        cur_time = time.time()
        client_socket.send(struct.pack("B",20))
        if ( l > 0 ):
            client_socket.send(struct.pack("B",0))
            client_socket.send(struct.pack("B",l))
        else :
            client_socket.send(struct.pack("B",1))
            client_socket.send(struct.pack("B",-l))
            
        if ( r > 0 ):
            client_socket.send(struct.pack("B",0))
            client_socket.send(struct.pack("B",r))
        else :
            client_socket.send(struct.pack("B",1))
            client_socket.send(struct.pack("B",-r))

    key = cv2.waitKey(1)
    if key & 0xFF == ord('q'):
        break