#include "UTF16Lex.h"
#include <quex/code_base/analyzer/C-adaptions.h>
QUEX_NAMESPACE_MAIN_OPEN
/* Global */QUEX_NAME(Mode)  QUEX_NAME(X);
#ifndef __QUEX_INDICATOR_DUMPED_TOKEN_ID_DEFINED
    static QUEX_TYPE_TOKEN_ID    QUEX_NAME_TOKEN(DumpedTokenIdObject);
#endif
#define self  (*(QUEX_TYPE_DERIVED_ANALYZER*)me)
#define __self_result_token_id    QUEX_NAME_TOKEN(DumpedTokenIdObject)

void
QUEX_NAME(X_on_entry)(QUEX_TYPE_ANALYZER* me, const QUEX_NAME(Mode)* FromMode) {
    (void)me;
    (void)FromMode;
#   ifdef QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
    QUEX_NAME(X).has_entry_from(FromMode);
#   endif

}

void
QUEX_NAME(X_on_exit)(QUEX_TYPE_ANALYZER* me, const QUEX_NAME(Mode)* ToMode)  {
    (void)me;
    (void)ToMode;
#   ifdef QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
    QUEX_NAME(X).has_exit_to(ToMode);
#   endif

}

#if defined(QUEX_OPTION_INDENTATION_TRIGGER) 
void
QUEX_NAME(X_on_indentation)(QUEX_TYPE_ANALYZER*    me, 
                                        QUEX_TYPE_INDENTATION  Indentation, 
                                        QUEX_TYPE_CHARACTER*   Begin) {
    (void)me;
    (void)Indentation;
    (void)Begin;
    return;
}
#endif

#ifdef QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
bool
QUEX_NAME(X_has_base)(const QUEX_NAME(Mode)* Mode) {
    (void)Mode;
    return false;
}
bool
QUEX_NAME(X_has_entry_from)(const QUEX_NAME(Mode)* Mode) {
    (void)Mode;
    return true; /* default */
}
bool
QUEX_NAME(X_has_exit_to)(const QUEX_NAME(Mode)* Mode) {
    (void)Mode;
    return true; /* default */
}
#endif    
#undef self
#undef __self_result_token_id
QUEX_NAMESPACE_MAIN_CLOSE

/* #include "UTF16Lex.h"*/
#if defined(__QUEX_OPTION_CONVERTER_HELPER)
#   include "quex/code_base/converter_helper/utf16.i"
#endif
#include <quex/code_base/analyzer/headers.i>
#include <quex/code_base/analyzer/C-adaptions.h>
QUEX_NAMESPACE_MAIN_OPEN
QUEX_TYPE_CHARACTER  QUEX_NAME(LexemeNullObject) = (QUEX_TYPE_CHARACTER)0;

#include <quex/code_base/analyzer/member/basic>
#include <quex/code_base/buffer/Buffer>
#ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
#   include <quex/code_base/token/TokenQueue>
#endif

#ifdef    CONTINUE
#   undef CONTINUE
#endif
#define   CONTINUE goto __REENTRY_PREPARATION; 

#ifdef    RETURN
#   undef RETURN
#endif

#if defined(QUEX_OPTION_TOKEN_POLICY_QUEUE)
#   define RETURN   return
#else
#   define RETURN   do { return __self_result_token_id; } while(0)
#endif
#include <quex/code_base/temporary_macros_on>

