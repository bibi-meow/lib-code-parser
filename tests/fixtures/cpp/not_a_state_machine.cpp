// Looks like an FSM (enum + switch) but maps to NO Python FSM family.
// Downstream state-diagram test asserts ZERO state nodes (negative fixture).
enum class Color { RED, GREEN, BLUE };

int describe(Color c) {
    switch (c) {
        case Color::RED:
            return 1;
        case Color::GREEN:
            return 2;
        case Color::BLUE:
            return 3;
    }
    return 0;
}
