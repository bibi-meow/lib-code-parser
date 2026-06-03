// Member-relation spectrum: composes / aggregates / associates / none.
struct Point {
    int x;
    int y;
};

struct Shape {
    int kind;
};

class Diagram {
public:
    Point center;       // value member of known type -> composes
    Shape* parent;      // pointer member of known type -> aggregates
    Point& ref;         // reference member of known type -> aggregates
    int count;          // builtin member -> no edge
    Unknown* widget;    // member of an undeclared/unknown type -> associates
};