__QUEX_TYPE_ANALYZER_RETURN_VALUE  
QUEX_NAME(X_analyzer_function)(QUEX_TYPE_ANALYZER* me) 
{
    /* NOTE: Different modes correspond to different analyzer functions. The analyzer  
             functions are all located inside the main class as static functions. That  
             means, they are something like 'globals'. They receive a pointer to the   
             lexical analyzer, since static member do not have access to the 'this' pointer.
     */
#   if defined(QUEX_OPTION_TOKEN_POLICY_SINGLE)
    register QUEX_TYPE_TOKEN_ID __self_result_token_id 
           = (QUEX_TYPE_TOKEN_ID)__QUEX_SETTING_TOKEN_ID_UNINITIALIZED;
#   endif
#   ifdef     self
#       undef self
#   endif
#   define self (*((QUEX_TYPE_ANALYZER*)me))
    QUEX_TYPE_CHARACTER_POSITION*  post_context_start_position    = 0x0;
    const size_t                   PostContextStartPositionN      = (size_t)0;
    QUEX_TYPE_GOTO_LABEL           last_acceptance                = QUEX_LABEL(128);
    QUEX_TYPE_GOTO_LABEL           target_state_else_index        = ((QUEX_TYPE_CHARACTER)0x0);
    QUEX_TYPE_CHARACTER            input                          = (QUEX_TYPE_CHARACTER)(0x00);
    QUEX_TYPE_GOTO_LABEL           target_state_index             = ((QUEX_TYPE_CHARACTER)0x0);
    QUEX_TYPE_CHARACTER_POSITION   last_acceptance_input_position = ((QUEX_TYPE_CHARACTER*)0x00);
#   ifndef QUEX_OPTION_COMPUTED_GOTOS
#   endif /* QUEX_OPTION_COMPUTED_GOTOS */
#   define X    (QUEX_NAME(X))

    /* Post context positions do not have to be reset or initialized. If a state
     * is reached which is associated with 'end of post context' it is clear what
     * post context is meant. This results from the ways the state machine is 
     * constructed. A post context positions live time looks like the following:
     *
     * (1)   unitialized (don't care)
     * (1.b) on buffer reload it may, or may not be adapted (don't care)
     * (2)   when a post context begin state is passed, the it is **SET** (now: take care)
     * (2.b) on buffer reload it **is adapted**.
     * (3)   when a terminal state of the post context is reached (which can only be reached
     *       for that particular post context, then the post context position is used
     *       to reset the input position.                                              */
#   if    defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE) \
       || defined(QUEX_OPTION_ASSERTS)
    me->DEBUG_analyzer_function_at_entry = me->current_analyzer_function;
#   endif
__REENTRY:
    me->buffer._lexeme_start_p = me->buffer._input_p;
    QUEX_LEXEME_TERMINATING_ZERO_UNDO(&me->buffer);
INIT_STATE_TRANSITION_BLOCK:
    __quex_debug_init_state();
    input = *(me->buffer._input_p);
    if( input < 0x400) {
        if( input < 0x37E) {
            if( input < 0x3A) {
                switch( input ) {
                    case 0x0:     goto __RELOAD_INIT_STATE;
                    case 0x2:     
                    case 0x3:     
                    case 0x4:     
                    case 0x5:     
                    case 0x6:     
                    case 0x7:     
                    case 0x8:     
                    case 0x9:     goto _125;
                    case 0xA:     goto _124;
                    case 0xB:     
                    case 0xC:     
                    case 0xD:     
                    case 0xE:     
                    case 0xF:     
                    case 0x10:    
                    case 0x11:    
                    case 0x12:    
                    case 0x13:    
                    case 0x14:    
                    case 0x15:    
                    case 0x16:    
                    case 0x17:    
                    case 0x18:    
                    case 0x19:    
                    case 0x1A:    
                    case 0x1B:    
                    case 0x1C:    
                    case 0x1D:    
                    case 0x1E:    
                    case 0x1F:    
                    case 0x20:    
                    case 0x21:    
                    case 0x22:    
                    case 0x23:    
                    case 0x24:    
                    case 0x25:    
                    case 0x26:    
                    case 0x27:    
                    case 0x28:    
                    case 0x29:    
                    case 0x2A:    
                    case 0x2B:    
                    case 0x2C:    
                    case 0x2D:    
                    case 0x2E:    
                    case 0x2F:    goto _125;
                    case 0x30:    
                    case 0x31:    
                    case 0x32:    
                    case 0x33:    
                    case 0x34:    
                    case 0x35:    
                    case 0x36:    
                    case 0x37:    
                    case 0x38:    
                    case 0x39:    goto _114;
                }
            } else {
                if( input < 0x47) {
                    switch( input ) {
                        case 0x3A:    goto _126;
                        case 0x3B:    
                        case 0x3C:    
                        case 0x3D:    
                        case 0x3E:    
                        case 0x3F:    
                        case 0x40:    goto _125;
                        case 0x41:    
                        case 0x42:    
                        case 0x43:    
                        case 0x44:    
                        case 0x45:    
                        case 0x46:    goto _114;
                    }
                } else {
                    if( input < 0x374 ) {
                        goto _125;
                    } else if( input < 0x376 ) {
                        goto _115;
                    } else if( input < 0x37A ) {
                        goto _125;
                    } else {
                        goto _115;
}
                }
            }
        } else {
            if( input < 0x38E) {
                switch( input ) {
                    case 0x37E:   
                    case 0x37F:   
                    case 0x380:   
                    case 0x381:   
                    case 0x382:   
                    case 0x383:   goto _125;
                    case 0x384:   
                    case 0x385:   
                    case 0x386:   goto _115;
                    case 0x387:   goto _125;
                    case 0x388:   
                    case 0x389:   
                    case 0x38A:   goto _115;
                    case 0x38B:   goto _125;
                    case 0x38C:   goto _115;
                    case 0x38D:   goto _125;
                }
            } else {
                if( input < 0x3CF) {
                    if( input < 0x3A2 ) {
                        goto _115;
                    } else if( input == 0x3A2 ) {
                        goto _125;
                    } else {
                        goto _115;
}
                } else {
                    switch( input ) {
                        case 0x3CF:   goto _125;
                        case 0x3D0:   
                        case 0x3D1:   
                        case 0x3D2:   
                        case 0x3D3:   
                        case 0x3D4:   
                        case 0x3D5:   
                        case 0x3D6:   
                        case 0x3D7:   
                        case 0x3D8:   
                        case 0x3D9:   
                        case 0x3DA:   
                        case 0x3DB:   
                        case 0x3DC:   
                        case 0x3DD:   
                        case 0x3DE:   
                        case 0x3DF:   
                        case 0x3E0:   
                        case 0x3E1:   goto _115;
                        case 0x3E2:   
                        case 0x3E3:   
                        case 0x3E4:   
                        case 0x3E5:   
                        case 0x3E6:   
                        case 0x3E7:   
                        case 0x3E8:   
                        case 0x3E9:   
                        case 0x3EA:   
                        case 0x3EB:   
                        case 0x3EC:   
                        case 0x3ED:   
                        case 0x3EE:   
                        case 0x3EF:   goto _125;
                        case 0x3F0:   
                        case 0x3F1:   
                        case 0x3F2:   
                        case 0x3F3:   
                        case 0x3F4:   
                        case 0x3F5:   
                        case 0x3F6:   
                        case 0x3F7:   
                        case 0x3F8:   
                        case 0x3F9:   
                        case 0x3FA:   
                        case 0x3FB:   
                        case 0x3FC:   
                        case 0x3FD:   
                        case 0x3FE:   
                        case 0x3FF:   goto _115;
                    }
                }
            }
        }
    } else {
        if( input < 0x1F5E) {
            if( input < 0x1F1E) {
                if( input < 0x1D6B) {
                    if( input < 0x1D5D) {
                        if( input < 0x1D26 ) {
                            goto _125;
                        } else if( input < 0x1D2B ) {
                            goto _115;
                        } else {
                            goto _125;
}
                    } else {
                        switch( input ) {
                            case 0x1D5D:  
                            case 0x1D5E:  
                            case 0x1D5F:  
                            case 0x1D60:  
                            case 0x1D61:  goto _115;
                            case 0x1D62:  
                            case 0x1D63:  
                            case 0x1D64:  
                            case 0x1D65:  goto _125;
                            case 0x1D66:  
                            case 0x1D67:  
                            case 0x1D68:  
                            case 0x1D69:  
                            case 0x1D6A:  goto _115;
                        }
                    }
                } else {
                    if( input < 0x1F00) {
                        if( input < 0x1DBF ) {
                            goto _125;
                        } else if( input == 0x1DBF ) {
                            goto _115;
                        } else {
                            goto _125;
}
                    } else {
                        switch( input ) {
                            case 0x1F00:  
                            case 0x1F01:  
                            case 0x1F02:  
                            case 0x1F03:  
                            case 0x1F04:  
                            case 0x1F05:  
                            case 0x1F06:  
                            case 0x1F07:  
                            case 0x1F08:  
                            case 0x1F09:  
                            case 0x1F0A:  
                            case 0x1F0B:  
                            case 0x1F0C:  
                            case 0x1F0D:  
                            case 0x1F0E:  
                            case 0x1F0F:  
                            case 0x1F10:  
                            case 0x1F11:  
                            case 0x1F12:  
                            case 0x1F13:  
                            case 0x1F14:  
                            case 0x1F15:  goto _115;
                            case 0x1F16:  
                            case 0x1F17:  goto _125;
                            case 0x1F18:  
                            case 0x1F19:  
                            case 0x1F1A:  
                            case 0x1F1B:  
                            case 0x1F1C:  
                            case 0x1F1D:  goto _115;
                        }
                    }
                }
            } else {
                switch( input ) {
                    case 0x1F1E:  
                    case 0x1F1F:  goto _125;
                    case 0x1F20:  
                    case 0x1F21:  
                    case 0x1F22:  
                    case 0x1F23:  
                    case 0x1F24:  
                    case 0x1F25:  
                    case 0x1F26:  
                    case 0x1F27:  
                    case 0x1F28:  
                    case 0x1F29:  
                    case 0x1F2A:  
                    case 0x1F2B:  
                    case 0x1F2C:  
                    case 0x1F2D:  
                    case 0x1F2E:  
                    case 0x1F2F:  
                    case 0x1F30:  
                    case 0x1F31:  
                    case 0x1F32:  
                    case 0x1F33:  
                    case 0x1F34:  
                    case 0x1F35:  
                    case 0x1F36:  
                    case 0x1F37:  
                    case 0x1F38:  
                    case 0x1F39:  
                    case 0x1F3A:  
                    case 0x1F3B:  
                    case 0x1F3C:  
                    case 0x1F3D:  
                    case 0x1F3E:  
                    case 0x1F3F:  
                    case 0x1F40:  
                    case 0x1F41:  
                    case 0x1F42:  
                    case 0x1F43:  
                    case 0x1F44:  
                    case 0x1F45:  goto _115;
                    case 0x1F46:  
                    case 0x1F47:  goto _125;
                    case 0x1F48:  
                    case 0x1F49:  
                    case 0x1F4A:  
                    case 0x1F4B:  
                    case 0x1F4C:  
                    case 0x1F4D:  goto _115;
                    case 0x1F4E:  
                    case 0x1F4F:  goto _125;
                    case 0x1F50:  
                    case 0x1F51:  
                    case 0x1F52:  
                    case 0x1F53:  
                    case 0x1F54:  
                    case 0x1F55:  
                    case 0x1F56:  
                    case 0x1F57:  goto _115;
                    case 0x1F58:  goto _125;
                    case 0x1F59:  goto _115;
                    case 0x1F5A:  goto _125;
                    case 0x1F5B:  goto _115;
                    case 0x1F5C:  goto _125;
                    case 0x1F5D:  goto _115;
                }
            }
        } else {
            if( input < 0x1FF0) {
                if( input < 0x1FC5) {
                    if( input < 0x1F80) {
                        switch( input ) {
                            case 0x1F5E:  goto _125;
                            case 0x1F5F:  
                            case 0x1F60:  
                            case 0x1F61:  
                            case 0x1F62:  
                            case 0x1F63:  
                            case 0x1F64:  
                            case 0x1F65:  
                            case 0x1F66:  
                            case 0x1F67:  
                            case 0x1F68:  
                            case 0x1F69:  
                            case 0x1F6A:  
                            case 0x1F6B:  
                            case 0x1F6C:  
                            case 0x1F6D:  
                            case 0x1F6E:  
                            case 0x1F6F:  
                            case 0x1F70:  
                            case 0x1F71:  
                            case 0x1F72:  
                            case 0x1F73:  
                            case 0x1F74:  
                            case 0x1F75:  
                            case 0x1F76:  
                            case 0x1F77:  
                            case 0x1F78:  
                            case 0x1F79:  
                            case 0x1F7A:  
                            case 0x1F7B:  
                            case 0x1F7C:  
                            case 0x1F7D:  goto _115;
                            case 0x1F7E:  
                            case 0x1F7F:  goto _125;
                        }
                    } else {
                        if( input < 0x1FB5 ) {
                            goto _115;
                        } else if( input == 0x1FB5 ) {
                            goto _125;
                        } else {
                            goto _115;
}
                    }
                } else {
                    switch( input ) {
                        case 0x1FC5:  goto _125;
                        case 0x1FC6:  
                        case 0x1FC7:  
                        case 0x1FC8:  
                        case 0x1FC9:  
                        case 0x1FCA:  
                        case 0x1FCB:  
                        case 0x1FCC:  
                        case 0x1FCD:  
                        case 0x1FCE:  
                        case 0x1FCF:  
                        case 0x1FD0:  
                        case 0x1FD1:  
                        case 0x1FD2:  
                        case 0x1FD3:  goto _115;
                        case 0x1FD4:  
                        case 0x1FD5:  goto _125;
                        case 0x1FD6:  
                        case 0x1FD7:  
                        case 0x1FD8:  
                        case 0x1FD9:  
                        case 0x1FDA:  
                        case 0x1FDB:  goto _115;
                        case 0x1FDC:  goto _125;
                        case 0x1FDD:  
                        case 0x1FDE:  
                        case 0x1FDF:  
                        case 0x1FE0:  
                        case 0x1FE1:  
                        case 0x1FE2:  
                        case 0x1FE3:  
                        case 0x1FE4:  
                        case 0x1FE5:  
                        case 0x1FE6:  
                        case 0x1FE7:  
                        case 0x1FE8:  
                        case 0x1FE9:  
                        case 0x1FEA:  
                        case 0x1FEB:  
                        case 0x1FEC:  
                        case 0x1FED:  
                        case 0x1FEE:  
                        case 0x1FEF:  goto _115;
                    }
                }
            } else {
                if( input < 0x2127) {
                    if( input < 0x1FF6) {
                        switch( input ) {
                            case 0x1FF0:  
                            case 0x1FF1:  goto _125;
                            case 0x1FF2:  
                            case 0x1FF3:  
                            case 0x1FF4:  goto _115;
                            case 0x1FF5:  goto _125;
                        }
                    } else {
                        if( input < 0x1FFF ) {
                            goto _115;
                        } else if( input < 0x2126 ) {
                            goto _125;
                        } else {
                            goto _115;
}
                    }
                } else {
                    if( input < 0xD834) {
                        if( input < 0xD800 ) {
                            goto _125;
                        } else if( input == 0xD800 ) {
                            goto _122;
                        } else {
                            goto _125;
}
                    } else {
                        if( input == 0xD834 ) {
                            goto _117;
                        } else if( input < 0x110000 ) {
                            goto _125;
                        }
                    }
                }
            }
        }
    }
    goto _128;
_113:

    ++(me->buffer._input_p);
    goto INIT_STATE_TRANSITION_BLOCK;

    __quex_assert_no_passage();
_115:
    __quex_debug_state(115);
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    last_acceptance                = QUEX_LABEL(129);
    last_acceptance_input_position = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer);
    if( input < 0x1F46) {
        if( input < 0x3D0) {
            switch( input ) {
                case 0x0:     QUEX_GOTO_RELOAD(__RELOAD_FORWARD, QUEX_LABEL(115), QUEX_LABEL(130));
                case 0x374:   
                case 0x375:   
                case 0x37A:   
                case 0x37B:   
                case 0x37C:   
                case 0x37D:   
                case 0x384:   
                case 0x385:   
                case 0x386:   
                case 0x388:   
                case 0x389:   
                case 0x38A:   
                case 0x38C:   
                case 0x38E:   
                case 0x38F:   
                case 0x390:   
                case 0x391:   
                case 0x392:   
                case 0x393:   
                case 0x394:   
                case 0x395:   
                case 0x396:   
                case 0x397:   
                case 0x398:   
                case 0x399:   
                case 0x39A:   
                case 0x39B:   
                case 0x39C:   
                case 0x39D:   
                case 0x39E:   
                case 0x39F:   
                case 0x3A0:   
                case 0x3A1:   
                case 0x3A3:   
                case 0x3A4:   
                case 0x3A5:   
                case 0x3A6:   
                case 0x3A7:   
                case 0x3A8:   
                case 0x3A9:   
                case 0x3AA:   
                case 0x3AB:   
                case 0x3AC:   
                case 0x3AD:   
                case 0x3AE:   
                case 0x3AF:   
                case 0x3B0:   
                case 0x3B1:   
                case 0x3B2:   
                case 0x3B3:   
                case 0x3B4:   
                case 0x3B5:   
                case 0x3B6:   
                case 0x3B7:   
                case 0x3B8:   
                case 0x3B9:   
                case 0x3BA:   
                case 0x3BB:   
                case 0x3BC:   
                case 0x3BD:   
                case 0x3BE:   
                case 0x3BF:   
                case 0x3C0:   
                case 0x3C1:   
                case 0x3C2:   
                case 0x3C3:   
                case 0x3C4:   
                case 0x3C5:   
                case 0x3C6:   
                case 0x3C7:   
                case 0x3C8:   
                case 0x3C9:   
                case 0x3CA:   
                case 0x3CB:   
                case 0x3CC:   
                case 0x3CD:   
                case 0x3CE:   goto _115;
            }
        } else {
            switch( input ) {
                case 0x3D0:   
                case 0x3D1:   
                case 0x3D2:   
                case 0x3D3:   
                case 0x3D4:   
                case 0x3D5:   
                case 0x3D6:   
                case 0x3D7:   
                case 0x3D8:   
                case 0x3D9:   
                case 0x3DA:   
                case 0x3DB:   
                case 0x3DC:   
                case 0x3DD:   
                case 0x3DE:   
                case 0x3DF:   
                case 0x3E0:   
                case 0x3E1:   
                case 0x3F0:   
                case 0x3F1:   
                case 0x3F2:   
                case 0x3F3:   
                case 0x3F4:   
                case 0x3F5:   
                case 0x3F6:   
                case 0x3F7:   
                case 0x3F8:   
                case 0x3F9:   
                case 0x3FA:   
                case 0x3FB:   
                case 0x3FC:   
                case 0x3FD:   
                case 0x3FE:   
                case 0x3FF:   
                case 0x1D26:  
                case 0x1D27:  
                case 0x1D28:  
                case 0x1D29:  
                case 0x1D2A:  
                case 0x1D5D:  
                case 0x1D5E:  
                case 0x1D5F:  
                case 0x1D60:  
                case 0x1D61:  
                case 0x1D66:  
                case 0x1D67:  
                case 0x1D68:  
                case 0x1D69:  
                case 0x1D6A:  
                case 0x1DBF:  
                case 0x1F00:  
                case 0x1F01:  
                case 0x1F02:  
                case 0x1F03:  
                case 0x1F04:  
                case 0x1F05:  
                case 0x1F06:  
                case 0x1F07:  
                case 0x1F08:  
                case 0x1F09:  
                case 0x1F0A:  
                case 0x1F0B:  
                case 0x1F0C:  
                case 0x1F0D:  
                case 0x1F0E:  
                case 0x1F0F:  
                case 0x1F10:  
                case 0x1F11:  
                case 0x1F12:  
                case 0x1F13:  
                case 0x1F14:  
                case 0x1F15:  
                case 0x1F18:  
                case 0x1F19:  
                case 0x1F1A:  
                case 0x1F1B:  
                case 0x1F1C:  
                case 0x1F1D:  
                case 0x1F20:  
                case 0x1F21:  
                case 0x1F22:  
                case 0x1F23:  
                case 0x1F24:  
                case 0x1F25:  
                case 0x1F26:  
                case 0x1F27:  
                case 0x1F28:  
                case 0x1F29:  
                case 0x1F2A:  
                case 0x1F2B:  
                case 0x1F2C:  
                case 0x1F2D:  
                case 0x1F2E:  
                case 0x1F2F:  
                case 0x1F30:  
                case 0x1F31:  
                case 0x1F32:  
                case 0x1F33:  
                case 0x1F34:  
                case 0x1F35:  
                case 0x1F36:  
                case 0x1F37:  
                case 0x1F38:  
                case 0x1F39:  
                case 0x1F3A:  
                case 0x1F3B:  
                case 0x1F3C:  
                case 0x1F3D:  
                case 0x1F3E:  
                case 0x1F3F:  
                case 0x1F40:  
                case 0x1F41:  
                case 0x1F42:  
                case 0x1F43:  
                case 0x1F44:  
                case 0x1F45:  goto _115;
            }
        }
    } else {
        if( input < 0x1FC5) {
            switch( input ) {
                case 0x1F48:  
                case 0x1F49:  
                case 0x1F4A:  
                case 0x1F4B:  
                case 0x1F4C:  
                case 0x1F4D:  
                case 0x1F50:  
                case 0x1F51:  
                case 0x1F52:  
                case 0x1F53:  
                case 0x1F54:  
                case 0x1F55:  
                case 0x1F56:  
                case 0x1F57:  
                case 0x1F59:  
                case 0x1F5B:  
                case 0x1F5D:  
                case 0x1F5F:  
                case 0x1F60:  
                case 0x1F61:  
                case 0x1F62:  
                case 0x1F63:  
                case 0x1F64:  
                case 0x1F65:  
                case 0x1F66:  
                case 0x1F67:  
                case 0x1F68:  
                case 0x1F69:  
                case 0x1F6A:  
                case 0x1F6B:  
                case 0x1F6C:  
                case 0x1F6D:  
                case 0x1F6E:  
                case 0x1F6F:  
                case 0x1F70:  
                case 0x1F71:  
                case 0x1F72:  
                case 0x1F73:  
                case 0x1F74:  
                case 0x1F75:  
                case 0x1F76:  
                case 0x1F77:  
                case 0x1F78:  
                case 0x1F79:  
                case 0x1F7A:  
                case 0x1F7B:  
                case 0x1F7C:  
                case 0x1F7D:  
                case 0x1F80:  
                case 0x1F81:  
                case 0x1F82:  
                case 0x1F83:  
                case 0x1F84:  
                case 0x1F85:  
                case 0x1F86:  
                case 0x1F87:  
                case 0x1F88:  
                case 0x1F89:  
                case 0x1F8A:  
                case 0x1F8B:  
                case 0x1F8C:  
                case 0x1F8D:  
                case 0x1F8E:  
                case 0x1F8F:  
                case 0x1F90:  
                case 0x1F91:  
                case 0x1F92:  
                case 0x1F93:  
                case 0x1F94:  
                case 0x1F95:  
                case 0x1F96:  
                case 0x1F97:  
                case 0x1F98:  
                case 0x1F99:  
                case 0x1F9A:  
                case 0x1F9B:  
                case 0x1F9C:  
                case 0x1F9D:  
                case 0x1F9E:  
                case 0x1F9F:  
                case 0x1FA0:  
                case 0x1FA1:  
                case 0x1FA2:  
                case 0x1FA3:  
                case 0x1FA4:  
                case 0x1FA5:  
                case 0x1FA6:  
                case 0x1FA7:  
                case 0x1FA8:  
                case 0x1FA9:  
                case 0x1FAA:  
                case 0x1FAB:  
                case 0x1FAC:  
                case 0x1FAD:  
                case 0x1FAE:  
                case 0x1FAF:  
                case 0x1FB0:  
                case 0x1FB1:  
                case 0x1FB2:  
                case 0x1FB3:  
                case 0x1FB4:  
                case 0x1FB6:  
                case 0x1FB7:  
                case 0x1FB8:  
                case 0x1FB9:  
                case 0x1FBA:  
                case 0x1FBB:  
                case 0x1FBC:  
                case 0x1FBD:  
                case 0x1FBE:  
                case 0x1FBF:  
                case 0x1FC0:  
                case 0x1FC1:  
                case 0x1FC2:  
                case 0x1FC3:  
                case 0x1FC4:  goto _115;
            }
        } else {
            switch( input ) {
                case 0x1FC6:  
                case 0x1FC7:  
                case 0x1FC8:  
                case 0x1FC9:  
                case 0x1FCA:  
                case 0x1FCB:  
                case 0x1FCC:  
                case 0x1FCD:  
                case 0x1FCE:  
                case 0x1FCF:  
                case 0x1FD0:  
                case 0x1FD1:  
                case 0x1FD2:  
                case 0x1FD3:  
                case 0x1FD6:  
                case 0x1FD7:  
                case 0x1FD8:  
                case 0x1FD9:  
                case 0x1FDA:  
                case 0x1FDB:  
                case 0x1FDD:  
                case 0x1FDE:  
                case 0x1FDF:  
                case 0x1FE0:  
                case 0x1FE1:  
                case 0x1FE2:  
                case 0x1FE3:  
                case 0x1FE4:  
                case 0x1FE5:  
                case 0x1FE6:  
                case 0x1FE7:  
                case 0x1FE8:  
                case 0x1FE9:  
                case 0x1FEA:  
                case 0x1FEB:  
                case 0x1FEC:  
                case 0x1FED:  
                case 0x1FEE:  
                case 0x1FEF:  
                case 0x1FF2:  
                case 0x1FF3:  
                case 0x1FF4:  
                case 0x1FF6:  
                case 0x1FF7:  
                case 0x1FF8:  
                case 0x1FF9:  
                case 0x1FFA:  
                case 0x1FFB:  
                case 0x1FFC:  
                case 0x1FFD:  
                case 0x1FFE:  
                case 0x2126:  goto _115;
                case 0xD800:  goto _121;
                case 0xD834:  goto _123;
            }
        }
    }
