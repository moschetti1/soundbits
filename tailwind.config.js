/** @type {import('tailwindcss').Config} */

module.exports = {
    content: [
      './src/**/*.html',
      './node_modules/flowbite/**/*.js'
    ],
    theme: {
      fontFamily: {
        'grotesk': ['Space Grotesk'],
        'inter': ['Inter'],
        'work': ['Work Sans']
      }
    },
    plugins: [
      require('flowbite/plugin'),
      require('@tailwindcss/forms')
    ]
  }
  