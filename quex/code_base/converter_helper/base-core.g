/* (C) 2010 Frank-Rene Schaefer */
#ifndef __QUEX_FROM
#   error "__QUEX_FROM must be defined."
#endif
#ifndef __QUEX_TO
#   error "__QUEX_TO must be defined."
#endif

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
__QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)(const __QUEX_TYPE_SOURCE**  source_pp, 
                                                const __QUEX_TYPE_SOURCE*   SourceEnd, 
                                                __QUEX_TYPE_DRAIN**         drain_pp,  
                                                const __QUEX_TYPE_DRAIN*    DrainEnd);

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_TYPE_DRAIN>
__QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)(const std::basic_string<__QUEX_TYPE_SOURCE>& Source);
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#undef __QUEX_TO
#undef __QUEX_TYPE_DRAIN
#undef __QUEX_CONVERTER_MY_STRING