_130:
goto _129;

    __quex_assert_no_passage();
_119:
    __quex_debug_state(119);
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    switch( input ) {
        case 0x0:     QUEX_GOTO_RELOAD(__RELOAD_FORWARD, QUEX_LABEL(119), QUEX_LABEL(131));
        case 0x30:    
        case 0x31:    
        case 0x32:    
        case 0x33:    
        case 0x34:    
        case 0x35:    
        case 0x36:    
        case 0x37:    
        case 0x38:    
        case 0x39:    
        case 0x41:    
        case 0x42:    
        case 0x43:    
        case 0x44:    
        case 0x45:    
        case 0x46:    goto _119;
    }
_131:
goto _132;

    __quex_assert_no_passage();
_114:
    __quex_debug_state(114);
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    switch( input ) {
        case 0x0:     QUEX_GOTO_RELOAD(__RELOAD_FORWARD, QUEX_LABEL(114), QUEX_LABEL(133));
        case 0x30:    
        case 0x31:    
        case 0x32:    
        case 0x33:    
        case 0x34:    
        case 0x35:    
        case 0x36:    
        case 0x37:    
        case 0x38:    
        case 0x39:    
        case 0x41:    
        case 0x42:    
        case 0x43:    
        case 0x44:    
        case 0x45:    
        case 0x46:    goto _119;
    }
