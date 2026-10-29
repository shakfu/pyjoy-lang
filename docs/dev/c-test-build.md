# C Test Build Layout

`pyjoy test --compile` compiles each Joy file into its own directory:

```
build/
  <stem>/
    <stem>.c
    <stem>          (executable; <stem>.exe on Windows)
    Makefile
    joy_runtime.c
    joy_runtime.h
    joy_primitives.c
```
