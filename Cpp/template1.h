#include <iostream>
#include <functional>
#include <algorithm>
#include <vector>
#include <cmath>
#include <map>
#include <string>

using namespace std;
template <typename T>
void coutln(T val){
    cout<<val<<endl;
}

template <typename... T>
void coutvln(T... args)
{
    string len = "size of args" + std::to_string(sizeof...(args));
    coutln(len);
    
    (..., coutln(args));

    ((cout << args << " "), ...) << endl;
}