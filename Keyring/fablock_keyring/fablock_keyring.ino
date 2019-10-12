int i;
int j;
int time = 60*5; //time in seconds until the noise begins

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);

  //blink LED
  for (i = 0; i < time; i++) { 
    digitalWrite(LED_BUILTIN, HIGH);   
    delay(100);                       
    digitalWrite(LED_BUILTIN, LOW); 
    delay(900);
  }

  //noise cycle 10 times
  for(j=0; j < 10; j++){
    for(i=0; i < 3; i++){ 
      //make noise!
      tone(10,4000, 100);
      digitalWrite(LED_BUILTIN, HIGH);   
      delay(100);                       
      digitalWrite(LED_BUILTIN, LOW); 
      delay(900);  
    }
    //pause for 10 seconds with blinking LED
    for (i = 0; i < 10; i++) { 
      digitalWrite(LED_BUILTIN, HIGH);   
      delay(100);                       
      digitalWrite(LED_BUILTIN, LOW); 
      delay(900);
    }
  }
  
}

void loop() {
}
