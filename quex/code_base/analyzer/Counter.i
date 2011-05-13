#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER_I

#include <quex/code_base/definitions>
#include <quex/code_base/analyzer/asserts>
#include <quex/code_base/analyzer/Counter>

QUEX_NAMESPACE_MAIN_OPEN

    QUEX_INLINE void
    QUEX_NAME(Counter_init)(QUEX_NAME(Counter)* me)
    {
        __QUEX_IF_COUNT_LINES(me->_line_number_at_begin = (size_t)0);
        __QUEX_IF_COUNT_LINES(me->_line_number_at_end   = (size_t)1);
        __QUEX_IF_COUNT_COLUMNS(me->_column_number_at_begin = (size_t)0);
        __QUEX_IF_COUNT_COLUMNS(me->_column_number_at_end   = (size_t)1); 
	    __QUEX_IF_COUNT_INDENTATION(QUEX_NAME(IndentationStack_init)(&me->_indentation_stack));
    }

    QUEX_INLINE void
    QUEX_NAME(Counter_construct)(QUEX_NAME(Counter)* me)
    { 
        /* Set all to '0xFF' in order to catch easily a lack of initialization. */
        __QUEX_IF_ASSERTS(memset((void*)me, 0xFF, sizeof(QUEX_NAME(Counter))));

        QUEX_NAME(Counter_init)((QUEX_NAME(Counter)*)me); 
    }

    QUEX_INLINE void
    QUEX_NAME(Counter_reset)(QUEX_NAME(Counter)* me)
    {
        QUEX_NAME(Counter_init)((QUEX_NAME(Counter)*)me);
    }

    QUEX_INLINE void    
    QUEX_NAME(Counter_count)(QUEX_NAME(Counter)* me, 
                             QUEX_TYPE_CHARACTER* Begin, QUEX_TYPE_CHARACTER* End)
    /* PURPOSE:
     *   Adapts the column number and the line number according to the newlines
     *   and letters of the last line occuring in the lexeme.
     *
     * NOTE: Providing LexemeLength may spare a subtraction (End - Lexeme) in case 
     *       there is no newline in the lexeme (see below).                        */
    {
#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        QUEX_TYPE_CHARACTER* it = QUEX_NAME(Counter_count_chars_to_newline_backwards)(me, Begin, End);
        __QUEX_IF_COUNT_LINES(if( *it == '\n' ) ++(me->_line_number_at_end));
#       else
        QUEX_TYPE_CHARACTER* it = End;
#       endif

        /* The last function may have digested a newline (*it == '\n'), but then it 
         * would have increased the _line_number_at_end.                          */
        __quex_assert(it >= Begin);
        /* Investigate remaining part of the lexeme, i.e. before the last newline
         * (recall the lexeme is traced from the rear)                            */
        while( it != Begin ) {
            --it;
            if( *it == '\n' ) ++(me->_line_number_at_end); 
        }         
#       else
        QUEX_NAME(Counter_count_chars_to_newline_backwards)(me, Begin, End);
#       endif
    }

    QUEX_INLINE void  
    QUEX_NAME(Counter_count_FixNewlineN)(QUEX_NAME(Counter)*  me,
                                                   QUEX_TYPE_CHARACTER*           Lexeme,
                                                   QUEX_TYPE_CHARACTER*           LexemeEnd,
                                                   const int                      LineNIncrement) 
    {
        __quex_assert( LexemeEnd > Lexeme );

#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
        QUEX_NAME(Counter_count_chars_to_newline_backwards)(me, (QUEX_TYPE_CHARACTER*)Lexeme, 
                                                            (QUEX_TYPE_CHARACTER*)(LexemeEnd)); 
#       endif
        __QUEX_IF_COUNT_LINES(me->_line_number_at_end += (size_t)LineNIncrement);
    }


    QUEX_INLINE QUEX_TYPE_CHARACTER*
    QUEX_NAME(Counter_count_chars_to_newline_backwards)(QUEX_NAME(Counter)*   me, 
                                                        QUEX_TYPE_CHARACTER*  Begin,
                                                        QUEX_TYPE_CHARACTER*  End)
    /* RETURNS: Pointer to the first newline or the beginning of the lexeme.
     *
     * This function increases _line_number_at_end if a newline occurs and 
     * LicenseToIncrementLineCountF = true.
     *
     * NOTE: The 'license' flag shall enable the compiler to **delete** the line number counting
     *       from the following function or implemented unconditionally, since the decision
     *       is based, then on a condition of a constant (either true or false) -- once the 
     *       function has been inlined.   
     *
     * NOTE: Quex writes a call to this function only, if there **is** a potential
     *       newline in the lexeme. Otherwise, it adds the fixed pattern length
     *       or the LexemeLength directly.                                      */
    {
        QUEX_TYPE_CHARACTER* it = 0x0; 

        __quex_assert(Begin < End);  /* LexemeLength >= 1 */

        /* loop from [End] to [Begin]:
         *
         *        [Begin]xxxxxxxxxxxxxxxxxxxxxxxxxx\n
         *     \n
         *     \n xxxxxxxxxxxxxxxxxxxxxxxx[End]
         *               <---------
         *                                                */
        for(it = End - 1; *it != '\n' ; --it) {
            if( it == Begin ) {
                /* -- In case NO newline occurs, the column index is to be INCREASED 
                 *    by the length of the string -1, since counting starts at zero
                 * -- _column_number_at_begin =    _column_number_at_end 
                 *                               - LexemeLength (just take the old one) */
                __QUEX_IF_COUNT_COLUMNS(me->_column_number_at_end += (size_t)(End - Begin));
                return it;
            }
        }

        __quex_assert(End >= it);
        /* -- In case that newline occurs, the column index is equal to
         *    the number of letters from newline to end of string             */
        __QUEX_IF_COUNT_COLUMNS(me->_column_number_at_end = (size_t)(End - it));

        return it;
    }

    QUEX_INLINE void 
    QUEX_NAME(Counter_print_this)(QUEX_NAME(Counter)* me)
    {
        __QUEX_IF_COUNT_INDENTATION(size_t* iterator = 0x0);

        __QUEX_STD_printf("   Counter:\n");
#       ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
        __QUEX_STD_printf("   _line_number_at_begin = %i;\n", (int)me->_line_number_at_begin);
        __QUEX_STD_printf("   _line_number_at_end   = %i;\n", (int)me->_line_number_at_end);
#       endif
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        __QUEX_STD_printf("   _column_number_at_begin = %i;\n", (int)me->_column_number_at_begin);
        __QUEX_STD_printf("   _column_number_at_end   = %i;\n", (int)me->_column_number_at_end);
#       endif
#       ifdef  QUEX_OPTION_INDENTATION_TRIGGER
        __QUEX_STD_printf("   _indentation = %i;\n", (int)me->_indentation);
        __QUEX_STD_printf("   _indentation_stack = {");
        for(iterator = me->_indentation_stack.front; iterator != me->_indentation_stack.back + 1; ++iterator) {
            __QUEX_STD_printf("%i, ", (int)me->_indentation);
        }
        __QUEX_STD_printf("}");
#       endif
    }

#if defined(QUEX_OPTION_INDENTATION_TRIGGER)
	QUEX_INLINE void
	QUEX_NAME(IndentationStack_init)(QUEX_NAME(IndentationStack)* me)
	{
        *(me->front)   = 0;          /* first indentation at column = 0 */
        me->back       = me->front;
        me->memory_end = me->front + QUEX_SETTING_INDENTATION_STACK_SIZE;
	}
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__COUNTER_I */

