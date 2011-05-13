/* -*- C++ -*-   vim: set syntax=cpp: 
 * (C) 2004-2009 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY
 */
#ifndef __QUEX_INCLUDE_GUARD__TOKEN__GENERATED____QUEX____TOKEN
#define __QUEX_INCLUDE_GUARD__TOKEN__GENERATED____QUEX____TOKEN

#include <quex/code_base/definitions>


#   line 2 "/home/fschaef/prj/quex/trunk/quex/code_base/token/CDefault.qx"

       #include <stdio.h>
       #include <string.h>

       #include <quex/code_base/definitions>
       #include <quex/code_base/asserts>
       #include <quex/code_base/compatibility/inttypes.h>

       extern QUEX_TYPE_CHARACTER  QUEX_NAME(LexemeNullObject);

       extern const char* 
       QUEX_NAME_TOKEN(get_string)(const QUEX_TYPE_TOKEN*  me, 
                                   char*                   buffer, 
                                   size_t                  BufferSize); 

       extern const char* 
       QUEX_NAME_TOKEN(pretty_char_text)(const QUEX_TYPE_TOKEN*  me, 
                                        char*                   buffer, 
                                        size_t                  BufferSize); 

       /* The following function converts the engine's codec to utf8. */
       QUEX_NAMESPACE_MAIN_OPEN
       QUEX_INLINE void
       __QUEX_CONVERTER_STRING(QUEX_SETTING_CODEC, char)(const QUEX_TYPE_CHARACTER**  Source, 
                                                         const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                                         char**                       Drain, 
                                                         const char*                  DrainEnd);
#      if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)
       extern const wchar_t* 
       QUEX_NAME_TOKEN(pretty_wchar_text)(const QUEX_TYPE_TOKEN*  me, 
                                          wchar_t*                buffer, 
                                          size_t                  BufferSize); 

       QUEX_INLINE void
       __QUEX_CONVERTER_STRING(QUEX_SETTING_CODEC, wchar)(const QUEX_TYPE_CHARACTER**  Source, 
                                                          const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                                          wchar_t**                    Drain, 
                                                          const wchar_t*               DrainEnd);
#      endif
       QUEX_NAMESPACE_MAIN_CLOSE
   

#   line 55 "Calc_lexer-token.h"

 
typedef struct quex_Token_tag {
    QUEX_TYPE_TOKEN_ID    _id;

#   line 47 "/home/fschaef/prj/quex/trunk/quex/code_base/token/CDefault.qx"
    const QUEX_TYPE_CHARACTER* text;
#   line 48 "/home/fschaef/prj/quex/trunk/quex/code_base/token/CDefault.qx"
    size_t                     number;
#   line 65 "Calc_lexer-token.h"


#   ifdef     QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN
#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
        QUEX_TYPE_TOKEN_LINE_N    _line_n;
#       endif
#       ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
        QUEX_TYPE_TOKEN_COLUMN_N  _column_n;
#       endif
#   endif

#   line 144 "/home/fschaef/prj/quex/trunk/quex/code_base/token/CDefault.qx"

       /*
        */
   

#   line 83 "Calc_lexer-token.h"

} quex_Token;

QUEX_INLINE void QUEX_NAME_TOKEN(construct)(QUEX_TYPE_TOKEN*);
QUEX_INLINE void QUEX_NAME_TOKEN(copy_construct)(QUEX_TYPE_TOKEN*, 
                                                  const QUEX_TYPE_TOKEN*);
QUEX_INLINE void QUEX_NAME_TOKEN(copy)(QUEX_TYPE_TOKEN*, 
                                        const QUEX_TYPE_TOKEN*);
QUEX_INLINE void QUEX_NAME_TOKEN(destruct)(QUEX_TYPE_TOKEN*);

/* NOTE: Setters and getters as in the C++ version of the token class are not
 *       necessary, since the members are accessed directly.                   */

QUEX_INLINE void 
QUEX_NAME_TOKEN(_set)(QUEX_TYPE_TOKEN*         __this, 
                      const QUEX_TYPE_TOKEN_ID ID);

extern const char*  QUEX_NAME_TOKEN(map_id_to_name)(const QUEX_TYPE_TOKEN_ID);

QUEX_INLINE bool 
QUEX_NAME_TOKEN(take_text)(QUEX_TYPE_TOKEN*           __this, 
                           QUEX_TYPE_ANALYZER*        analyzer, 
                           const QUEX_TYPE_CHARACTER* Begin, const QUEX_TYPE_CHARACTER* End);

#ifdef QUEX_OPTION_TOKEN_REPETITION_SUPPORT
QUEX_INLINE size_t QUEX_NAME_TOKEN(repetition_n_get)(QUEX_TYPE_TOKEN*);
QUEX_INLINE void   QUEX_NAME_TOKEN(repetition_n_set)(QUEX_TYPE_TOKEN*, size_t);
#endif /* QUEX_OPTION_TOKEN_REPETITION_SUPPORT */


#endif /* __QUEX_INCLUDE_GUARD__TOKEN__GENERATED____QUEX____TOKEN */
