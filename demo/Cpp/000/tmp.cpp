#include <stdio.h>

class X {
public:
    X() { printf("hello world!\n"); }
};

int main(int argc, char** argv)
{
    X  x;

    return 0;
}
