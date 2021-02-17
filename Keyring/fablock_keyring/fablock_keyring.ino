#include "LowPower.h"

int i;
int j;
int time = 60*1; //time in seconds until the noise begins
int noiseCycles = 3;
bool muted = false;
bool abgespielt = false;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(A3, INPUT);
  Serial.begin(115200);
  muted = false;
  abgespielt = false;
}

void loop() {
  if(analogRead(A3)<=500){ //if not loading
    Serial.println("In the Zone!");
    abgespielt = false;

    
    // wait cycle
    for (i = 0; i < time; i++) { 
      LowPower.idle(SLEEP_1S, ADC_OFF, TIMER2_OFF, TIMER1_OFF, TIMER0_OFF, SPI_OFF, USART0_OFF, TWI_OFF);
      if(analogRead(A3)>500){
        break;
      }
    }
    
    //noise cycle 10 times
    for(j=1; j <= noiseCycles; j++){
      if(analogRead(A3)>500){
        break;
      }
      for(i=0; i < 3; i++){ 
        //make noise!
        if(!muted) tone(10,4000, 200);
        digitalWrite(LED_BUILTIN, HIGH);   
        delay(100);                       
        digitalWrite(LED_BUILTIN, LOW); 
        delay(900); 
        if(analogRead(A3)>500){
          break;
        } 
      }
      //pause for 10 seconds with blinking LED
      for (i = 0; i < 10; i++) { 
        digitalWrite(LED_BUILTIN, HIGH);   
        delay(100);                       
        digitalWrite(LED_BUILTIN, LOW); 
        delay(900);
        if(analogRead(A3)>500){
          break;
        }
      }
      if(j == noiseCycles){
        muted = true;
      }
    } 
    
  }else{
    if(abgespielt==false){
      tone(10,4000, 600);
      delay(700);
      abgespielt = true;
      muted = false;
    }
    Serial.println("Am Ladekabel");
    LowPower.idle(SLEEP_1S, ADC_OFF, TIMER2_OFF, TIMER1_OFF, TIMER0_OFF, SPI_OFF, USART0_OFF, TWI_OFF);
  }
}
