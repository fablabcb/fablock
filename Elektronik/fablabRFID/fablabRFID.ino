#include <Arduino.h>
#include "A4988.h"

// using a 200-step motor (most common)
// pins used are DIR, STEP, MS1, MS2, MS3 in that order
A4988 stepper(200, 8, 9, 10, 11, 12);
const int buttonPin = 2;
int d = -1;
int OpenEndstop = 0;

void setup() {
    // Set target motor RPM to 1RPM
    stepper.setRPM(150);
    // Set full speed mode (microstepping also works for smoother hand movement
    stepper.setMicrostep(1);
    pinMode(OpenEndstop, INPUT);


}

void loop() {
  OpenEndstop = digitalRead(buttonPin);
  if(OpenEndstop == HIGH){
    stepper.rotate(d*10);
  }else{
    stepper.disable();
    d = d*-1;
    delay(10000);
  }
}
