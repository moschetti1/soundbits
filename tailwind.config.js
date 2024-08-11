/** @type {import('tailwindcss').Config} */

module.exports = {
    content: [
      './src/**/*.html',
      './node_modules/flowbite/**/*.js'
    ],
    theme: {
      extend: {
        animation: {
          fade: 'fadeIn 0.5s ease-in-out',
        },
  
        keyframes: {
          fadeIn: {
            from: { opacity: 0 },
            to: { opacity: 1 },
          },
        },
      },
      fontFamily: {
        'grotesk': ['Space Grotesk'],
        'inter': ['Inter'],
        'work': ['Work Sans'],
        'stix': ['STIX Two Text']
      }
    },
    plugins: [
      require('flowbite/plugin'),
      require('@tailwindcss/forms'),
    ]
  }
  