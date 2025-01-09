#include <thread>
#include <iostream>
#include <vector>
#include <algorithm>
#include <ranges>
#include <concepts>
#include <list>
#include <format>
#include <cmath>
#include <functional>
#include <utility>

using namespace std;

struct coutdln
{
    void operator()(double val)
    {
        cout<<":"<<val<<endl;
    }
};
struct coutiln
{
    void operator()(int val)
    {
        cout<<":"<<val<<endl;
    }
};
struct coutsln
{
    void operator()(std::string val)
    {
        cout<<":"<<val<<endl;
    }
};

void thread_function(std::tuple<int, std::string> t) {
    //std::cout << "Thread is running" << std::endl;
    coutsln()("Thread is running");
    std::cout << "ID: " << std::get<0>(t) << std::endl;
    std::cout << "Name: " << std::get<1>(t) << std::endl;

    coutsln()("test");
    coutsln()("ID1: " + std::to_string(std::get<0>(t)));
    coutsln()("Name1: " + std::get<1>(t));
}

void thread_function2(std::vector<double> t2) {
    std::cout << "Thread is running" << std::endl;
    for (double i = 0; i < t2.size(); i++) {
        cout << t2[i] << endl;
    }
    auto lambda1= [](double v){ return std::pow(v,v);};

    auto vec2 = ranges::views::transform(t2, [](double v){ return v*2; }) 
              | ranges::views::take(3);
    auto vec3 = ranges::views::transform(t2, lambda1) 
              | ranges::views::take(4);
    for (auto val : vec2) {
        cout << "vec2:"<<val << std::endl;
    }
    
    for (auto val : vec3) {
        cout << "vec3:"<<val << std::endl;
        coutdln()(val);
    }

    coutsln()("vec3 printing with foreach");
  //  ranges::for_each(vec3,coutdln());

    auto list = vec3 | std::views::take(3);
    //for_each(vec3.cbegin(),vec3.cend(),[](const auto& v){cout<<"vec3 num : "<<v<<endl;});
    coutsln()("list printing");
    ranges::for_each(list, coutdln());
    


}

int main() {
    std::tuple<int, std::string> t1 = std::make_tuple(1, "Mehul");
    std::thread t(thread_function, std::move(t1));
    t.join();
    

    std::vector<double> vec1 = {1.1, 2.2, 3.3, 4.4, 5.5, 6.6,7.7,8.8,9.9};
    std::thread t2(thread_function2, std::move(vec1));
    
    t2.join();
    return 0;
}   