_133:
goto _134;

    __quex_assert_no_passage();
_117:
    __quex_debug_state(117);
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    if( input >= 0xDE46 ) {
    } else if( input >= 0xDE00 ) {
        goto _115;
    } else if( input >= 0x1 ) {
    } else {
        QUEX_GOTO_RELOAD(__RELOAD_FORWARD, QUEX_LABEL(117), QUEX_LABEL(135));
}
_135:
goto _134;

    __quex_assert_no_passage();
_121:
    __quex_debug_state(121);
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    if( input >= 0xDD8B ) {
    } else if( input >= 0xDD40 ) {
        goto _115;
    } else if( input >= 0x1 ) {
    } else {
        QUEX_GOTO_RELOAD(__RELOAD_FORWARD, QUEX_LABEL(121), QUEX_LABEL(136));
}
_136:
goto __TERMINAL_ROUTER; 

    __quex_assert_no_passage();
_122:
    __quex_debug_state(122);
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    if( input >= 0xDD8B ) {
    } else if( input >= 0xDD40 ) {
        goto _115;
    } else if( input >= 0x1 ) {
    } else {
        QUEX_GOTO_RELOAD(__RELOAD_FORWARD, QUEX_LABEL(122), QUEX_LABEL(137));
}
_137:
goto _134;

    __quex_assert_no_passage();
_123:
    __quex_debug_state(123);
    ++(me->buffer._input_p);
    input = *(me->buffer._input_p);
    if( input >= 0xDE46 ) {
    } else if( input >= 0xDE00 ) {
        goto _115;
    } else if( input >= 0x1 ) {
    } else {
        QUEX_GOTO_RELOAD(__RELOAD_FORWARD, QUEX_LABEL(123), QUEX_LABEL(138));
}
_138:
goto __TERMINAL_ROUTER; 

#   if defined(QUEX_OPTION_COMPUTED_GOTOS)
    __quex_assert_no_passage();
    /* Scenario: -- QUEX_GOTO_TERMINAL(last_acceptance) defined
     *              => required __TERMINAL_ROUTER
     *           -- all last_acceptance are 'failure' 
     *              => no routing.
     *           -- Compilation with 'QUEX_OPTION_COMPUTED_GOTOS'.
     *              => no state router required.                     
     * Then: There is no 'goto' to __TERMINAL_ROUTER and the compiler
     *       would complain about an unreferenced label. Avoid this by
     *       putting an explicit, never reached 'goto' here.               */
    goto __TERMINAL_ROUTER;
#   endif
    __quex_assert_no_passage();
