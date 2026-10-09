#include <cstdint>
#define A0 14
#define A1 15
#define A2 16
#define LOW 0
#define HIGH 1
#define OUTPUT 1
#define INPUT_PULLUP 2
#define F(x) x
inline unsigned long millis(){return 0;}
inline void pinMode(uint8_t,int){}
inline void digitalWrite(uint8_t,int){}
inline int digitalRead(uint8_t){return HIGH;}
struct SerialStub {
 void begin(int){}
 int availableForWrite(){return 64;}
 template<class T> void print(T){}
 template<class T> void println(T){}
} Serial;
