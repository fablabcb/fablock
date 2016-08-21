#include <Arduino.h>
#include "A4988.h"

// using a 200-step motor (most common)
// pins used are DIR, STEP, MS1, MS2, MS3 in that order
A4988 stepper(200, 8, 9, 10, 11, 12);
const int Locked = 5; // Endstop for the locked position
const int Unlocked = 4; // Endstop for the unlocked position
const int Closed = 7; // Endstop for detecting whether the window 
// is closed or not
int d = -1; // direction of motor rotation


void setup() {
  stepper.disable();
  Serial.begin(9600);
  stepper.setRPM(150);
  // Set full speed mode (microstepping also works for smoother hand movement
  stepper.setMicrostep(1);
  pinMode(Closed, INPUT_PULLUP);
  pinMode(Locked, INPUT_PULLUP);
  pinMode(Unlocked, INPUT_PULLUP);




  // wait for successfull rfid match
    // ...


  
  while(digitalRead(Unlocked) == LOW){
    Serial.println("Opening Window");
    // Open window locking mechanism
    stepper.rotate(-10);
  }//ends when EndStopUnlocked is pressed
  Serial.println("Open reached");

  delay(10000);
  
  while(digitalRead(Locked) == LOW){
    // wait for WindowClosed Endstop to be pressed    
    if(digitalRead(Closed) == HIGH){
      Serial.println("closing");
      // Close window locking mechanism
      stepper.rotate(10);
    }else{
      Serial.println("waiting to close");
    }
      //else{
//      delay(1000);
//      //if cycle is broken by opening the window again it waits 
//      //for WindowClosed to be pressed again
//    }
  }  //don't stop cycle until window is
  //locked
  stepper.disable();
  Serial.println("window closed");  
}

void loop() {

}
