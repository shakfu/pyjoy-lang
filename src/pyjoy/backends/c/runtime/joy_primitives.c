/**
 * joy_primitives.c - Joy primitive operations implemented in C
 */

#include "joy_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* Helper macros */
#define REQUIRE(n, op) \
    if (ctx->stack->depth < (n)) joy_error_underflow(op, n, ctx->stack->depth)

#define POP() joy_stack_pop(ctx->stack)
#define PUSH(v) joy_stack_push(ctx->stack, v)
#define PEEK() joy_stack_peek(ctx->stack)
#define PEEK_N(n) joy_stack_peek_n(ctx->stack, n)

#define EXPECT_TYPE(v, t, op) \
    if ((v).type != (t)) joy_error_type(op, #t, (v).type)

/* ---------- Stack Operations ---------- */

static void prim_dup(JoyContext* ctx) {
    REQUIRE(1, "dup");
    joy_stack_dup(ctx->stack);
}

static void prim_pop(JoyContext* ctx) {
    REQUIRE(1, "pop");
    JoyValue v = POP();
    joy_value_free(&v);
}

static void prim_swap(JoyContext* ctx) {
    REQUIRE(2, "swap");
    joy_stack_swap(ctx->stack);
}

static void prim_rollup(JoyContext* ctx) {
    REQUIRE(3, "rollup");
    JoyValue z = POP();
    JoyValue y = POP();
    JoyValue x = POP();
    PUSH(y);
    PUSH(z);
    PUSH(x);
}

static void prim_rolldown(JoyContext* ctx) {
    REQUIRE(3, "rolldown");
    JoyValue z = POP();
    JoyValue y = POP();
    JoyValue x = POP();
    PUSH(z);
    PUSH(x);
    PUSH(y);
}

static void prim_rotate(JoyContext* ctx) {
    REQUIRE(3, "rotate");
    JoyValue z = POP();
    JoyValue y = POP();
    JoyValue x = POP();
    PUSH(z);
    PUSH(y);
    PUSH(x);
}

static void prim_dupd(JoyContext* ctx) {
    REQUIRE(2, "dupd");
    JoyValue y = POP();
    joy_stack_dup(ctx->stack);
    PUSH(y);
}

static void prim_swapd(JoyContext* ctx) {
    REQUIRE(3, "swapd");
    JoyValue z = POP();
    joy_stack_swap(ctx->stack);
    PUSH(z);
}

static void prim_popd(JoyContext* ctx) {
    REQUIRE(2, "popd");
    JoyValue y = POP();
    JoyValue x = POP();
    joy_value_free(&x);
    PUSH(y);
}

static void prim_stack(JoyContext* ctx) {
    JoyValue list = joy_list_empty();
    for (size_t i = ctx->stack->depth; i > 0; i--) {
        joy_list_push(list.data.list, joy_value_copy(ctx->stack->items[i-1]));
    }
    PUSH(list);
}

static void prim_unstack(JoyContext* ctx) {
    REQUIRE(1, "unstack");
    JoyValue v = POP();
    EXPECT_TYPE(v, JOY_LIST, "unstack");
    joy_stack_clear(ctx->stack);
    for (size_t i = v.data.list->length; i > 0; i--) {
        PUSH(joy_value_copy(v.data.list->items[i-1]));
    }
    joy_value_free(&v);
}

/* ---------- Arithmetic Operations ---------- */

static void prim_add(JoyContext* ctx) {
    REQUIRE(2, "+");
    JoyValue b = POP();
    JoyValue a = POP();

    if (a.type == JOY_INTEGER && b.type == JOY_INTEGER) {
        PUSH(joy_integer(a.data.integer + b.data.integer));
    } else if (a.type == JOY_FLOAT || b.type == JOY_FLOAT) {
        double av = a.type == JOY_FLOAT ? a.data.floating : (double)a.data.integer;
        double bv = b.type == JOY_FLOAT ? b.data.floating : (double)b.data.integer;
        PUSH(joy_float(av + bv));
    } else {
        joy_error_type("+", "number", a.type);
    }
}

static void prim_sub(JoyContext* ctx) {
    REQUIRE(2, "-");
    JoyValue b = POP();
    JoyValue a = POP();

    if (a.type == JOY_INTEGER && b.type == JOY_INTEGER) {
        PUSH(joy_integer(a.data.integer - b.data.integer));
    } else if (a.type == JOY_FLOAT || b.type == JOY_FLOAT) {
        double av = a.type == JOY_FLOAT ? a.data.floating : (double)a.data.integer;
        double bv = b.type == JOY_FLOAT ? b.data.floating : (double)b.data.integer;
        PUSH(joy_float(av - bv));
    } else {
        joy_error_type("-", "number", a.type);
    }
}

static void prim_mul(JoyContext* ctx) {
    REQUIRE(2, "*");
    JoyValue b = POP();
    JoyValue a = POP();

    if (a.type == JOY_INTEGER && b.type == JOY_INTEGER) {
        PUSH(joy_integer(a.data.integer * b.data.integer));
    } else if (a.type == JOY_FLOAT || b.type == JOY_FLOAT) {
        double av = a.type == JOY_FLOAT ? a.data.floating : (double)a.data.integer;
        double bv = b.type == JOY_FLOAT ? b.data.floating : (double)b.data.integer;
        PUSH(joy_float(av * bv));
    } else {
        joy_error_type("*", "number", a.type);
    }
}

static void prim_div(JoyContext* ctx) {
    REQUIRE(2, "/");
    JoyValue b = POP();
    JoyValue a = POP();

    if (a.type == JOY_INTEGER && b.type == JOY_INTEGER) {
        if (b.data.integer == 0) joy_error("Division by zero");
        PUSH(joy_integer(a.data.integer / b.data.integer));
    } else if (a.type == JOY_FLOAT || b.type == JOY_FLOAT) {
        double av = a.type == JOY_FLOAT ? a.data.floating : (double)a.data.integer;
        double bv = b.type == JOY_FLOAT ? b.data.floating : (double)b.data.integer;
        if (bv == 0.0) joy_error("Division by zero");
        PUSH(joy_float(av / bv));
    } else {
        joy_error_type("/", "number", a.type);
    }
}

static void prim_rem(JoyContext* ctx) {
    REQUIRE(2, "rem");
    JoyValue b = POP();
    JoyValue a = POP();
    EXPECT_TYPE(a, JOY_INTEGER, "rem");
    EXPECT_TYPE(b, JOY_INTEGER, "rem");
    if (b.data.integer == 0) joy_error("Division by zero");
    PUSH(joy_integer(a.data.integer % b.data.integer));
}

static void prim_succ(JoyContext* ctx) {
    REQUIRE(1, "succ");
    JoyValue v = POP();
    EXPECT_TYPE(v, JOY_INTEGER, "succ");
    PUSH(joy_integer(v.data.integer + 1));
}

static void prim_pred(JoyContext* ctx) {
    REQUIRE(1, "pred");
    JoyValue v = POP();
    EXPECT_TYPE(v, JOY_INTEGER, "pred");
    PUSH(joy_integer(v.data.integer - 1));
}

static void prim_abs(JoyContext* ctx) {
    REQUIRE(1, "abs");
    JoyValue v = POP();
    if (v.type == JOY_INTEGER) {
        PUSH(joy_integer(v.data.integer < 0 ? -v.data.integer : v.data.integer));
    } else if (v.type == JOY_FLOAT) {
        PUSH(joy_float(fabs(v.data.floating)));
    } else {
        joy_error_type("abs", "number", v.type);
    }
}

static void prim_neg(JoyContext* ctx) {
    REQUIRE(1, "neg");
    JoyValue v = POP();
    if (v.type == JOY_INTEGER) {
        PUSH(joy_integer(-v.data.integer));
    } else if (v.type == JOY_FLOAT) {
        PUSH(joy_float(-v.data.floating));
    } else {
        joy_error_type("neg", "number", v.type);
    }
}

static void prim_sign(JoyContext* ctx) {
    REQUIRE(1, "sign");
    JoyValue v = POP();
    if (v.type == JOY_INTEGER) {
        int64_t s = v.data.integer > 0 ? 1 : (v.data.integer < 0 ? -1 : 0);
        PUSH(joy_integer(s));
    } else if (v.type == JOY_FLOAT) {
        int s = v.data.floating > 0 ? 1 : (v.data.floating < 0 ? -1 : 0);
        PUSH(joy_integer(s));
    } else {
        joy_error_type("sign", "number", v.type);
    }
}

static void prim_max(JoyContext* ctx) {
    REQUIRE(2, "max");
    JoyValue b = POP();
    JoyValue a = POP();
    if (a.type == JOY_INTEGER && b.type == JOY_INTEGER) {
        PUSH(joy_integer(a.data.integer > b.data.integer ? a.data.integer : b.data.integer));
    } else if (a.type == JOY_FLOAT || b.type == JOY_FLOAT) {
        double av = a.type == JOY_FLOAT ? a.data.floating : (double)a.data.integer;
        double bv = b.type == JOY_FLOAT ? b.data.floating : (double)b.data.integer;
        PUSH(joy_float(av > bv ? av : bv));
    } else {
        joy_error_type("max", "number", a.type);
    }
}

static void prim_min(JoyContext* ctx) {
    REQUIRE(2, "min");
    JoyValue b = POP();
    JoyValue a = POP();
    if (a.type == JOY_INTEGER && b.type == JOY_INTEGER) {
        PUSH(joy_integer(a.data.integer < b.data.integer ? a.data.integer : b.data.integer));
    } else if (a.type == JOY_FLOAT || b.type == JOY_FLOAT) {
        double av = a.type == JOY_FLOAT ? a.data.floating : (double)a.data.integer;
        double bv = b.type == JOY_FLOAT ? b.data.floating : (double)b.data.integer;
        PUSH(joy_float(av < bv ? av : bv));
    } else {
        joy_error_type("min", "number", a.type);
    }
}

/* ---------- Math Functions ---------- */

static void prim_sin(JoyContext* ctx) {
    REQUIRE(1, "sin");
    JoyValue v = POP();
    double x = v.type == JOY_FLOAT ? v.data.floating : (double)v.data.integer;
    PUSH(joy_float(sin(x)));
}

static void prim_cos(JoyContext* ctx) {
    REQUIRE(1, "cos");
    JoyValue v = POP();
    double x = v.type == JOY_FLOAT ? v.data.floating : (double)v.data.integer;
    PUSH(joy_float(cos(x)));
}

static void prim_tan(JoyContext* ctx) {
    REQUIRE(1, "tan");
    JoyValue v = POP();
    double x = v.type == JOY_FLOAT ? v.data.floating : (double)v.data.integer;
    PUSH(joy_float(tan(x)));
}

static void prim_sqrt(JoyContext* ctx) {
    REQUIRE(1, "sqrt");
    JoyValue v = POP();
    double x = v.type == JOY_FLOAT ? v.data.floating : (double)v.data.integer;
    PUSH(joy_float(sqrt(x)));
}

static void prim_exp(JoyContext* ctx) {
    REQUIRE(1, "exp");
    JoyValue v = POP();
    double x = v.type == JOY_FLOAT ? v.data.floating : (double)v.data.integer;
    PUSH(joy_float(exp(x)));
}

static void prim_log(JoyContext* ctx) {
    REQUIRE(1, "log");
    JoyValue v = POP();
    double x = v.type == JOY_FLOAT ? v.data.floating : (double)v.data.integer;
    PUSH(joy_float(log(x)));
}

static void prim_pow(JoyContext* ctx) {
    REQUIRE(2, "pow");
    JoyValue b = POP();
    JoyValue a = POP();
    double av = a.type == JOY_FLOAT ? a.data.floating : (double)a.data.integer;
    double bv = b.type == JOY_FLOAT ? b.data.floating : (double)b.data.integer;
    PUSH(joy_float(pow(av, bv)));
}

static void prim_floor(JoyContext* ctx) {
    REQUIRE(1, "floor");
    JoyValue v = POP();
    double x = v.type == JOY_FLOAT ? v.data.floating : (double)v.data.integer;
    PUSH(joy_integer((int64_t)floor(x)));
}

static void prim_ceil(JoyContext* ctx) {
    REQUIRE(1, "ceil");
    JoyValue v = POP();
    double x = v.type == JOY_FLOAT ? v.data.floating : (double)v.data.integer;
    PUSH(joy_integer((int64_t)ceil(x)));
}

static void prim_trunc(JoyContext* ctx) {
    REQUIRE(1, "trunc");
    JoyValue v = POP();
    double x = v.type == JOY_FLOAT ? v.data.floating : (double)v.data.integer;
    PUSH(joy_integer((int64_t)trunc(x)));
}

/* ---------- Comparison Operations ---------- */

static void prim_eq(JoyContext* ctx) {
    REQUIRE(2, "=");
    JoyValue b = POP();
    JoyValue a = POP();
    PUSH(joy_boolean(joy_value_equal(a, b)));
    joy_value_free(&a);
    joy_value_free(&b);
}

static void prim_neq(JoyContext* ctx) {
    REQUIRE(2, "!=");
    JoyValue b = POP();
    JoyValue a = POP();
    PUSH(joy_boolean(!joy_value_equal(a, b)));
    joy_value_free(&a);
    joy_value_free(&b);
}

static void prim_lt(JoyContext* ctx) {
    REQUIRE(2, "<");
    JoyValue b = POP();
    JoyValue a = POP();
    bool result = false;
    if (a.type == JOY_INTEGER && b.type == JOY_INTEGER) {
        result = a.data.integer < b.data.integer;
    } else if (a.type == JOY_FLOAT || b.type == JOY_FLOAT) {
        double av = a.type == JOY_FLOAT ? a.data.floating : (double)a.data.integer;
        double bv = b.type == JOY_FLOAT ? b.data.floating : (double)b.data.integer;
        result = av < bv;
    } else if (a.type == JOY_CHAR && b.type == JOY_CHAR) {
        result = a.data.character < b.data.character;
    } else if (a.type == JOY_STRING && b.type == JOY_STRING) {
        result = strcmp(a.data.string, b.data.string) < 0;
    }
    PUSH(joy_boolean(result));
    joy_value_free(&a);
    joy_value_free(&b);
}

static void prim_gt(JoyContext* ctx) {
    REQUIRE(2, ">");
    JoyValue b = POP();
    JoyValue a = POP();
    bool result = false;
    if (a.type == JOY_INTEGER && b.type == JOY_INTEGER) {
        result = a.data.integer > b.data.integer;
    } else if (a.type == JOY_FLOAT || b.type == JOY_FLOAT) {
        double av = a.type == JOY_FLOAT ? a.data.floating : (double)a.data.integer;
        double bv = b.type == JOY_FLOAT ? b.data.floating : (double)b.data.integer;
        result = av > bv;
    } else if (a.type == JOY_CHAR && b.type == JOY_CHAR) {
        result = a.data.character > b.data.character;
    } else if (a.type == JOY_STRING && b.type == JOY_STRING) {
        result = strcmp(a.data.string, b.data.string) > 0;
    }
    PUSH(joy_boolean(result));
    joy_value_free(&a);
    joy_value_free(&b);
}

static void prim_le(JoyContext* ctx) {
    REQUIRE(2, "<=");
    JoyValue b = POP();
    JoyValue a = POP();
    bool result = false;
    if (a.type == JOY_INTEGER && b.type == JOY_INTEGER) {
        result = a.data.integer <= b.data.integer;
    } else if (a.type == JOY_FLOAT || b.type == JOY_FLOAT) {
        double av = a.type == JOY_FLOAT ? a.data.floating : (double)a.data.integer;
        double bv = b.type == JOY_FLOAT ? b.data.floating : (double)b.data.integer;
        result = av <= bv;
    }
    PUSH(joy_boolean(result));
    joy_value_free(&a);
    joy_value_free(&b);
}

static void prim_ge(JoyContext* ctx) {
    REQUIRE(2, ">=");
    JoyValue b = POP();
    JoyValue a = POP();
    bool result = false;
    if (a.type == JOY_INTEGER && b.type == JOY_INTEGER) {
        result = a.data.integer >= b.data.integer;
    } else if (a.type == JOY_FLOAT || b.type == JOY_FLOAT) {
        double av = a.type == JOY_FLOAT ? a.data.floating : (double)a.data.integer;
        double bv = b.type == JOY_FLOAT ? b.data.floating : (double)b.data.integer;
        result = av >= bv;
    }
    PUSH(joy_boolean(result));
    joy_value_free(&a);
    joy_value_free(&b);
}

/* ---------- Logical Operations ---------- */

static void prim_and(JoyContext* ctx) {
    REQUIRE(2, "and");
    JoyValue b = POP();
    JoyValue a = POP();
    PUSH(joy_boolean(joy_value_truthy(a) && joy_value_truthy(b)));
    joy_value_free(&a);
    joy_value_free(&b);
}

static void prim_or(JoyContext* ctx) {
    REQUIRE(2, "or");
    JoyValue b = POP();
    JoyValue a = POP();
    PUSH(joy_boolean(joy_value_truthy(a) || joy_value_truthy(b)));
    joy_value_free(&a);
    joy_value_free(&b);
}

static void prim_not(JoyContext* ctx) {
    REQUIRE(1, "not");
    JoyValue v = POP();
    PUSH(joy_boolean(!joy_value_truthy(v)));
    joy_value_free(&v);
}

/* ---------- List/Aggregate Operations ---------- */

static void prim_first(JoyContext* ctx) {
    REQUIRE(1, "first");
    JoyValue v = POP();
    if (v.type == JOY_LIST) {
        if (v.data.list->length == 0) joy_error("first of empty list");
        PUSH(joy_value_copy(v.data.list->items[0]));
    } else if (v.type == JOY_QUOTATION) {
        if (v.data.quotation->length == 0) joy_error("first of empty quotation");
        PUSH(joy_value_copy(v.data.quotation->terms[0]));
    } else if (v.type == JOY_STRING) {
        if (v.data.string[0] == '\0') joy_error("first of empty string");
        PUSH(joy_char(v.data.string[0]));
    } else {
        joy_error_type("first", "aggregate", v.type);
    }
    joy_value_free(&v);
}

static void prim_rest(JoyContext* ctx) {
    REQUIRE(1, "rest");
    JoyValue v = POP();
    if (v.type == JOY_LIST) {
        JoyList* rest = joy_list_rest(v.data.list);
        JoyValue result = {.type = JOY_LIST, .data.list = rest};
        PUSH(result);
    } else if (v.type == JOY_QUOTATION) {
        JoyQuotation* rest = joy_quotation_new(v.data.quotation->length);
        for (size_t i = 1; i < v.data.quotation->length; i++) {
            joy_quotation_push(rest, joy_value_copy(v.data.quotation->terms[i]));
        }
        JoyValue result = {.type = JOY_QUOTATION, .data.quotation = rest};
        PUSH(result);
    } else if (v.type == JOY_STRING) {
        PUSH(joy_string(v.data.string + 1));
    } else {
        joy_error_type("rest", "aggregate", v.type);
    }
    joy_value_free(&v);
}

static void prim_cons(JoyContext* ctx) {
    REQUIRE(2, "cons");
    JoyValue agg = POP();
    JoyValue item = POP();
    if (agg.type == JOY_LIST) {
        JoyList* result = joy_list_cons(item, agg.data.list);
        joy_value_free(&item);
        joy_value_free(&agg);
        JoyValue v = {.type = JOY_LIST, .data.list = result};
        PUSH(v);
    } else if (agg.type == JOY_QUOTATION) {
        JoyQuotation* result = joy_quotation_new(agg.data.quotation->length + 1);
        joy_quotation_push(result, joy_value_copy(item));
        for (size_t i = 0; i < agg.data.quotation->length; i++) {
            joy_quotation_push(result, joy_value_copy(agg.data.quotation->terms[i]));
        }
        joy_value_free(&item);
        joy_value_free(&agg);
        JoyValue v = {.type = JOY_QUOTATION, .data.quotation = result};
        PUSH(v);
    } else {
        joy_error_type("cons", "aggregate", agg.type);
    }
}

static void prim_swons(JoyContext* ctx) {
    REQUIRE(2, "swons");
    joy_stack_swap(ctx->stack);
    prim_cons(ctx);
}

static void prim_uncons(JoyContext* ctx) {
    REQUIRE(1, "uncons");
    JoyValue v = POP();
    if (v.type == JOY_LIST) {
        if (v.data.list->length == 0) joy_error("uncons of empty list");
        JoyValue first = joy_value_copy(v.data.list->items[0]);
        JoyList* rest = joy_list_rest(v.data.list);
        joy_value_free(&v);
        PUSH(first);
        JoyValue rv = {.type = JOY_LIST, .data.list = rest};
        PUSH(rv);
    } else if (v.type == JOY_QUOTATION) {
        if (v.data.quotation->length == 0) joy_error("uncons of empty quotation");
        JoyValue first = joy_value_copy(v.data.quotation->terms[0]);
        JoyQuotation* rest = joy_quotation_new(v.data.quotation->length);
        for (size_t i = 1; i < v.data.quotation->length; i++) {
            joy_quotation_push(rest, joy_value_copy(v.data.quotation->terms[i]));
        }
        joy_value_free(&v);
        PUSH(first);
        JoyValue rv = {.type = JOY_QUOTATION, .data.quotation = rest};
        PUSH(rv);
    } else {
        joy_error_type("uncons", "aggregate", v.type);
    }
}

static void prim_concat(JoyContext* ctx) {
    REQUIRE(2, "concat");
    JoyValue b = POP();
    JoyValue a = POP();
    if (a.type == JOY_LIST && b.type == JOY_LIST) {
        JoyList* result = joy_list_concat(a.data.list, b.data.list);
        joy_value_free(&a);
        joy_value_free(&b);
        JoyValue v = {.type = JOY_LIST, .data.list = result};
        PUSH(v);
    } else if (a.type == JOY_QUOTATION && b.type == JOY_QUOTATION) {
        JoyQuotation* result = joy_quotation_concat(a.data.quotation, b.data.quotation);
        joy_value_free(&a);
        joy_value_free(&b);
        JoyValue v = {.type = JOY_QUOTATION, .data.quotation = result};
        PUSH(v);
    } else if (a.type == JOY_STRING && b.type == JOY_STRING) {
        size_t len = strlen(a.data.string) + strlen(b.data.string) + 1;
        char* result = malloc(len);
        strcpy(result, a.data.string);
        strcat(result, b.data.string);
        joy_value_free(&a);
        joy_value_free(&b);
        PUSH(joy_string_owned(result));
    } else {
        joy_error_type("concat", "aggregate", a.type);
    }
}

static void prim_size(JoyContext* ctx) {
    REQUIRE(1, "size");
    JoyValue v = POP();
    size_t sz = 0;
    switch (v.type) {
        case JOY_LIST: sz = v.data.list->length; break;
        case JOY_QUOTATION: sz = v.data.quotation->length; break;
        case JOY_STRING: sz = strlen(v.data.string); break;
        case JOY_SET: sz = joy_set_size(v.data.set); break;
        default: joy_error_type("size", "aggregate", v.type);
    }
    joy_value_free(&v);
    PUSH(joy_integer((int64_t)sz));
}

static void prim_null(JoyContext* ctx) {
    REQUIRE(1, "null");
    JoyValue v = POP();
    bool is_null = false;
    switch (v.type) {
        case JOY_INTEGER: is_null = v.data.integer == 0; break;
        case JOY_FLOAT: is_null = v.data.floating == 0.0; break;
        case JOY_BOOLEAN: is_null = !v.data.boolean; break;
        case JOY_LIST: is_null = v.data.list->length == 0; break;
        case JOY_QUOTATION: is_null = v.data.quotation->length == 0; break;
        case JOY_STRING: is_null = v.data.string[0] == '\0'; break;
        case JOY_SET: is_null = v.data.set == 0; break;
        default: is_null = false;
    }
    joy_value_free(&v);
    PUSH(joy_boolean(is_null));
}

static void prim_small(JoyContext* ctx) {
    REQUIRE(1, "small");
    JoyValue v = POP();
    bool is_small = false;
    switch (v.type) {
        case JOY_INTEGER: is_small = v.data.integer <= 1 && v.data.integer >= -1; break;
        case JOY_LIST: is_small = v.data.list->length <= 1; break;
        case JOY_QUOTATION: is_small = v.data.quotation->length <= 1; break;
        case JOY_STRING: is_small = strlen(v.data.string) <= 1; break;
        case JOY_SET: is_small = joy_set_size(v.data.set) <= 1; break;
        default: is_small = false;
    }
    joy_value_free(&v);
    PUSH(joy_boolean(is_small));
}

/* ---------- Quotation Combinators ---------- */

static void prim_i(JoyContext* ctx) {
    REQUIRE(1, "i");
    JoyValue v = POP();
    if (v.type == JOY_QUOTATION) {
        joy_execute_quotation(ctx, v.data.quotation);
    } else if (v.type == JOY_LIST) {
        /* Treat list as quotation */
        for (size_t i = 0; i < v.data.list->length; i++) {
            joy_execute_value(ctx, v.data.list->items[i]);
        }
    } else {
        joy_error_type("i", "QUOTATION", v.type);
    }
    joy_value_free(&v);
}

static void prim_x(JoyContext* ctx) {
    REQUIRE(1, "x");
    JoyValue v = PEEK();
    if (v.type == JOY_QUOTATION) {
        joy_execute_quotation(ctx, v.data.quotation);
    } else if (v.type == JOY_LIST) {
        for (size_t i = 0; i < v.data.list->length; i++) {
            joy_execute_value(ctx, v.data.list->items[i]);
        }
    } else {
        joy_error_type("x", "QUOTATION", v.type);
    }
}

static void prim_dip(JoyContext* ctx) {
    REQUIRE(2, "dip");
    JoyValue quot = POP();
    JoyValue saved = POP();
    if (quot.type == JOY_QUOTATION) {
        joy_execute_quotation(ctx, quot.data.quotation);
    } else if (quot.type == JOY_LIST) {
        for (size_t i = 0; i < quot.data.list->length; i++) {
            joy_execute_value(ctx, quot.data.list->items[i]);
        }
    } else {
        joy_error_type("dip", "QUOTATION", quot.type);
    }
    PUSH(saved);
    joy_value_free(&quot);
}

static void prim_ifte(JoyContext* ctx) {
    REQUIRE(3, "ifte");
    JoyValue falseBranch = POP();
    JoyValue trueBranch = POP();
    JoyValue condition = POP();

    /* Save stack state */
    JoyStack* saved = joy_stack_copy(ctx->stack);

    /* Execute condition */
    if (condition.type == JOY_QUOTATION) {
        joy_execute_quotation(ctx, condition.data.quotation);
    } else if (condition.type == JOY_LIST) {
        for (size_t i = 0; i < condition.data.list->length; i++) {
            joy_execute_value(ctx, condition.data.list->items[i]);
        }
    }

    /* Get result and restore stack */
    JoyValue result = POP();
    bool cond_result = joy_value_truthy(result);
    joy_value_free(&result);

    /* Restore stack */
    joy_stack_free(ctx->stack);
    ctx->stack = saved;

    /* Execute appropriate branch */
    JoyValue branch = cond_result ? trueBranch : falseBranch;
    if (branch.type == JOY_QUOTATION) {
        joy_execute_quotation(ctx, branch.data.quotation);
    } else if (branch.type == JOY_LIST) {
        for (size_t i = 0; i < branch.data.list->length; i++) {
            joy_execute_value(ctx, branch.data.list->items[i]);
        }
    }

    joy_value_free(&condition);
    joy_value_free(&trueBranch);
    joy_value_free(&falseBranch);
}

static void prim_branch(JoyContext* ctx) {
    REQUIRE(3, "branch");
    JoyValue falseBranch = POP();
    JoyValue trueBranch = POP();
    JoyValue cond = POP();
    bool b = joy_value_truthy(cond);
    joy_value_free(&cond);
    JoyValue branch = b ? trueBranch : falseBranch;
    if (branch.type == JOY_QUOTATION) {
        joy_execute_quotation(ctx, branch.data.quotation);
    } else if (branch.type == JOY_LIST) {
        for (size_t i = 0; i < branch.data.list->length; i++) {
            joy_execute_value(ctx, branch.data.list->items[i]);
        }
    }
    joy_value_free(&trueBranch);
    joy_value_free(&falseBranch);
}

static void prim_times(JoyContext* ctx) {
    REQUIRE(2, "times");
    JoyValue quot = POP();
    JoyValue count = POP();
    EXPECT_TYPE(count, JOY_INTEGER, "times");
    for (int64_t i = 0; i < count.data.integer; i++) {
        if (quot.type == JOY_QUOTATION) {
            joy_execute_quotation(ctx, quot.data.quotation);
        } else if (quot.type == JOY_LIST) {
            for (size_t j = 0; j < quot.data.list->length; j++) {
                joy_execute_value(ctx, quot.data.list->items[j]);
            }
        }
    }
    joy_value_free(&quot);
}

static void prim_while(JoyContext* ctx) {
    REQUIRE(2, "while");
    JoyValue body = POP();
    JoyValue cond = POP();

    while (true) {
        /* Save stack for condition test */
        JoyStack* saved = joy_stack_copy(ctx->stack);

        /* Execute condition */
        if (cond.type == JOY_QUOTATION) {
            joy_execute_quotation(ctx, cond.data.quotation);
        } else if (cond.type == JOY_LIST) {
            for (size_t i = 0; i < cond.data.list->length; i++) {
                joy_execute_value(ctx, cond.data.list->items[i]);
            }
        }

        JoyValue result = POP();
        bool cont = joy_value_truthy(result);
        joy_value_free(&result);

        /* Restore stack */
        joy_stack_free(ctx->stack);
        ctx->stack = saved;

        if (!cont) break;

        /* Execute body */
        if (body.type == JOY_QUOTATION) {
            joy_execute_quotation(ctx, body.data.quotation);
        } else if (body.type == JOY_LIST) {
            for (size_t i = 0; i < body.data.list->length; i++) {
                joy_execute_value(ctx, body.data.list->items[i]);
            }
        }
    }

    joy_value_free(&cond);
    joy_value_free(&body);
}

static void prim_map(JoyContext* ctx) {
    REQUIRE(2, "map");
    JoyValue quot = POP();
    JoyValue agg = POP();

    if (agg.type != JOY_LIST && agg.type != JOY_QUOTATION) {
        joy_error_type("map", "aggregate", agg.type);
    }

    size_t len = agg.type == JOY_LIST ? agg.data.list->length : agg.data.quotation->length;
    JoyValue* items = agg.type == JOY_LIST ? agg.data.list->items : agg.data.quotation->terms;

    JoyList* result = joy_list_new(len);

    for (size_t i = 0; i < len; i++) {
        PUSH(joy_value_copy(items[i]));
        if (quot.type == JOY_QUOTATION) {
            joy_execute_quotation(ctx, quot.data.quotation);
        } else if (quot.type == JOY_LIST) {
            for (size_t j = 0; j < quot.data.list->length; j++) {
                joy_execute_value(ctx, quot.data.list->items[j]);
            }
        }
        JoyValue mapped = POP();
        joy_list_push(result, mapped);
    }

    joy_value_free(&agg);
    joy_value_free(&quot);

    JoyValue rv = {.type = JOY_LIST, .data.list = result};
    PUSH(rv);
}

static void prim_step(JoyContext* ctx) {
    REQUIRE(2, "step");
    JoyValue quot = POP();
    JoyValue agg = POP();

    size_t len = 0;
    JoyValue* items = NULL;

    if (agg.type == JOY_LIST) {
        len = agg.data.list->length;
        items = agg.data.list->items;
    } else if (agg.type == JOY_QUOTATION) {
        len = agg.data.quotation->length;
        items = agg.data.quotation->terms;
    } else {
        joy_error_type("step", "aggregate", agg.type);
    }

    for (size_t i = 0; i < len; i++) {
        PUSH(joy_value_copy(items[i]));
        if (quot.type == JOY_QUOTATION) {
            joy_execute_quotation(ctx, quot.data.quotation);
        } else if (quot.type == JOY_LIST) {
            for (size_t j = 0; j < quot.data.list->length; j++) {
                joy_execute_value(ctx, quot.data.list->items[j]);
            }
        }
    }

    joy_value_free(&agg);
    joy_value_free(&quot);
}

static void prim_fold(JoyContext* ctx) {
    REQUIRE(3, "fold");
    JoyValue quot = POP();
    JoyValue init = POP();
    JoyValue agg = POP();

    PUSH(init);

    size_t len = 0;
    JoyValue* items = NULL;

    if (agg.type == JOY_LIST) {
        len = agg.data.list->length;
        items = agg.data.list->items;
    } else if (agg.type == JOY_QUOTATION) {
        len = agg.data.quotation->length;
        items = agg.data.quotation->terms;
    } else {
        joy_error_type("fold", "aggregate", agg.type);
    }

    for (size_t i = 0; i < len; i++) {
        PUSH(joy_value_copy(items[i]));
        if (quot.type == JOY_QUOTATION) {
            joy_execute_quotation(ctx, quot.data.quotation);
        } else if (quot.type == JOY_LIST) {
            for (size_t j = 0; j < quot.data.list->length; j++) {
                joy_execute_value(ctx, quot.data.list->items[j]);
            }
        }
    }

    joy_value_free(&agg);
    joy_value_free(&quot);
}

static void prim_filter(JoyContext* ctx) {
    REQUIRE(2, "filter");
    JoyValue quot = POP();
    JoyValue agg = POP();

    if (agg.type != JOY_LIST && agg.type != JOY_QUOTATION) {
        joy_error_type("filter", "aggregate", agg.type);
    }

    size_t len = agg.type == JOY_LIST ? agg.data.list->length : agg.data.quotation->length;
    JoyValue* items = agg.type == JOY_LIST ? agg.data.list->items : agg.data.quotation->terms;

    JoyList* result = joy_list_new(len);

    for (size_t i = 0; i < len; i++) {
        JoyValue item = joy_value_copy(items[i]);
        PUSH(joy_value_copy(item));
        if (quot.type == JOY_QUOTATION) {
            joy_execute_quotation(ctx, quot.data.quotation);
        } else if (quot.type == JOY_LIST) {
            for (size_t j = 0; j < quot.data.list->length; j++) {
                joy_execute_value(ctx, quot.data.list->items[j]);
            }
        }
        JoyValue pred = POP();
        if (joy_value_truthy(pred)) {
            joy_list_push(result, item);
        } else {
            joy_value_free(&item);
        }
        joy_value_free(&pred);
    }

    joy_value_free(&agg);
    joy_value_free(&quot);

    JoyValue rv = {.type = JOY_LIST, .data.list = result};
    PUSH(rv);
}

/* ---------- I/O Operations ---------- */

static void prim_put(JoyContext* ctx) {
    REQUIRE(1, "put");
    JoyValue v = POP();
    joy_value_print(v);
    joy_value_free(&v);
}

static void prim_putch(JoyContext* ctx) {
    REQUIRE(1, "putch");
    JoyValue v = POP();
    if (v.type == JOY_CHAR) {
        putchar(v.data.character);
    } else if (v.type == JOY_INTEGER) {
        putchar((char)v.data.integer);
    } else {
        joy_error_type("putch", "CHAR or INTEGER", v.type);
    }
    joy_value_free(&v);
}

static void prim_putchars(JoyContext* ctx) {
    REQUIRE(1, "putchars");
    JoyValue v = POP();
    EXPECT_TYPE(v, JOY_STRING, "putchars");
    printf("%s", v.data.string);
    joy_value_free(&v);
}

static void prim_newline(JoyContext* ctx) {
    (void)ctx;
    printf("\n");
}

/* ---------- Type Predicates ---------- */

static void prim_integer(JoyContext* ctx) {
    REQUIRE(1, "integer");
    JoyValue v = POP();
    PUSH(joy_boolean(v.type == JOY_INTEGER));
    joy_value_free(&v);
}

static void prim_float_p(JoyContext* ctx) {
    REQUIRE(1, "float");
    JoyValue v = POP();
    PUSH(joy_boolean(v.type == JOY_FLOAT));
    joy_value_free(&v);
}

static void prim_logical(JoyContext* ctx) {
    REQUIRE(1, "logical");
    JoyValue v = POP();
    PUSH(joy_boolean(v.type == JOY_BOOLEAN));
    joy_value_free(&v);
}

static void prim_char_p(JoyContext* ctx) {
    REQUIRE(1, "char");
    JoyValue v = POP();
    PUSH(joy_boolean(v.type == JOY_CHAR));
    joy_value_free(&v);
}

static void prim_string_p(JoyContext* ctx) {
    REQUIRE(1, "string");
    JoyValue v = POP();
    PUSH(joy_boolean(v.type == JOY_STRING));
    joy_value_free(&v);
}

static void prim_list(JoyContext* ctx) {
    REQUIRE(1, "list");
    JoyValue v = POP();
    PUSH(joy_boolean(v.type == JOY_LIST || v.type == JOY_QUOTATION));
    joy_value_free(&v);
}

static void prim_set_p(JoyContext* ctx) {
    REQUIRE(1, "set");
    JoyValue v = POP();
    PUSH(joy_boolean(v.type == JOY_SET));
    joy_value_free(&v);
}

/* ---------- Type Conversion ---------- */

static void prim_ord(JoyContext* ctx) {
    REQUIRE(1, "ord");
    JoyValue v = POP();
    EXPECT_TYPE(v, JOY_CHAR, "ord");
    PUSH(joy_integer((int64_t)(unsigned char)v.data.character));
}

static void prim_chr(JoyContext* ctx) {
    REQUIRE(1, "chr");
    JoyValue v = POP();
    EXPECT_TYPE(v, JOY_INTEGER, "chr");
    PUSH(joy_char((char)v.data.integer));
}

/* ---------- Constants ---------- */

static void prim_true(JoyContext* ctx) {
    PUSH(joy_boolean(true));
}

static void prim_false(JoyContext* ctx) {
    PUSH(joy_boolean(false));
}

/* ---------- Registration ---------- */

void joy_register_primitives(JoyContext* ctx) {
    JoyDict* d = ctx->dictionary;

    /* Stack */
    joy_dict_define_primitive(d, "dup", prim_dup);
    joy_dict_define_primitive(d, "pop", prim_pop);
    joy_dict_define_primitive(d, "swap", prim_swap);
    joy_dict_define_primitive(d, "rollup", prim_rollup);
    joy_dict_define_primitive(d, "rolldown", prim_rolldown);
    joy_dict_define_primitive(d, "rotate", prim_rotate);
    joy_dict_define_primitive(d, "dupd", prim_dupd);
    joy_dict_define_primitive(d, "swapd", prim_swapd);
    joy_dict_define_primitive(d, "popd", prim_popd);
    joy_dict_define_primitive(d, "stack", prim_stack);
    joy_dict_define_primitive(d, "unstack", prim_unstack);

    /* Arithmetic */
    joy_dict_define_primitive(d, "+", prim_add);
    joy_dict_define_primitive(d, "-", prim_sub);
    joy_dict_define_primitive(d, "*", prim_mul);
    joy_dict_define_primitive(d, "/", prim_div);
    joy_dict_define_primitive(d, "rem", prim_rem);
    joy_dict_define_primitive(d, "succ", prim_succ);
    joy_dict_define_primitive(d, "pred", prim_pred);
    joy_dict_define_primitive(d, "abs", prim_abs);
    joy_dict_define_primitive(d, "neg", prim_neg);
    joy_dict_define_primitive(d, "sign", prim_sign);
    joy_dict_define_primitive(d, "max", prim_max);
    joy_dict_define_primitive(d, "min", prim_min);

    /* Math */
    joy_dict_define_primitive(d, "sin", prim_sin);
    joy_dict_define_primitive(d, "cos", prim_cos);
    joy_dict_define_primitive(d, "tan", prim_tan);
    joy_dict_define_primitive(d, "sqrt", prim_sqrt);
    joy_dict_define_primitive(d, "exp", prim_exp);
    joy_dict_define_primitive(d, "log", prim_log);
    joy_dict_define_primitive(d, "pow", prim_pow);
    joy_dict_define_primitive(d, "floor", prim_floor);
    joy_dict_define_primitive(d, "ceil", prim_ceil);
    joy_dict_define_primitive(d, "trunc", prim_trunc);

    /* Comparison */
    joy_dict_define_primitive(d, "=", prim_eq);
    joy_dict_define_primitive(d, "!=", prim_neq);
    joy_dict_define_primitive(d, "<", prim_lt);
    joy_dict_define_primitive(d, ">", prim_gt);
    joy_dict_define_primitive(d, "<=", prim_le);
    joy_dict_define_primitive(d, ">=", prim_ge);

    /* Logical */
    joy_dict_define_primitive(d, "and", prim_and);
    joy_dict_define_primitive(d, "or", prim_or);
    joy_dict_define_primitive(d, "not", prim_not);

    /* Aggregates */
    joy_dict_define_primitive(d, "first", prim_first);
    joy_dict_define_primitive(d, "rest", prim_rest);
    joy_dict_define_primitive(d, "cons", prim_cons);
    joy_dict_define_primitive(d, "swons", prim_swons);
    joy_dict_define_primitive(d, "uncons", prim_uncons);
    joy_dict_define_primitive(d, "concat", prim_concat);
    joy_dict_define_primitive(d, "size", prim_size);
    joy_dict_define_primitive(d, "null", prim_null);
    joy_dict_define_primitive(d, "small", prim_small);

    /* Combinators */
    joy_dict_define_primitive(d, "i", prim_i);
    joy_dict_define_primitive(d, "x", prim_x);
    joy_dict_define_primitive(d, "dip", prim_dip);
    joy_dict_define_primitive(d, "ifte", prim_ifte);
    joy_dict_define_primitive(d, "branch", prim_branch);
    joy_dict_define_primitive(d, "times", prim_times);
    joy_dict_define_primitive(d, "while", prim_while);
    joy_dict_define_primitive(d, "map", prim_map);
    joy_dict_define_primitive(d, "step", prim_step);
    joy_dict_define_primitive(d, "fold", prim_fold);
    joy_dict_define_primitive(d, "filter", prim_filter);

    /* I/O */
    joy_dict_define_primitive(d, "put", prim_put);
    joy_dict_define_primitive(d, "putch", prim_putch);
    joy_dict_define_primitive(d, "putchars", prim_putchars);
    joy_dict_define_primitive(d, ".", prim_newline);

    /* Type predicates */
    joy_dict_define_primitive(d, "integer", prim_integer);
    joy_dict_define_primitive(d, "float", prim_float_p);
    joy_dict_define_primitive(d, "logical", prim_logical);
    joy_dict_define_primitive(d, "char", prim_char_p);
    joy_dict_define_primitive(d, "string", prim_string_p);
    joy_dict_define_primitive(d, "list", prim_list);
    joy_dict_define_primitive(d, "set", prim_set_p);

    /* Type conversion */
    joy_dict_define_primitive(d, "ord", prim_ord);
    joy_dict_define_primitive(d, "chr", prim_chr);

    /* Constants */
    joy_dict_define_primitive(d, "true", prim_true);
    joy_dict_define_primitive(d, "false", prim_false);
}
