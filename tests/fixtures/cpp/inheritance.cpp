// Single + multiple inheritance fixture (D-04 class-diagram inherits edges).
struct Shape {
    virtual ~Shape() {}
};

struct Point {
    int x;
    int y;
};

// Single inheritance: Square : public Shape
class Square : public Shape {
public:
    int side;
};

// Multiple inheritance: two CXX_BASE_SPECIFIER children.
class Circle : public Shape, public Point {
public:
    int radius;
};
