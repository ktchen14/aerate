/// @file foo.c

/// This is an ambiguous struct in foo.c with a reference to
/// ambiguous_function()
struct ambiguous_struct {
  int member;
};

/// This is a referrent
void referrent(void) {
}

/// This is another referrent
int referrent(int a) {
  return 0;
}

/// This is an ambiguous function in foo.c with a referrent()
void ambiguous_function(void) {
}