__TERMINAL_ROUTER:
    __quex_debug("terminal router");
    /*  if last_acceptance => goto correspondent acceptance terminal state */
    /*  else               => execute defaul action                        */
    if( last_acceptance == QUEX_LABEL(128) ) {
        goto _128; /* TERMINAL: FAILURE */
    }
    /* When a terminal router is used, the terminal is determined dynamically,
     * thus the last_acceptance_input_position **must** be set. 
     * Exception: Template States, where acceptance states of post conditions
     *            do not set the acceptance position (because its retrieved
     *            anyway from post_context_start_position[i]).               */
    if(last_acceptance_input_position != 0x0) {
        QUEX_NAME(Buffer_seek_memory_adr)(&me->buffer, last_acceptance_input_position);
    }
#   ifdef  QUEX_OPTION_COMPUTED_GOTOS
    goto *last_acceptance;
#   else
    target_state_index = last_acceptance;
    goto __STATE_ROUTER;
#   endif /* QUEX_OPTION_COMPUTED_GOTOS */

    /* (*) Terminal states _______________________________________________________
     *
     * States that implement actions of the 'winner patterns.                     */

    /* Lexeme setup: 
     *
     * There is a temporary zero stored at the end of each lexeme, if the action 
     * references to the 'Lexeme'. 'LexemeNull' provides a reference to an empty
     * zero terminated string.                                                    */

#if defined(QUEX_OPTION_ASSERTS)
#   define Lexeme       QUEX_NAME(access_Lexeme)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#   define LexemeBegin  QUEX_NAME(access_Lexeme)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#   define LexemeL      QUEX_NAME(access_LexemeL)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#   define LexemeEnd    QUEX_NAME(access_LexemeEnd)((const char*)__FILE__, (size_t)__LINE__, &me->buffer)
#else
#   define Lexeme       (me->buffer._lexeme_start_p)
#   define LexemeBegin  (me->buffer._lexeme_start_p)
#   define LexemeL      ((size_t)(me->buffer._input_p - me->buffer._lexeme_start_p))
#   define LexemeEnd    (me->buffer._input_p)
#endif

#define LexemeNull      (&QUEX_NAME(LexemeNullObject))
_125:
    __quex_debug("pre-terminal 24: .");
    ++(me->buffer._input_p);
_134:
    __quex_debug("* terminal 24:   .");

#   ifdef __QUEX_OPTION_COUNTER
    __QUEX_IF_COUNT_LINES(self.counter._line_number_at_begin     = self.counter._line_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_begin = self.counter._column_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 1);
    __QUEX_ASSERT_COUNTER_CONSISTENCY(&self.counter);
    __quex_debug_counter();
#   endif
    {

#   line 20 "greek-other.qx"
QUEX_NAME_TOKEN(take_text)(self_write_token_p(), &self, self.buffer._lexeme_start_p, self.buffer._input_p);
self_send(TKN_UNKNOWN);
QUEX_SETTING_AFTER_SEND_CONTINUE_OR_RETURN();

#   line 1188 "UTF16Lex.c"

    }
    goto __REENTRY_PREPARATION;
_132:
    __quex_debug("* terminal 18:   {NUMBER}");

#   ifdef __QUEX_OPTION_COUNTER
    __QUEX_IF_COUNT_LINES(self.counter._line_number_at_begin     = self.counter._line_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_begin = self.counter._column_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end +=     ((size_t)(self.buffer._input_p - self.buffer._lexeme_start_p)));
    __QUEX_ASSERT_COUNTER_CONSISTENCY(&self.counter);
    __quex_debug_counter();
#   endif
    {

#   line 18 "greek-other.qx"
QUEX_NAME_TOKEN(take_text)(self_write_token_p(), &self, self.buffer._lexeme_start_p, self.buffer._input_p);
self_send(TKN_NUMBER);
QUEX_SETTING_AFTER_SEND_CONTINUE_OR_RETURN();

#   line 1209 "UTF16Lex.c"

    }
    goto __REENTRY_PREPARATION;
_124:
    __quex_debug("pre-terminal 27: [ \\t\\n]");
    ++(me->buffer._input_p);
    __quex_debug("* terminal 27:   [ \\t\\n]");

#   ifdef __QUEX_OPTION_COUNTER
    __QUEX_IF_COUNT_LINES(self.counter._line_number_at_begin     = self.counter._line_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_begin = self.counter._column_number_at_end);
    QUEX_NAME(Counter_count)(&self.counter, self.buffer._lexeme_start_p, self.buffer._input_p);
    __QUEX_ASSERT_COUNTER_CONSISTENCY(&self.counter);
    __quex_debug_counter();
#   endif
    {

#   line 21 "greek-other.qx"
QUEX_NAME_TOKEN(take_text)(self_write_token_p(), &self, self.buffer._lexeme_start_p, self.buffer._input_p);
self_send(TKN_WHITE);
QUEX_SETTING_AFTER_SEND_CONTINUE_OR_RETURN();

#   line 1232 "UTF16Lex.c"

    }
    goto __REENTRY_PREPARATION;
_126:
    __quex_debug("pre-terminal 21: double-quote:double-quote");
    ++(me->buffer._input_p);
    __quex_debug("* terminal 21:   double-quote:double-quote");

#   ifdef __QUEX_OPTION_COUNTER
    __QUEX_IF_COUNT_LINES(self.counter._line_number_at_begin     = self.counter._line_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_begin = self.counter._column_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 1);
    __QUEX_ASSERT_COUNTER_CONSISTENCY(&self.counter);
    __quex_debug_counter();
#   endif
    {

#   line 19 "greek-other.qx"
QUEX_NAME_TOKEN(take_text)(self_write_token_p(), &self, self.buffer._lexeme_start_p, self.buffer._input_p);
self_send(TKN_COLON);
QUEX_SETTING_AFTER_SEND_CONTINUE_OR_RETURN();

#   line 1255 "UTF16Lex.c"

    }
    goto __REENTRY_PREPARATION;
_129:
    __quex_debug("* terminal 15:   {WORD}");

#   ifdef __QUEX_OPTION_COUNTER
    __QUEX_IF_COUNT_LINES(self.counter._line_number_at_begin     = self.counter._line_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_begin = self.counter._column_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end +=     ((size_t)(self.buffer._input_p - self.buffer._lexeme_start_p)));
    __QUEX_ASSERT_COUNTER_CONSISTENCY(&self.counter);
    __quex_debug_counter();
#   endif
    {

#   line 17 "greek-other.qx"
QUEX_NAME_TOKEN(take_text)(self_write_token_p(), &self, self.buffer._lexeme_start_p, self.buffer._input_p);
self_send(TKN_WORD);
QUEX_SETTING_AFTER_SEND_CONTINUE_OR_RETURN();

#   line 1276 "UTF16Lex.c"

    }
    goto __REENTRY_PREPARATION;

_143: /* TERMINAL: END_OF_STREAM */

#   ifdef __QUEX_OPTION_COUNTER
    __QUEX_IF_COUNT_LINES(self.counter._line_number_at_begin     = self.counter._line_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_begin = self.counter._column_number_at_end);
    __quex_debug_counter();
#   endif
    {

#   line 16 "greek-other.qx"
QUEX_NAME_TOKEN(take_text)(self_write_token_p(), &self, LexemeNull, LexemeNull);
self_send(TKN_TERMINATION);

#   line 1294 "UTF16Lex.c"

    }
     /* End of Stream causes a return from the lexical analyzer, so that no
      * tokens can be filled after the termination token.                    */
     RETURN;          

_128: /* TERMINAL: FAILURE */
me->buffer._input_p = me->buffer._lexeme_start_p;
if(QUEX_NAME(Buffer_is_end_of_file)(&me->buffer)) {

    /* Next increment will stop on EOF character. */
}

else {
    /* Step over nomatching character */
    ++(me->buffer._input_p);
}


#   ifdef __QUEX_OPTION_COUNTER
    __QUEX_IF_COUNT_LINES(self.counter._line_number_at_begin     = self.counter._line_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_begin = self.counter._column_number_at_end);
    QUEX_NAME(Counter_count)(&self.counter, self.buffer._lexeme_start_p, self.buffer._input_p);
    __quex_debug_counter();
#   endif
    {
QUEX_ERROR_EXIT("\n    Match failure in mode 'X'.\n"
                "    No 'on_failure' section provided for this mode.\n"
                "    Proposal: Define 'on_failure' and analyze 'Lexeme'.\n");

    }
     goto __REENTRY_PREPARATION;

#undef Lexeme
#undef LexemeBegin
#undef LexemeEnd
#undef LexemeNull
#undef LexemeL

__REENTRY_PREPARATION:
    /* (*) Common point for **restarting** lexical analysis.
     *     at each time when CONTINUE is called at the end of a pattern. */
    
