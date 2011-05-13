from quex.input.setup import setup as Setup
from   quex.core_engine.generator.languages.address import get_label

def do(StateIdx, InitStateF, SMD):
    """Generate the code fragment that produce the 'input' character for
       the subsequent transition map. In general this consists of 

           (i)  incrementing/decrementing the input pointer.
           (ii) dereferencing the pointer to get a value.

       The initial state in forward lexing is an exception! The input pointer
       is not increased, since it already stands on the right position from
       the last analyzis step. When the init state is entered from any 'normal'
       state it enters via the 'epilog' generated in the function 
       do_init_state_input_epilog().
    """
    LanguageDB = Setup.language_db

    txt = []

    if not InitStateF: 
        txt.append("    __quex_assert_no_passage();\n")

    if InitStateF and SMD.forward_lexing_f():
        txt.append(get_label("$init_state_fw_transition_block") + ":\n")
        txt.append("    " + LanguageDB["$debug-init-state"]) 
    else:
        txt.append(get_label("$entry", StateIdx) + ":\n")
        txt.append("    " + LanguageDB["$debug-state"](StateIdx, SMD.forward_lexing_f())) 

    # The init state in forward lexing does not increase the input pointer
    if not (SMD.forward_lexing_f() and InitStateF): 
        if SMD.forward_lexing_f(): cmd = LanguageDB["$input/increment"]
        else:                      cmd = LanguageDB["$input/decrement"]
        txt.extend(["    ", cmd, "\n"])

    txt.extend(["    ", LanguageDB["$input/get"], "\n"])

    return txt

