/* -*- C++ -*-   vim: set syntax=cpp: 
 * (C) 2004-2009 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY
 */
#ifndef __QUEX_INCLUDE_GUARD__TOKEN__GENERATED__$$INCLUDE_GUARD_EXTENSION$$_I
#define __QUEX_INCLUDE_GUARD__TOKEN__GENERATED__$$INCLUDE_GUARD_EXTENSION$$_I

$$NAMESPACE_OPEN$$

inline
/* NOTE: If you get an error here, then your configuration
 *       file does not declare QUEX_TYPE0_TOKEN as $$TOKEN_CLASS$$. 
 *       The following weirdly typed constructor shall break in
 *       this particular case.                                        */
$$TOKEN_CLASS$$::QUEX_TYPE0_TOKEN()
/*****************************************************/
{
#   define self (*this)
$$CONSTRUCTOR$$
#   undef  self
}

inline
$$TOKEN_CLASS$$::$$TOKEN_CLASS$$(const $$TOKEN_CLASS$$& Other)
{
   QUEX_NAME_TOKEN(copy)(this, &Other);
#  define self (*this)
$$CONSTRUCTOR$$
#  undef  self
}

inline
$$TOKEN_CLASS$$::~$$TOKEN_CLASS$$()
{
#  define self (*this)
$$DESTRUCTOR$$
#  undef  self
}

inline void
QUEX_NAME_TOKEN(construct)($$TOKEN_CLASS$$* __this)
{
    /* Explicit constructor call by 'placement new' */
    new ((void*)__this) QUEX_TYPE_TOKEN;
}

inline void
QUEX_NAME_TOKEN(destruct)($$TOKEN_CLASS$$* __this)
{
    __this->QUEX_TYPE0_TOKEN::~QUEX_TYPE0_TOKEN();  
}

inline void
QUEX_NAME_TOKEN(copy)($$TOKEN_CLASS$$* __this, const $$TOKEN_CLASS$$* __That)
{
#  define self  (*__this)
#  define Other (*__That)
    (void)__this;
    (void)__That;
$$COPY$$
#  undef Other
#  undef self
   /* If the user even misses to copy the token id, then there's
    * something seriously wrong.                                 */
   __quex_assert(__this->_id == __That->_id);
#ifdef     QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN
#  ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
   __quex_assert(__this->_line_n == __That->_line_n);
#  endif
#  ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
   __quex_assert(__this->_column_n == __That->_column_n);
#  endif
#endif
}

QUEX_INLINE bool 
QUEX_NAME_TOKEN(take_text)($$TOKEN_CLASS$$*           __this, 
                           QUEX_TYPE_ANALYZER*        __analyzer, 
                           const QUEX_TYPE_CHARACTER* Begin, 
                           const QUEX_TYPE_CHARACTER* End)
{
#  define self      (*__this)
#  define analyzer  (*__analyzer)
    (void)__this;
    (void)__analyzer;
$$FUNC_TAKE_TEXT$$
#  undef analyzer
#  undef self
}

#ifdef QUEX_OPTION_TOKEN_REPETITION_SUPPORT
QUEX_INLINE size_t 
QUEX_NAME_TOKEN(repetition_n_get)(QUEX_TYPE_TOKEN* __this)
{
#   define self      (*__this)
    (void)__this;
    $$TOKEN_REPETITION_N_GET$$
#   undef  self
}

QUEX_INLINE void 
QUEX_NAME_TOKEN(repetition_n_set)(QUEX_TYPE_TOKEN* __this, size_t N)
{
#   define self      (*__this)
    (void)__this;
    (void)N;
    $$TOKEN_REPETITION_N_SET$$
#   undef  self
}
#endif /* QUEX_OPTION_TOKEN_REPETITION_SUPPORT */

$$NAMESPACE_CLOSE$$

#endif /* __QUEX_INCLUDE_GUARD__TOKEN__GENERATED__$$INCLUDE_GUARD_EXTENSION$$_I */