#   ifndef __QUEX_OPTION_PLAIN_ANALYZER_OBJECT
#   ifdef  QUEX_OPTION_TOKEN_POLICY_QUEUE
    if( QUEX_NAME(TokenQueue_is_full)(&self._token_queue) ) RETURN;
#   else
    if( self_token_get_id() != __QUEX_SETTING_TOKEN_ID_UNINITIALIZED) RETURN;
#   endif
#   endif

    last_acceptance = QUEX_LABEL(128); /* TERMINAL: FAILURE */


    /* Post context positions do not have to be reset or initialized. If a state
     * is reached which is associated with 'end of post context' it is clear what
     * post context is meant. This results from the ways the state machine is 
     * constructed. A post context positions live time looks like the following:
     *
     * (1)   unitialized (don't care)
     * (1.b) on buffer reload it may, or may not be adapted (don't care)
     * (2)   when a post context begin state is passed, the it is **SET** (now: take care)
     * (2.b) on buffer reload it **is adapted**.
     * (3)   when a terminal state of the post context is reached (which can only be reached
     *       for that particular post context, then the post context position is used
     *       to reset the input position.                                              */

    /*  If a mode change happened, then the function must first return and
     *  indicate that another mode function is to be called. At this point, 
     *  we to force a 'return' on a mode change. 
     *
     *  Pseudo Code: if( previous_mode != current_mode ) {
     *                   return 0;
     *               }
     *
     *  When the analyzer returns, the caller function has to watch if a mode change
     *  occured. If not it can call this function again.                               */
#   if    defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE)        || defined(QUEX_OPTION_ASSERTS)
    if( me->DEBUG_analyzer_function_at_entry != me->current_analyzer_function ) 
#   endif
    { 
#       if defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE)
        self_token_set_id(__QUEX_SETTING_TOKEN_ID_UNINITIALIZED);
        RETURN;
#       elif defined(QUEX_OPTION_ASSERTS)
        QUEX_ERROR_EXIT("Mode change without immediate return from the lexical analyzer.");
#       endif
    }

    goto __REENTRY;

    __quex_assert_no_passage();
__RELOAD_FORWARD:
    __quex_debug("__RELOAD_FORWARD");

    __quex_assert(input == QUEX_SETTING_BUFFER_LIMIT_CODE);
    if( me->buffer._memory._end_of_file_p == 0x0 ) {
        __quex_debug_reload_before();
        QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,
                                               post_context_start_position, PostContextStartPositionN);
        __quex_debug_reload_after();
        QUEX_GOTO_STATE(target_state_index);
    }
    __quex_debug("reload impossible");
    QUEX_GOTO_STATE(target_state_else_index);

    __quex_assert_no_passage();
__RELOAD_INIT_STATE:
    __quex_debug("__RELOAD_INIT_STATE");

    __quex_assert(input == QUEX_SETTING_BUFFER_LIMIT_CODE);
    if( me->buffer._memory._end_of_file_p == 0x0 ) {
        __quex_debug_reload_before();
        QUEX_NAME(buffer_reload_forward_LA_PC)(&me->buffer, &last_acceptance_input_position,
                                               post_context_start_position, PostContextStartPositionN);
        __quex_debug_reload_after();
        goto _113; /* Init state entry */
    }
    goto _143;  /* End of stream    */
#   ifndef QUEX_OPTION_COMPUTED_GOTOS
    __quex_assert_no_passage();
__STATE_ROUTER:
    switch( target_state_index ) {
        case 114: { goto _114; }
        case 115: { goto _115; }
        case 117: { goto _117; }
        case 119: { goto _119; }
        case 121: { goto _121; }
        case 122: { goto _122; }
        case 123: { goto _123; }
        case 129: { goto _129; }
        case 130: { goto _130; }
        case 131: { goto _131; }
        case 133: { goto _133; }
        case 135: { goto _135; }
        case 136: { goto _136; }
        case 137: { goto _137; }
        case 138: { goto _138; }

        default:
            __QUEX_STD_fprintf(stderr, "State router: index = %i\n", (int)target_state_index);
            QUEX_ERROR_EXIT("State router: unknown index.");
    }
#   endif /* QUEX_OPTION_COMPUTED_GOTOS */

    /* Prevent compiler warning 'unused variable': use variables once in a part of the code*/
    /* that is never reached (and deleted by the compiler anyway).*/
    (void)QUEX_NAME(LexemeNullObject);
    (void)QUEX_NAME_TOKEN(DumpedTokenIdObject);
    QUEX_ERROR_EXIT("Unreachable code has been reached.\n");
#   undef X
#   undef self
}
#include <quex/code_base/temporary_macros_off>
QUEX_NAMESPACE_MAIN_CLOSE


QUEX_NAMESPACE_TOKEN_OPEN

const char*
QUEX_NAME_TOKEN(map_id_to_name)(const QUEX_TYPE_TOKEN_ID TokenID)
{
   static char  error_string[64];
   static const char  uninitialized_string[] = "<UNINITIALIZED>";
   static const char  termination_string[]   = "<TERMINATION>";
#  if defined(QUEX_OPTION_INDENTATION_TRIGGER)
   static const char  indent_string[]        = "<INDENT>";
   static const char  dedent_string[]        = "<DEDENT>";
   static const char  nodent_string[]        = "<NODENT>";
#  endif
   static const char  token_id_str_COLON[]         = "COLON";
   static const char  token_id_str_NUMBER[]        = "NUMBER";
   static const char  token_id_str_UNKNOWN[]       = "UNKNOWN";
   static const char  token_id_str_WHITE[]         = "WHITE";
   static const char  token_id_str_WORD[]          = "WORD";
       

   /* NOTE: This implementation works only for token id types that are 
    *       some type of integer or enum. In case an alien type is to
    *       used, this function needs to be redefined.                  */
   switch( TokenID ) {
   default: {
       __QUEX_STD_sprintf(error_string, "<UNKNOWN TOKEN-ID: %i>", (int)TokenID);
       return error_string;
   }
   case __QUEX_SETTING_TOKEN_ID_TERMINATION:       return termination_string;
   case __QUEX_SETTING_TOKEN_ID_UNINITIALIZED:     return uninitialized_string;
#  if defined(QUEX_OPTION_INDENTATION_TRIGGER)
   case __QUEX_SETTING_TOKEN_ID_INDENT:     return indent_string;
   case __QUEX_SETTING_TOKEN_ID_DEDENT:     return dedent_string;
   case __QUEX_SETTING_TOKEN_ID_NODENT:     return nodent_string;
#  endif
   case TKN_COLON:         return token_id_str_COLON;
   case TKN_NUMBER:        return token_id_str_NUMBER;
   case TKN_UNKNOWN:       return token_id_str_UNKNOWN;
   case TKN_WHITE:         return token_id_str_WHITE;
   case TKN_WORD:          return token_id_str_WORD;

   }
}

QUEX_NAMESPACE_TOKEN_CLOSE

#include <quex/code_base/temporary_macros_on>

QUEX_NAMESPACE_MAIN_OPEN

#ifndef __QUEX_OPTION_PLAIN_C
TEMPLATE_IN(InputHandleT)
#endif
void
QUEX_NAME(constructor_core)(QUEX_TYPE_ANALYZER*    me,
                            InputHandleT*          input_handle, 
                            const char*            CharacterEncodingName,
                            bool                   ByteOrderReversionF,
                            QUEX_TYPE_CHARACTER*   BufferMemory,    
                            size_t                 BufferMemorySize,
                            QUEX_TYPE_CHARACTER*   BufferEndOfFileP)
{
    __quex_assert(QUEX_NAME(ModeID_X) < 1);

     QUEX_NAME(X).id   = QUEX_NAME(ModeID_X);
     QUEX_NAME(X).name = "X";
     QUEX_NAME(X).analyzer_function = QUEX_NAME(X_analyzer_function);
#    if      defined(QUEX_OPTION_INDENTATION_TRIGGER) \
        && ! defined(QUEX_OPTION_INDENTATION_DEFAULT_HANDLER)
     QUEX_NAME(X).on_indentation = QUEX_NAME(Mode_on_indentation_null_function);
#    endif
     QUEX_NAME(X).on_entry       = QUEX_NAME(Mode_on_entry_exit_null_function);
     QUEX_NAME(X).on_exit        = QUEX_NAME(Mode_on_entry_exit_null_function);
#    if      defined(QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK)
     QUEX_NAME(X).has_base       = QUEX_NAME(X_has_base);
     QUEX_NAME(X).has_entry_from = QUEX_NAME(X_has_entry_from);
     QUEX_NAME(X).has_exit_to    = QUEX_NAME(X_has_exit_to);
#    endif
        me->mode_db[QUEX_NAME(ModeID_X)] = &(QUEX_NAME(X));


    QUEX_NAME(construct_basic)(me, input_handle,
                               BufferMemory, BufferMemorySize, BufferEndOfFileP,
                               CharacterEncodingName, 
                               QUEX_SETTING_TRANSLATION_BUFFER_SIZE,
                               ByteOrderReversionF);

    me->__current_mode_p = 0x0; /* REQUIRED, for mode transition check */
    QUEX_NAME(set_mode_brutally_by_id)(me, __QUEX_SETTING_INITIAL_LEXER_MODE_ID);

#define self  (*(QUEX_TYPE_DERIVED_ANALYZER*)me)
/* START: User's constructor extensions _______________________________________*/

/* END: _______________________________________________________________________*/
#undef self
}


