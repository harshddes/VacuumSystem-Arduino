#pragma once
#include <cstdint>
#define A0 14
#define A1 15
#define A2 16
#define LOW 0
#define HIGH 1
#define OUTPUT 1
#define INPUT_PULLUP 2
#define F(x) x
extern unsigned long fakeTime;
extern int fakeLeds[20];
inline unsigned long millis(){return fakeTime;}
inline void pinMode(uint8_t,int){}
inline void digitalWrite(uint8_t p,int v){fakeLeds[p]=v;}
struct SerialFake {
 void begin(int){}
 template<class T> void print(T){}
 template<class T> void println(T){}
};
extern SerialFake Serial;
