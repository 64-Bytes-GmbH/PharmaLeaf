/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './app/templates/dashboard/*.html',
    './app/templates/app/*.html',
    './node_modules/flowbite/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          "50": "#f7f7f7",
          "100": "#e1e1e1",
          "200": "#cfcfcf",
          "300": "#b1b1b1",
          "400": "#9e9e9e",
          "500": "#7e7e7e",
          "600": "#626262",
          "700": "#515151",
          "800": "#3b3b3b",
          "900": "#222222",
          "950": "#0a0a0a"
        },
      },
    },
    fontFamily: {
      'body': [
        'Inter', 
        'ui-sans-serif', 
        'system-ui', 
        '-apple-system', 
        'system-ui', 
        'Segoe UI', 
        'Roboto', 
        'Helvetica Neue', 
        'Arial', 
        'Noto Sans', 
        'sans-serif', 
        'Apple Color Emoji', 
        'Segoe UI Emoji', 
        'Segoe UI Symbol', 
        'Noto Color Emoji'
      ],
        'sans': [
        'Inter', 
        'ui-sans-serif', 
        'system-ui', 
        '-apple-system', 
        'system-ui', 
        'Segoe UI', 
        'Roboto', 
        'Helvetica Neue', 
        'Arial', 
        'Noto Sans', 
        'sans-serif', 
        'Apple Color Emoji', 
        'Segoe UI Emoji', 
        'Segoe UI Symbol', 
        'Noto Color Emoji'
      ]
    }
  },
  variants: {
    opacity: ({ after }) => after(['disabled'])
  },
  plugins: [
    require('flowbite/plugin')({
      charts: true,
    }),
  ],
}
