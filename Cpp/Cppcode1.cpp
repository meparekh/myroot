#include <iostream> 
#include <string>
#include <memory>

using namespace std;
struct A {
  public:
    A(int c=0):a(c)
    {
        cout<<"A::A::"<<a<<endl;
    }
    void f()
    {
        cout <<"A::f"<<endl;
    }
    virtual void f2()
    {
        cout<<"A::f2"<<endl;
    }
    int getMemBase()
    {
        return a;
    }
    private:
    int a;  
};

struct B : A
{
    public:
    B(int c=0) : A(c)
    {
        cout<<"B::B"<<endl;
    }
    void f()
    {
        cout<<"B::f"<<getMemBase()<<endl;
    }
    
};

struct C : A
{
    C(int c=0):A(c)
    {
        cout<<"C::C"<<endl;
    }
      void f2()
      {
        cout<<"C::f2"<<endl;
      }
};

void test(A *pa)
{
    pa->f();
}

int main(){
    struct B b;
    struct A *pa=&b;
    test(pa);
    b.f();
    pa->f2();
    pa = new C(10);
    test(pa);
    std::shared_ptr<A> pa1 = std::make_shared<C>(5);
    test(pa1.get());
    pa1->f2();

    cout<<"hello world  for virtual functions with struct to "<<endl;
    return 0;
}

    
