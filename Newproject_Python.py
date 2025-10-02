import serial
import time
import os
import datetime
import json

#아두이노와 블루투스로 연결
SERIAL_PORT = '/dev/rfcomm0'  
BAUD_RATE = 9600

#로직 파라미터
PATTERN_WINDOW_SECONDS = 5.0
COOLDOWN_SECONDS = 5.0

#로깅 디렉터리 설정
LOG_MAIN_DIR = "/home/pi/sound_logs/"
# 파일 경로를 저장할 전역 변수
ai_log_filepath = None
status_log_filepath = None
error_log_filepath = None
# 로그를 메모리에 임시 저장할 리스트
ai_logs = []
status_logs = []
error_logs = []

#시스템 변수 설정
ser = None
current_state = "IDLE"
event_count = 0
state_timer = 0 

#특정 횟수에 맞게 아두이노에 제어 명령 송신신
COMMANDS = {
    "IDLE": "SET_STATE:IDLE",
    "BUSY": "SET_STATE:BUSY",
    1: "SET_COLOR:255,255,255",   # 1회: 흰색
    2: "SET_COLOR:0,255,255",     # 2회: 시안
    3: "SET_COLOR:255,0,0",       # 3회: 빨간색
    4: "SET_COLOR:255,165,0",     # 4회: 주황색
    5: "SET_COLOR:255,255,0",     # 5회: 노란색
    6: "SET_COLOR:255,0,255",     # 6회: 보라색
    7: "SET_COLOR:0,0,255"        # 7회 이상: 파란색
}

def setup_logging():
    """로깅 디렉토리 생성 및 '이번 실행'에 사용할 파일 경로 설정"""
    global ai_log_filepath, status_log_filepath, error_log_filepath
    
    print("로깅 디렉토리 및 파일 경로 설정 중...")
    try:
        ai_dir = os.path.join(LOG_MAIN_DIR, "ai_results")
        status_dir = os.path.join(LOG_MAIN_DIR, "status_logs")
        error_dir = os.path.join(LOG_MAIN_DIR, "error_logs")
        os.makedirs(ai_dir, exist_ok=True)
        os.makedirs(status_dir, exist_ok=True)
        os.makedirs(error_dir, exist_ok=True)

        timestamp_filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ai_log_filepath = os.path.join(ai_dir, f"{timestamp_filename}_ai.json")
        status_log_filepath = os.path.join(status_dir, f"{timestamp_filename}_status.json")
        error_log_filepath = os.path.join(error_dir, f"{timestamp_filename}_error.json")
        
        print("로깅 준비 완료. 저장될 파일:")
        print(f"  - AI 결과: {ai_log_filepath}")
        print(f"  - 시스템 상태: {status_log_filepath}")
        print(f"  - 에러: {error_log_filepath}")

    except Exception as e:
        print(f"!!! 로깅 설정 실패: {e} !!!")

def log_data(log_type, data):
    """데이터를 메모리 리스트에 추가하는 함수"""
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = {'timestamp': timestamp_str, **data} if isinstance(data, dict) else {'timestamp': timestamp_str, 'message': data}
    
    if log_type == "AiResult":
        ai_logs.append(log_entry)
    elif log_type == "SystemStatus":
        status_logs.append(log_entry)
    elif log_type == "Error":
        error_logs.append(log_entry)

def write_logs_to_file():
    """프로그램 종료 시 메모리의 로그를 파일에 저장하는 함수"""
    print("\n프로그램 종료... 로그를 파일에 저장합니다.")
    try:
        if ai_logs and ai_log_filepath:
            with open(ai_log_filepath, "w", encoding='utf-8') as f:
                json.dump(ai_logs, f, indent=4, ensure_ascii=False)
        if status_logs and status_log_filepath:
            with open(status_log_filepath, "w", encoding='utf-8') as f:
                json.dump(status_logs, f, indent=4, ensure_ascii=False)
        if error_logs and error_log_filepath:
            with open(error_log_filepath, "w", encoding='utf-8') as f:
                json.dump(error_logs, f, indent=4, ensure_ascii=False)
        print("로그 저장 완료.")
    except Exception as e:
        print(f"!!! 최종 로그 저장 실패: {e} !!!")

