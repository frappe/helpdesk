module.exports = {
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      fontSize: {
        xs: '11px',
        sm: '12px',
        base: '13px',
        lg: '14px',
        xl: '16px',
        '2xl': '18px',
        '3xl': '20px',
        '4xl': '22px',
        '5xl': '24px',
        '6xl': '26px',
        '7xl': '28px',
      },
      width: {
        112: '28rem',
        wizard: '650px',
      },
      minWidth: {
        40: '10rem',
      },
      maxHeight: {
        52: '13rem',
      },
      borderColor: (theme) => ({
        DEFAULT: theme('colors.gray.200'),
      }),
      colors: {
        brand: '#2490EF',
        'brand-100': '#f4f9ff',
        black: '#112B42',
        blue: {
          50: '#F0F8FE',
          100: '#D3E9FC',
          200: '#A7D3F9',
          300: '#7CBCF5',
          400: '#50A6F2',
          500: '#2490EF',
          600: '#1579D0',
          700: '#1366AE',
          800: '#154875',
          900: '#1A4469',
        },
        gray: {
          50: '#F9FAFA',
          100: '#F4F5F6',
          200: '#EBEEF0',
          300: '#DCE0E3',
          400: '#C0C6CC',
          500: '#98A1A9',
          600: '#687178',
          700: '#505A62',
          800: '#333C44',
          900: '#1F272E',
        },
        purple: {
          900: '#44427B',
          800: '#5552BC',
          700: '#6461D6',
          600: '#807DDE',
          500: '#928EF5',
          400: '#B7B6FC',
          300: '#D6D5F6',
          200: '#E8E8F7',
          100: '#F2F2FD',
          50: '#F8F8FC',
        },
      },
    },
    container: {
      padding: {
        xl: '5rem',
      },
    },
    screens: {
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('tailwindcss/plugin')(function ({ addUtilities, theme }) {
      addUtilities({
        '.bg-gradient-blue': {
          'background-image': `linear-gradient(180deg,#2c9af1 0%, ${theme(
            'colors.blue.500'
          )} 100%)`,
        },
      })
      addUtilities(
        {
          '.bg-gradient-none': {
            'background-image': 'none',
          },
        },
        {
          variants: ['focus', 'hover'],
        }
      )
    }),
  ],
}
