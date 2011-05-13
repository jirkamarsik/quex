/* (C) 2010 Frank-Rene Schaefer */
QUEX_NAMESPACE_MAIN_OPEN

#ifndef    __QUEX_TO
#    error "__QUEX_TO is not defined."
#endif
#ifndef    __QUEX_TYPE_DRAIN
#    error "__QUEX_TYPE_DRAIN is not defined."
#endif

QUEX_INLINE void
__QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)(const __QUEX_TYPE_SOURCE**  source_pp, 
                                                const __QUEX_TYPE_SOURCE*   SourceEnd, 
                                                __QUEX_TYPE_DRAIN**          drain_pp,  
                                                const __QUEX_TYPE_DRAIN*     DrainEnd)
{
    const __QUEX_TYPE_SOURCE*  source_iterator; 
    __QUEX_TYPE_DRAIN*         drain_iterator;

    __quex_assert(source_pp != 0x0);
    __quex_assert(*source_pp != 0x0);
    __quex_assert(drain_pp != 0x0);
    __quex_assert(*drain_pp != 0x0);

    drain_iterator  = *drain_pp;
    source_iterator = *source_pp;

    while( 1 + 1 == 2 ) { 
        if( source_iterator == SourceEnd ) break;
        if( DrainEnd - drain_iterator < (ptrdiff_t)__QUEX_MAX_CHAR_SIZE ) break;
        __QUEX_CONVERTER_CHAR(__QUEX_FROM, __QUEX_TO)(&source_iterator, &drain_iterator);
        __quex_assert(source_iterator >  *source_pp);
        __quex_assert(source_iterator <= SourceEnd);
    }

    *drain_pp  = drain_iterator;
    *source_pp = source_iterator;
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_TYPE_DRAIN>
__QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)(const std::basic_string<__QUEX_TYPE_SOURCE>& Source)
{
    const __QUEX_TYPE_SOURCE*             source_iterator = (__QUEX_TYPE_SOURCE*)Source.c_str();
    const __QUEX_TYPE_SOURCE*             source_end      = source_iterator + Source.length();
    __QUEX_TYPE_DRAIN                     drain[__QUEX_MAX_CHAR_SIZE + 1];
    __QUEX_TYPE_DRAIN*                    drain_iterator = 0;
    std::basic_string<__QUEX_TYPE_DRAIN>  result;

    while( source_iterator != source_end ) {
        drain_iterator = drain;
        __QUEX_CONVERTER_CHAR(__QUEX_FROM, __QUEX_TO)(&source_iterator, &drain_iterator);
        __quex_assert(source_iterator >  (__QUEX_TYPE_SOURCE*)Source.c_str());
        __quex_assert(source_iterator <= source_end);
        result.append((__QUEX_TYPE_DRAIN*)drain, (size_t)(drain_iterator - drain));
    }
    return result;
}
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#undef __QUEX_TO
#undef __QUEX_TYPE_DRAIN
#undef __QUEX_MAX_CHAR_SIZE