#ifdef QUEX_OPTION_INCLUDE_STACK

#ifndef __QUEX_OPTION_PLAIN_C
TEMPLATE_IN(InputHandleT)
#endif
QUEX_NAME(Memento)*
QUEX_NAME(memento_pack)(QUEX_TYPE_ANALYZER*   me, 
                        QUEX_TYPE_CHARACTER*  InputName, 
                        InputHandleT**        input_handle)
{
#   define self  (*me)
    QUEX_NAME(Memento)* memento = QUEX_NAME(MemoryManager_Memento_allocate)();
    
    (void)InputName;
    (void)input_handle;

#   ifndef __QUEX_OPTION_PLAIN_C
    /* Use placement 'new' for explicit call of constructor. 
     * Necessary in C++: Trigger call to constructor for user defined members.   */
    new ((void*)memento) QUEX_NAME(Memento);
#   endif

    memento->_parent_memento                  = self._parent_memento;
    memento->buffer                           = self.buffer;
    memento->__current_mode_p                 = self.__current_mode_p; 
    memento->current_analyzer_function        = self.current_analyzer_function;
#   if    defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE) \
       || defined(QUEX_OPTION_ASSERTS)
    memento->DEBUG_analyzer_function_at_entry = self.DEBUG_analyzer_function_at_entry;
#   endif
#   ifdef __QUEX_OPTION_COUNTER
    memento->counter                          = self.counter;
#   endif
#   ifdef QUEX_OPTION_STRING_ACCUMULATOR
    memento->accumulator                      = self.accumulator;
#   endif
    memento->__file_handle_allocated_by_constructor = self.__file_handle_allocated_by_constructor;

    /* Deriberately not subject to include handling:
     *    -- Mode stack.
     *    -- Token and token queues.
     *    -- Post categorizer.                                                 */

#   ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
    /* QuexTokenQueueRemainder_restore(&memento->token_queue_remainder, &self._token_queue); */
#   endif

/* START: User's memento 'pack' _______________________________________________*/

/* END: _______________________________________________________________________*/

    return memento;
#   undef self
}

#ifndef __QUEX_OPTION_PLAIN_C
QUEX_INLINE 
#endif
void
QUEX_NAME(memento_unpack)(QUEX_TYPE_ANALYZER*  me, 
                          QUEX_NAME(Memento)*  memento)
{
#   define self  (*me)
    self._parent_memento                  = memento->_parent_memento;
    self.buffer                           = memento->buffer;
    self.__current_mode_p                 = memento->__current_mode_p; 
    self.current_analyzer_function        = memento->current_analyzer_function;
#   if    defined(QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE) \
       || defined(QUEX_OPTION_ASSERTS)
    self.DEBUG_analyzer_function_at_entry = memento->DEBUG_analyzer_function_at_entry;
#   endif
#   ifdef __QUEX_OPTION_COUNTER
    self.counter                          = memento->counter;
#   endif
#   ifdef QUEX_OPTION_STRING_ACCUMULATOR
    self.accumulator                      = memento->accumulator;
#   endif
    self.__file_handle_allocated_by_constructor = memento->__file_handle_allocated_by_constructor;

#   ifdef QUEX_OPTION_TOKEN_POLICY_QUEUE
    /* QuexTokenQueueRemainder_restore(&memento->token_queue_remainder, &self._token_queue); */
#   endif

/* START: User's memento 'unpack' _____________________________________________*/

/* END: _______________________________________________________________________*/
    
#   ifndef __QUEX_OPTION_PLAIN_C
    /* Counterpart to placement new: Explicit destructor call.
     * Necessary in C++: Trigger call to destructor for user defined members.  */
    memento->~QUEX_NAME(Memento_tag)();
#   endif

    QUEX_NAME(MemoryManager_Memento_free)(memento);
#   undef self
}
#endif /* QUEX_OPTION_INCLUDE_STACK */

QUEX_NAMESPACE_MAIN_CLOSE

#include <quex/code_base/temporary_macros_off>

#if defined(__QUEX_OPTION_CONVERTER_HELPER)
#   include "quex/code_base/converter_helper/utf16.i"
#endif
#include <quex/code_base/analyzer/headers.i>


/* -*- C++ -*-   vim: set syntax=cpp: 
 * (C) 2004-2009 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY
 */
#ifndef __QUEX_INCLUDE_GUARD__TOKEN__GENERATED____QUEX____TOKEN_I
#define __QUEX_INCLUDE_GUARD__TOKEN__GENERATED____QUEX____TOKEN_I

#include <quex/code_base/definitions>

extern QUEX_TYPE_CHARACTER  QUEX_NAME(LexemeNullObject);

QUEX_INLINE void 
QUEX_NAME_TOKEN(_set)(QUEX_TYPE_TOKEN*         __this, 
                      const QUEX_TYPE_TOKEN_ID ID) 
{ __this->_id = ID; }

QUEX_INLINE const char*    
QUEX_NAME_TOKEN(map_id_to_name)(QUEX_TYPE_TOKEN_ID);

QUEX_INLINE void 
QUEX_NAME_TOKEN(construct)(QUEX_TYPE_TOKEN* __this)
{
#   define self (*__this)
#   define LexemeNull  &QUEX_NAME(LexemeNullObject)
    (void)__this;

#   line 55 "/home/fschaef/prj/quex/trunk/quex/code_base/token/CDefault.qx"

       self.number = 0;
       self.text   = LexemeNull;
   

#   line 1690 "UTF16Lex.c"

#   undef  LexemeNull
#   undef  self
}

QUEX_INLINE void 
QUEX_NAME_TOKEN(copy_construct)(QUEX_TYPE_TOKEN*       __this, 
                                const QUEX_TYPE_TOKEN* __That)
{
    QUEX_NAME_TOKEN(construct)(__this);
    QUEX_NAME_TOKEN(copy)(__this, __That);
}

QUEX_INLINE void 
QUEX_NAME_TOKEN(destruct)(QUEX_TYPE_TOKEN* __this)
{
#   define self (*__this)
#   define LexemeNull  &QUEX_NAME(LexemeNullObject)
    (void)__this;

#   line 60 "/home/fschaef/prj/quex/trunk/quex/code_base/token/CDefault.qx"

       if( self.text != LexemeNull ) {
           QUEX_NAME(MemoryManager_Text_free)((QUEX_TYPE_CHARACTER*)self.text);
           self.text = LexemeNull;
       }
   

#   line 1719 "UTF16Lex.c"

#   undef  LexemeNull
#   undef  self
}

QUEX_INLINE void
QUEX_NAME_TOKEN(copy)(QUEX_TYPE_TOKEN*       __this, 
                      const QUEX_TYPE_TOKEN* __That)
{
#   define self  (*__this)
#   define Other (*__That)
#   define LexemeNull  &QUEX_NAME(LexemeNullObject)
    (void)__this;
    (void)__That;

#   line 67 "/home/fschaef/prj/quex/trunk/quex/code_base/token/CDefault.qx"

        self._id  = Other._id;

        if( self.text != LexemeNull ) {
            QUEX_NAME(MemoryManager_Text_free)((QUEX_TYPE_CHARACTER*)self.text);
        }
        if( Other.text != LexemeNull ) {
            self.text = QUEX_NAME(MemoryManager_Text_allocate)(
                                    sizeof(QUEX_TYPE_CHARACTER) 
                                  * (QUEX_NAME(strlen)(Other.text) + 1));
            __QUEX_STD_memcpy((void*)self.text, (void*)Other.text, 
                                sizeof(QUEX_TYPE_CHARACTER) 
                              * (QUEX_NAME(strlen)(Other.text) + 1));
        }
        self.number = Other.number;
    #   ifdef     QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN
    #       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
            self._line_n   = Other._line_n;
    #       endif
    #       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
            self._column_n = Other._column_n;
    #       endif
    #   endif
   

#   line 1761 "UTF16Lex.c"

#   undef  LexemeNull
#   undef  Other
#   undef  self
    /* If the user even misses to copy the token id, then there's
     * something seriously wrong.                                 */
    __quex_assert(__this->_id == __That->_id);
#ifdef     QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN
#   ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
    __quex_assert(__this->_line_n == __That->_line_n);
#   endif
#   ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
    __quex_assert(__this->_column_n == __That->_column_n);
#   endif
#endif
}


