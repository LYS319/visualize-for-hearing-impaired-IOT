//센서 입력의 세기에 대한 THRESHOLD 값
const int AMPLITUDE_THRESHOLD = 150;
//SEN0232 핀 번호 지정
const int SOUND_SENSOR_PIN = A0;
//RGB LED 핀 번호 지정
const int RED_PIN = 9;
const int GREEN_PIN = 10;
const int BLUE_PIN = 11;

//시스템 변수 지정
boolean isIdleState = true;
const int SAMPLING_WINDOW = 10; //샘플링을 받아오는 시간
unsigned long sampleTimer;
int signalMax = 0;
int signalMin = 1023; //sigmalMax~MIN을 계산하여 peak값 측
boolean isSoundPulse = false;
unsigned long lastPulseTime = 0; 
const unsigned long DEBOUNCE_DELAY = 250; /*소리 감지 후 일정 시간동안 감지를 무시하여 중복 입력되는 것을 방지*/

void setup() {
  //시리얼 통신 값 초기화
  Serial.begin(9600);
  Serial1.begin(9600);
  //RGB LED 초기화
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  //시작시 현재 시간 측정
  sampleTimer = millis();
  Serial.println("아두이노: 공통 양극 모드 적용.");
}

void loop() {
  //소리 펄스를 감지하여 라즈베리파이로 전송
  int sample = analogRead(SOUND_SENSOR_PIN);
  /*소리 센서에서 읽어들인 아날로그 신호의 최대값과 최솟값을 사용해 진폭을 계산하기 위한 준비 단계*/
  if (sample < 1023) {
    if (sample > signalMax) signalMax = sample;
    if (sample < signalMin) signalMin = sample;
  }
  //샘플링 시간 확인 및 진폭 계산
  if (millis() - sampleTimer >= SAMPLING_WINDOW) {
    int peakToPeak = signalMax - signalMin;
    //소리 펄스 감지 및 전송
    if (!isSoundPulse && peakToPeak > AMPLITUDE_THRESHOLD && (millis() - lastPulseTime > DEBOUNCE_DELAY)) {
      isSoundPulse = true;
      Serial1.println("PULSE");
      Serial.println("PULSE 신호 전송!");
      lastPulseTime = millis();
    } else if (isSoundPulse && peakToPeak < AMPLITUDE_THRESHOLD) { //펄스 종료 감지 및 다음 측정 준비
      isSoundPulse = false;
    }
    signalMax = 0;
    signalMin = 1023;
    sampleTimer = millis();
  }

  //라즈베리파이로 부터 LED 제어 값 받기
  if (Serial1.available()) {
    String command = Serial1.readStringUntil('\n');
    command.trim();
    if (command.length() > 0) {
      Serial.print("수신된 명령: ");
      Serial.println(command);
      if (command.startsWith("SET_STATE:")) {
        String state = command.substring(10);
        if (state.equals("IDLE")) {
          isIdleState = true;
          Serial.println("==> IDLE 상태 명령 수신");
        } else { // "BUSY"
          isIdleState = false;
          setRgbColor(0, 0, 0);
          Serial.println("==> BUSY 상태 명령 수신");
        }
      } 
      else if (command.startsWith("SET_COLOR:")) {
        isIdleState = false;
        String params = command.substring(10);
        int r = params.substring(0, params.indexOf(',')).toInt();
        int g = params.substring(params.indexOf(',') + 1, params.lastIndexOf(',')).toInt();
        int b = params.substring(params.lastIndexOf(',') + 1).toInt();
        setRgbColor(r, g, b);
        Serial.println("==> 색상 변경 명령 수신");
      }
    }
  }

  // isIdleState 플래그가 true일 때만 숨쉬는 LED 실행
  if (isIdleState) {
    updateIdleLed();
  }
}

//RGB LED 색상을 설정하는 함수(공통 양극)
void setRgbColor(int r, int g, int b) {
  // 값을 반전시켜서 출력 (255 -> 0, 0 -> 255)
  analogWrite(RED_PIN, 255 - r);
  analogWrite(GREEN_PIN, 255 - g);
  analogWrite(BLUE_PIN, 255 - b);
}

//대기 상태일 떄 초록색으로 호흡효과를 줌
void updateIdleLed() {
  float breath = (sin(millis() / 2000.0 * 3.14159) * 0.5 + 0.5) * 255;
  setRgbColor(0, (int)breath, 0);
}