def connect_to_arduino():
    """아두이노 시리얼 포트에 연결을 시도하는 함수"""
    global ser
    while True:
        try:
            print(f"'{SERIAL_PORT}'에 연결 시도 중...")
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            print("연결 성공! 대기 상태로 시작합니다.")
            log_data("SystemStatus", "Connection successful.")
            send_command("IDLE")
            return
        except serial.SerialException as e:
            print(f"연결 실패: {e}. 5초 후 재시도합니다.")
            log_data("Error", f"Connection failed: {e}")
            time.sleep(5)

def send_command(command_key):
    """아두이노로 명령을 전송하는 함수"""
    command = COMMANDS.get(command_key)
    if command and ser:
        try:
            print(f">>> 아두이노에게 명령 전송: {command}")
            ser.write(f"{command}\n".encode('utf-8'))
        except Exception as e:
            print(f"명령 전송 실패: {e}")

def main_loop():
    """메인 루프: 데이터 수신 및 상태 관리"""
    global current_state, event_count, state_timer
    
    received_data = ser.readline().decode('utf-8', errors='ignore').strip()
    
    if current_state == "IDLE":
        if received_data == "PULSE":
            print("PULSE 신호 수신! 패턴 분석을 시작합니다.")
            log_data("SystemStatus", "PULSE received, starting analysis.")
            send_command("BUSY")
            current_state = "LISTENING"
            event_count = 1
            state_timer = time.time()
            print(f"  -> 이벤트 카운트: {event_count}")

    elif current_state == "LISTENING":
        if received_data == "PULSE":
            event_count += 1
            print(f"  -> 이벤트 카운트: {event_count}")
        if time.time() - state_timer > PATTERN_WINDOW_SECONDS:
            print("------------------------------------")
            print(f"분석 종료. 총 이벤트 횟수: {event_count}")
            
            log_content_for_ai = {
                "predicted_class": "Unknown",
                "confidence_score": 0.0,
                "all_probabilities": {f"{i}회 패턴": False for i in range(1, 8)}
            }
            
            result_key = event_count
            if event_count >= 7: result_key = 7

            if result_key > 0:
                predicted_class = f"{result_key}회 패턴"
                confidence_score = 1.0
                if f"{result_key}회 패턴" in log_content_for_ai["all_probabilities"]:
                    log_content_for_ai["all_probabilities"][f"{result_key}회 패턴"] = True
                
                log_content_for_ai["predicted_class"] = predicted_class
                log_content_for_ai["confidence_score"] = confidence_score
                
                print(f"  ==> {event_count}회 패턴 감지!")
                send_command(result_key)
            else:
                log_content_for_ai["predicted_class"] = "No Pattern"
                print("  ==> 유효 패턴 없음.")
            
            log_data("AiResult", log_content_for_ai)
            
            print("결과 표시 및 휴식 시작...")
            current_state = "COOLDOWN"
            state_timer = time.time()

    elif current_state == "COOLDOWN":
        if time.time() - state_timer > COOLDOWN_SECONDS:
            print("------------------------------------")
            print("휴식 종료. 대기 상태로 복귀합니다.")
            log_data("SystemStatus", "Cooldown finished. Returning to IDLE.")
            send_command("IDLE")
            current_state = "IDLE"
        # 휴식 중 들어오는 데이터는 읽어서 버림
        _ = ser.read(ser.in_waiting)
        time.sleep(0.1)

# --- 6. 메인 프로그램 실행 ---
if __name__ == "__main__":
    setup_logging()
    log_data("SystemStatus", "Program started.")
    connect_to_arduino()
    
    try:
        while True:
            main_loop()
    except serial.SerialException as e:
        log_data("Error", f"Serial connection lost: {e}")
        # 이 예제에서는 단순화를 위해 재연결 로직을 메인 루프 밖으로 두었으나,
        # 더 복잡한 애플리케이션에서는 이 부분에서 재연결 함수를 호출할 수 있습니다.
    except KeyboardInterrupt:
        log_data("SystemStatus", "Program terminated by user.")
    except Exception as e:
        log_data("Error", f"An unexpected error occurred: {e}")
    finally:
        # 프로그램이 어떤 이유로든 종료될 때, 모아둔 로그를 파일에 한 번에 저장
        write_logs_to_file()
        if ser and ser.is_open:
            send_command("BUSY")
            ser.close()
        print("프로그램을 종료합니다.")