QUEX_INLINE bool 
QUEX_NAME_TOKEN(take_text)(QUEX_TYPE_TOKEN*           __this, 
                           QUEX_TYPE_ANALYZER*        __analyzer, 
                           const QUEX_TYPE_CHARACTER* Begin, const QUEX_TYPE_CHARACTER* End)
{
#   define self       (*__this)
#   define analyzer   (*__analyzer)
#   ifdef  LexemeNull
#   error  "Error LexemeNull shall not be defined here."
#   endif
#   define LexemeNull  &QUEX_NAME(LexemeNullObject)
    (void)__this;
    (void)__analyzer;
    (void)Begin;
    (void)End;

#   line 92 "/home/fschaef/prj/quex/trunk/quex/code_base/token/CDefault.qx"


#       if 0
        /* Hint for debug: To check take_text change "#if 0" to "#if 1" */
        {
            const QUEX_TYPE_CHARACTER* it = 0x0;
            printf("previous:  '");
            if( self.text != LexemeNull ) {
                for(it = self.text; *it ; ++it) printf("%04X.", (int)*it);
                printf("%04X.", (int)*it);
            }
            printf("'\n");
            printf("take_text: '");
            for(it = Begin; it != End; ++it) printf("%04X.", (int)*it);
            printf("%04X.", (int)*it);
            printf("'\n");
        }
#       endif


        if( self.text != LexemeNull ) {
            QUEX_NAME(MemoryManager_Text_free)((QUEX_TYPE_CHARACTER*)self.text);
        }
        if( Begin != LexemeNull ) {
            self.text = QUEX_NAME(MemoryManager_Text_allocate)(
                              sizeof(QUEX_TYPE_CHARACTER) * (size_t)(End - Begin + 1));
            __QUEX_STD_memcpy((void*)self.text, (void*)Begin, 
                              sizeof(QUEX_TYPE_CHARACTER) * (size_t)(End - Begin));
            /* The string is not necessarily zero terminated, so terminate it here. */
            *((QUEX_TYPE_CHARACTER*)(self.text + (End - Begin))) = (QUEX_TYPE_CHARACTER)0;
        } else {
            self.text = LexemeNull;
        }

#       if 0
        /* Hint for debug: To check take_text change "#if 0" to "#if 1" */
        {
            const QUEX_TYPE_CHARACTER* it = 0x0;
            printf("after:     '");
            if( self.text != LexemeNull ) { 
                for(it = self.text; *it ; ++it) printf("%04X.", (int)*it);
                printf("%04X.", (int)*it);
            }
            printf("'\n");
        }
#       endif

        /* This token copied the text from the chunk into the string, 
         * so we do not claim owneship over it.                       */
        return false;
   

#   line 1849 "UTF16Lex.c"

#   undef  LexemeNull
#   undef  analyzer
#   undef  self
}

#ifdef QUEX_OPTION_TOKEN_REPETITION_SUPPORT
QUEX_INLINE size_t 
QUEX_NAME_TOKEN(repetition_n_get)(QUEX_TYPE_TOKEN* __this)
{
#   define self        (*__this)
#   define LexemeNull  &QUEX_NAME(LexemeNullObject)
    (void)__this;
    
#   line 153 "/home/fschaef/prj/quex/trunk/quex/code_base/token/CDefault.qx"

       return self.number;
   

#   line 1869 "UTF16Lex.c"

#   undef  LexemeNull
#   undef  self
}

QUEX_INLINE void 
QUEX_NAME_TOKEN(repetition_n_set)(QUEX_TYPE_TOKEN* __this, size_t N)
{
#   define self        (*__this)
#   define LexemeNull  &QUEX_NAME(LexemeNullObject)
    (void)__this;
    (void)N;
    
#   line 149 "/home/fschaef/prj/quex/trunk/quex/code_base/token/CDefault.qx"

       self.number = N;
   

#   line 1888 "UTF16Lex.c"

#   undef  LexemeNull
#   undef  self
}
#endif /* QUEX_OPTION_TOKEN_REPETITION_SUPPORT */


#   line 157 "/home/fschaef/prj/quex/trunk/quex/code_base/token/CDefault.qx"

        const char* 
        QUEX_NAME_TOKEN(get_string)(const QUEX_TYPE_TOKEN*  me, 
                                    char*                   buffer, 
                                    size_t                  BufferSize) 
        {
            const char*  token_type_str = QUEX_NAME_TOKEN(map_id_to_name)(me->_id);
            const char*  BufferEnd  = buffer + BufferSize;
            const char*  iterator   = 0;
            char*        writerator = 0;

            /* Token Type */
            iterator = token_type_str;
            writerator = buffer; 
            while( (*iterator) && writerator != BufferEnd ) {
                *writerator++ = *iterator++;
            }

            /* Opening Quote */
            if( BufferEnd - writerator > 2 ) {
                *writerator++ = ' ';
                *writerator++ = '\'';
            }

            /* The String */
            QUEX_NAME_TOKEN(pretty_char_text)(me, writerator, (size_t)(BufferEnd - writerator));

            while( *writerator ) {
                ++writerator;
            }

            /* Closing Quote */
            if( BufferEnd - writerator > 1 ) {
                *writerator++ = '\'';
            }
            *writerator = '\0';
            return buffer;
        }

        const char* 
        QUEX_NAME_TOKEN(pretty_char_text)(const QUEX_TYPE_TOKEN*  me, 
                                          char*                   buffer, 
                                          size_t                  BufferSize) 
        {
            const QUEX_TYPE_CHARACTER*  source    = me->text;
            char*                       drain     = buffer;
            const char*                 DrainEnd  = buffer + BufferSize;
#           if defined(__QUEX_OPTION_CONVERTER_HELPER)
            const QUEX_TYPE_CHARACTER*  SourceEnd = me->text + (size_t)(QUEX_NAME(strlen)(source)) + 1;

            __QUEX_CONVERTER_STRING(QUEX_SETTING_CODEC, char)(&source, SourceEnd, &drain, DrainEnd);
#           else
            (void)me;
            /* Converter helpers are only disabled automatically, if ASCII (Unicode in 0-FF)
             * is used and the character size is 1.                                          */
            __quex_assert(sizeof(QUEX_TYPE_CHARACTER) == 1);
            while( *source && drain != DrainEnd ) {
                *drain++ = (char)(*source++);
            }
            if( drain != DrainEnd ) {
                *drain = '\0';
            } 
#           endif
            return buffer;
        }

#       if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
        const wchar_t* 
        QUEX_NAME_TOKEN(pretty_wchar_text)(const QUEX_TYPE_TOKEN*  me, 
                                           wchar_t*                buffer, 
                                           size_t                  BufferSize) 
        {
            wchar_t*                    drain     = buffer;
            const wchar_t*              DrainEnd  = buffer + (ptrdiff_t)BufferSize;
            const QUEX_TYPE_CHARACTER*  source    = me->text;
#           if defined(__QUEX_OPTION_CONVERTER_HELPER)
            const QUEX_TYPE_CHARACTER*  SourceEnd = me->text + (ptrdiff_t)(QUEX_NAME(strlen)(source)) + 1;

            __QUEX_CONVERTER_STRING(QUEX_SETTING_CODEC, wchar)(&source, SourceEnd, &drain, DrainEnd);
#           else
            /* Converter helpers are only disabled automatically, if ASCII (Unicode in 0-FF)
             * is used and the character size is 1.                                          */
            __quex_assert(sizeof(QUEX_TYPE_CHARACTER) == 1);

            while( *source && drain != DrainEnd ) {
                *drain++ = (wchar_t)(*source++);
            }
            if( drain != DrainEnd ) {
                *drain = L'\0';
            } 
#           endif
            return buffer;
        }
#       endif
   

#   line 1993 "UTF16Lex.c"


#endif /* __QUEX_INCLUDE_GUARD__TOKEN__GENERATED____QUEX____TOKEN_I */

