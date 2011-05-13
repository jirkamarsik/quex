/* -*- C++ -*-   vim: set syntax=cpp: 
 * (C) 2004-2009 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY
 */
#ifndef __QUEX_INCLUDE_GUARD__TOKEN__GENERATED__$$INCLUDE_GUARD_EXTENSION$$_I
#define __QUEX_INCLUDE_GUARD__TOKEN__GENERATED__$$INCLUDE_GUARD_EXTENSION$$_I

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
$$CONSTRUCTOR$$
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
$$DESTRUCTOR$$
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
$$COPY$$
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
$$FUNC_TAKE_TEXT$$
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
    $$TOKEN_REPETITION_N_GET$$
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
    $$TOKEN_REPETITION_N_SET$$
#   undef  LexemeNull
#   undef  self
}
#endif /* QUEX_OPTION_TOKEN_REPETITION_SUPPORT */

$$FOOTER$$

#endif /* __QUEX_INCLUDE_GUARD__TOKEN__GENERATED__$$INCLUDE_GUARD_EXTENSION$$_I */
