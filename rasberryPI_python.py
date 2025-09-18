import serial
import time
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import csv
import os

# 한글 폰트 + minus sign 표시 오류 방지
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

# 시리얼 포트 연결
try:
    ser_mega = serial.Serial('/dev/rfcomm0', 9600, timeout=0.1)
    ser_uno = serial.Serial('/dev/rfcomm1', 9600, timeout=1)
    ser_mega.reset_input_buffer()
    print("[INFO] 블루투스 포트 연결 성공")
except serial.SerialException as e:
    print(f"[ERROR] 시리얼 포트 연결 실패: {e}")
    exit()

# 로그 폴더 생성
log_dir = os.path.expanduser('~/log')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"colorZone_log_{time.strftime('%Y%m%d_%H%M%S')}.csv")
log_writer = open(log_file, 'w', newline='')
csv_writer = csv.writer(log_writer)
csv_writer.writerow(['시간', 'ColorZone'])

# 그래프 초기화
x_vals, y_vals = [], []
plt.ion()
fig, ax = plt.subplots()
fig.suptitle("실시간 데시벨 측정 (Color Zone)")
line_plot, = ax.plot([], [], marker='o')
ax.set_ylabel("Color Zone (0~4)")
ax.set_ylim(-0.5, 4.5)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show(block=False)

# 그래프 업데이트 주기 설정 (5개마다 갱신)
update_interval = 5
update_counter = 0

try:
    while True:
        line = ser_mega.readline().decode().strip()

        if not line or not line.isdigit():
            continue

        colorZone = int(line)
        now = datetime.now().strftime('%H:%M:%S')
        print(f"[ColorZone] {colorZone} ({now})")

        x_vals.append(now)
        y_vals.append(colorZone)

        # 로그 기록
        csv_writer.writerow([now, colorZone])
        log_writer.flush()

        # UNO로 전송 (char 한 글자씩 정확히 전송)
        ser_uno.write(bytes([colorZone + ord('0')]))
        ser_uno.flush()

        # 그래프는 일정 주기마다만 갱신
        update_counter += 1
        if update_counter >= update_interval:
            update_counter = 0
            x_plot = x_vals[-50:]
            y_plot = y_vals[-50:]

            line_plot.set_data(range(len(x_plot)), y_plot)
            ax.set_xlim(0, len(x_plot))
            ax.set_xticks(range(len(x_plot))[::5])
            ax.set_xticklabels(x_plot[::5], rotation=45)
            ax.relim()
            ax.autoscale_view()
            plt.pause(0.01)

except KeyboardInterrupt:
    print("\n[INFO] Ctrl+C 감지. 종료 중...")
    ser_mega.close()
    ser_uno.close()
    log_writer.close()
    plt.close()



