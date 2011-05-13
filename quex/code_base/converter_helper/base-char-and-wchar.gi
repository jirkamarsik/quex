#ifndef __QUEX_DRAIN_CODEC
#   error "__QUEX_DRAIN_CODEC must be defined."
#endif

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
__QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)(const __QUEX_TYPE_SOURCE**  source_pp, 
                                                const __QUEX_TYPE_SOURCE*   SourceEnd, 
                                                __QUEX_TYPE_DRAIN**         drain_pp,  
                                                const __QUEX_TYPE_DRAIN*    DrainEnd)
{
#if   __QUEX_DRAIN_CODEC == 8
    __quex_assert(sizeof(__QUEX_TYPE_DRAIN) == 1);
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(source_pp,           SourceEnd, 
                                               (uint8_t**)drain_pp, (const uint8_t*)DrainEnd);
#elif __QUEX_DRAIN_CODEC == 16
    __quex_assert(sizeof(__QUEX_TYPE_DRAIN) == 2);
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(source_pp,            SourceEnd, 
                                                (uint16_t**)drain_pp, (const uint16_t*)DrainEnd);
#elif __QUEX_DRAIN_CODEC == 32
    __quex_assert(sizeof(__QUEX_TYPE_DRAIN) == 4);
    __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(source_pp,            SourceEnd, 
                                                (uint32_t**)drain_pp, (const uint32_t*)DrainEnd);
#else
#     error "Codec of 'char' or 'wchar' must be either 'UTF8', 'UTF16' or 'UTF32' -> 8, 16, or 32. Define QUEX_SETTING_CHAR_CODEC and QUEX_SETTING_WCHAR_CODEC."
#endif
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::basic_string<__QUEX_TYPE_DRAIN>
__QUEX_CONVERTER_STRING(__QUEX_FROM, __QUEX_TO)(const std::basic_string<__QUEX_TYPE_SOURCE>& Source)
{
#if   __QUEX_DRAIN_CODEC == 8
    __quex_assert(sizeof(__QUEX_TYPE_DRAIN) == 1);
    std::basic_string<uint8_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf8)(Source);

#elif __QUEX_DRAIN_CODEC == 16
    __quex_assert(sizeof(__QUEX_TYPE_DRAIN) == 2);
    std::basic_string<uint16_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf16)(Source);

#elif __QUEX_DRAIN_CODEC == 32
    __quex_assert(sizeof(__QUEX_TYPE_DRAIN) == 4);
    std::basic_string<uint32_t> tmp = __QUEX_CONVERTER_STRING(__QUEX_FROM, utf32)(Source);
#endif
    return std::basic_string<__QUEX_TYPE_DRAIN>((__QUEX_TYPE_DRAIN*)tmp.c_str());
}
#endif

QUEX_NAMESPACE_MAIN_CLOSE

#undef __QUEX_TO
#undef __QUEX_TYPE_DRAIN
#undef __QUEX_DRAIN_CODEC
