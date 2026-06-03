// Missing #include: parse still builds the cursor tree (LNG-05 warn-not-error).
// The diagnostic for missing_header.h must NOT abort the Ok struct cursor.
#include "missing_header.h"

struct Ok {
    int value;
};
