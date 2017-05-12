"""
Implement instructions of the Bitcoin VM.


The MIT License (MIT)

Copyright (c) 2013 by Richard Kiss

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from . import errno
from . import ScriptError

from .flags import VERIFY_MINIMALDATA


def do_OP_VERIFY(vm):
    v = vm.bool_from_script_bytes(vm.stack.pop())
    if not v:
        raise ScriptError("VERIFY failed", errno.VERIFY)


def do_OP_DEPTH(vm):
    """
    >>> s = [1, 2, 1, 2, 1, 2]
    >>> do_OP_DEPTH(s)
    >>> print(s)
    [1, 2, 1, 2, 1, 2, b'\\x06']
    """
    vm.stack.append(vm.IntStreamer.int_to_script_bytes(len(vm.stack)))


def do_OP_PICK(vm):
    """
    >>> s = [b'a', b'b', b'c', b'd', b'\2']
    >>> do_OP_PICK(s, require_minimal=True)
    >>> print(s)
    [b'a', b'b', b'c', b'd', b'b']
    """
    v = vm.nonnegative_int_from_script_bytes(vm.stack.pop(), require_minimal=vm.flags & VERIFY_MINIMALDATA)
    vm.stack.append(vm.stack[-v-1])


def do_OP_ROLL(vm):
    """
    >>> s = [b'a', b'b', b'c', b'd', b'\2']
    >>> do_OP_ROLL(s, require_minimal=True)
    >>> print(s)
    [b'a', b'c', b'd', b'b']
    """
    v = vm.nonnegative_int_from_script_bytes(vm.stack.pop(), require_minimal=vm.flags & VERIFY_MINIMALDATA)
    vm.stack.append(vm.stack.pop(-v-1))


def do_OP_SUBSTR(vm):
    """
    >>> s = [b'abcdef', b'\3', b'\2']
    >>> do_OP_SUBSTR(s, require_minimal=True)
    >>> print(s)
    [b'de']
    """
    pos = vm.nonnegative_int_from_script_bytes(vm.stack.pop(), require_minimal=vm.flags & VERIFY_MINIMALDATA)
    length = vm.nonnegative_int_from_script_bytes(vm.stack.pop(), require_minimal=vm.flags & VERIFY_MINIMALDATA)
    vm.stack.append(vm.stack.pop()[length:length+pos])


def do_OP_LEFT(vm):
    """
    >>> s = [b'abcdef', b'\3']
    >>> do_OP_LEFT(s, require_minimal=True)
    >>> print(len(s)==1 and s[0]==b'abc')
    True
    >>> s = [b'abcdef', b'']
    >>> do_OP_LEFT(s, require_minimal=True)
    >>> print(len(s) ==1 and s[0]==b'')
    True
    """
    pos = vm.nonnegative_int_from_script_bytes(vm.stack.pop(), require_minimal=vm.flags & VERIFY_MINIMALDATA)
    vm.stack.append(vm.stack.pop()[:pos])


def do_OP_RIGHT(vm):
    """
    >>> s = [b'abcdef', b'\\3']
    >>> do_OP_RIGHT(s, require_minimal=True)
    >>> print(s==[b'def'])
    True
    >>> s = [b'abcdef', b'\\0']
    >>> do_OP_RIGHT(s, require_minimal=False)
    >>> print(s==[b''])
    True
    """
    pos = vm.nonnegative_int_from_script_bytes(vm.stack.pop(), require_minimal=vm.flags & VERIFY_MINIMALDATA)
    if pos > 0:
        vm.stack.append(vm.stack.pop()[-pos:])
    else:
        vm.stack.pop()
        vm.stack.append(b'')


def do_OP_SIZE(vm):
    """
    >>> import binascii
    >>> s = [b'abcdef']
    >>> do_OP_SIZE(s)
    >>> print(s == [b'abcdef', b'\x06'])
    True
    >>> s = [b'abcdef'*1000]
    >>> do_OP_SIZE(s)
    >>> print(binascii.hexlify(s[-1]) == b'7017')
    True
    """
    vm.stack.append(vm.IntStreamer.int_to_script_bytes(len(vm.stack[-1])))


def make_same_size(v1, v2):
    larger = max(len(v1), len(v2))
    nulls = b'\0' * larger
    v1 = (v1 + nulls)[:larger]
    v2 = (v2 + nulls)[:larger]
    return v1, v2


def do_OP_EQUAL(vm):
    """
    >>> s = [b'string1', b'string1']
    >>> do_OP_EQUAL(s)
    >>> print(s == [b'\1'])
    True
    >>> s = [b'string1', b'string2']
    >>> do_OP_EQUAL(s)
    >>> print(s == [b''])
    True
    """
    v1, v2 = [vm.stack.pop() for i in range(2)]
    vm.stack.append(vm.bool_to_script_bytes(v1 == v2))


def do_OP_EQUALVERIFY(vm):
    do_OP_EQUAL(vm)
    v = vm.bool_from_script_bytes(vm.stack.pop())
    if not v:
        raise ScriptError("VERIFY failed", errno.EQUALVERIFY)


def pop_check_bounds(vm):
    v = vm.stack.pop()
    if len(v) > 4:
        raise ScriptError("overflow in binop", errno.UNKNOWN_ERROR)
    return vm.IntStreamer.int_from_script_bytes(v, require_minimal=vm.flags & VERIFY_MINIMALDATA)


def make_bin_op(binop):
    def f(vm):
        v1, v2 = [pop_check_bounds(vm) for i in range(2)]
        vm.stack.append(vm.IntStreamer.int_to_script_bytes(binop(v2, v1)))
    return f


def make_bool_bin_op(binop):
    def f(vm):
        v1, v2 = [pop_check_bounds(vm) for i in range(2)]
        vm.stack.append(vm.bool_to_script_bytes(binop(v2, v1)))
    return f


do_OP_ADD = make_bin_op(lambda x, y: x + y)
do_OP_SUB = make_bin_op(lambda x, y: x - y)
do_OP_MUL = make_bin_op(lambda x, y: x * y)
do_OP_DIV = make_bin_op(lambda x, y: x // y)
do_OP_MOD = make_bin_op(lambda x, y: x % y)
do_OP_LSHIFT = make_bin_op(lambda x, y: x << y)
do_OP_RSHIFT = make_bin_op(lambda x, y: x >> y)
do_OP_BOOLAND = make_bool_bin_op(lambda x, y: x and y)
do_OP_BOOLOR = make_bool_bin_op(lambda x, y: x or y)
do_OP_NUMEQUAL = make_bool_bin_op(lambda x, y: x == y)
do_OP_NUMNOTEQUAL = make_bool_bin_op(lambda x, y: x != y)
do_OP_LESSTHAN = make_bool_bin_op(lambda x, y: x < y)
do_OP_GREATERTHAN = make_bool_bin_op(lambda x, y: x > y)
do_OP_LESSTHANOREQUAL = make_bool_bin_op(lambda x, y: x <= y)
do_OP_GREATERTHANOREQUAL = make_bool_bin_op(lambda x, y: x >= y)
do_OP_MIN = make_bin_op(min)
do_OP_MAX = make_bin_op(max)


def do_OP_NUMEQUALVERIFY(vm):
    do_OP_NUMEQUAL(vm)
    do_OP_VERIFY(vm)


def do_OP_WITHIN(vm):
    """
    >>> s = [b'b', b'a', b'c']
    >>> do_OP_WITHIN(s, False)
    >>> print(s == [b'\1'])
    True
    >>> s = [b'd', b'a', b'c']
    >>> do_OP_WITHIN(s, False)
    >>> print(s == [b''])
    True
    """
    v3, v2, v1 = [vm.IntStreamer.int_from_script_bytes(
        vm.stack.pop(), require_minimal=vm.flags & VERIFY_MINIMALDATA) for i in range(3)]
    ok = (v2 <= v1 < v3)
    vm.stack.append(vm.bool_to_script_bytes(ok))


def make_unary_num_op(unary_f):
    def f(vm):
        vm.stack.append(vm.IntStreamer.int_to_script_bytes(unary_f(pop_check_bounds(vm))))
    return f


do_OP_1ADD = make_unary_num_op(lambda x: x + 1)
do_OP_1SUB = make_unary_num_op(lambda x: x - 1)
do_OP_2MUL = make_unary_num_op(lambda x: x << 1)
do_OP_2DIV = make_unary_num_op(lambda x: x >> 1)
do_OP_NEGATE = make_unary_num_op(lambda x: -x)
do_OP_ABS = make_unary_num_op(lambda x: abs(x))


def do_OP_NOT(vm):
    return vm.stack.append(vm.bool_to_script_bytes(not pop_check_bounds(vm)))


def do_OP_0NOTEQUAL(vm):
    return vm.stack.append(
        vm.IntStreamer.int_to_script_bytes(
            vm.bool_from_script_bytes(
                vm.stack.pop(), require_minimal=vm.flags & VERIFY_MINIMALDATA)))
