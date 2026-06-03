// #include dependency edges for the component diagram (#include regex on raw_content).
// Local headers need not exist - unresolved includes warn, not error (LNG-05).
#include "local_a.h"
#include "local_b.h"
#include <vector>

struct Holder {
    int size;
};
