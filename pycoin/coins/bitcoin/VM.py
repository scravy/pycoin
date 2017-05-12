
from ...tx.script import intops, stackops, checksigops, miscops

from ...tx.script import errno, opcodes, ScriptError

from .ScriptCodec import BitcoinScriptCodec
from .ScriptTools import BitcoinScriptTools

from ...tx.script.BaseVM import VM


def _make_bad_instruction(v):
    def f(vm_state):
        raise ScriptError("invalid instruction x%02x at %d" % (v, vm_state.pc), errno.BAD_OPCODE)
    return f


def _collect_opcodes(module):
    d = {}
    for k in dir(module):
        if k.startswith("do_OP"):
            d[k[3:]] = getattr(module, k)
    return d


def _no_op(vm):
    pass


def _make_instruction_lookup(opcode_pairs):
    OPCODE_DATA_LIST = list(BitcoinScriptCodec.data_opcodes)

    # start with all opcodes invalid
    instruction_lookup = [_make_bad_instruction(i) for i in range(256)]

    for i in OPCODE_DATA_LIST:
        instruction_lookup[i] = _no_op
    opcode_lookups = {}
    # BRAIN DAMAGE
    opcode_lookups.update(_collect_opcodes(checksigops))
    opcode_lookups.update(_collect_opcodes(intops))
    opcode_lookups.update(stackops.all_opcodes())
    opcode_lookups.update(miscops.all_opcodes())
    for opcode_name, opcode_value in opcode_pairs:
        if opcode_name in opcode_lookups:
            instruction_lookup[opcode_value] = opcode_lookups[opcode_name]
    return instruction_lookup


def make_vm():
    class BitcoinVM(VM):
        INSTRUCTION_LOOKUP = _make_instruction_lookup(opcodes.OPCODE_LIST)
        ScriptCodec = BitcoinScriptCodec
        dataCodec = BitcoinScriptCodec

        bin_script = BitcoinScriptTools.compile_push_data_list
    return BitcoinVM


BitcoinVM = make_vm()
