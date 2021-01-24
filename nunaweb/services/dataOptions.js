export const endians = [
  {
    name: 'Little Endian',
    value: 'little'
  },
  {
    name: 'Any Endian',
    value: 'any'
  },
  {
    name: 'Big Endian',
    value: 'big'
  }
];

export const languages = [
  {
    name: 'C',
    value: 'c'
  },
  {
    name: 'C++ (coming soon)',
    value: 'c++',
    disabled: true
  },
  {
    name: 'Python (coming soon)',
    value: 'python',
    disabled: true
  }
];

export const flags = [
  {
    name: 'Enable serialization asserts',
    description: 'Instruct support header generators to generate language-specific assert statements as part of serialization routines. By default the serialization logic generated may make assumptions based on documented requirements for calling logic that could expose a system to undefined behaviour. The alternative, for langauges that do not support exception handling, is to use assertions designed to halt a program rather than execute undefined logic.',
    flag: '--enable-serialization-asserts',
    value: true
  },
  {
    name: 'Omit float serialization support',
    flag: '--omit-float-serialization-support',
    description: 'Instruct support header generators to omit support for floating point operations in serialization routines. This will result in errors if floating point types are used, however; if you are working on a platform without IEEE754 support and do not use floating point types in your message definitions this option will avoid dead code or compiler errors in generated serialization logic.',
    value: false
  }
]
