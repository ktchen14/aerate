///@ file foo.c

/// This is an ambiguous struct in foo.c with a reference to
/// ambiguous_function()
struct ambiguous_struct {
  int member;
};

/// This is an ambiguous function in foo.c
void ambiguous_function(void) {
}
