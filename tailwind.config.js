/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        // Palette premium bleu marine / jaune or
        'brand': {
          'primary': '#0D1B2A',      // Bleu marine profond (fond principal)
          'surface': '#1B263B',       // Bleu marine clair (panneaux, cartes)
          'accent': '#F0C419',        // Jaune or élégant (boutons, badges)
          'white': '#FFFFFF',         // Blanc pur
        },
        // Alias pour faciliter l'utilisation
        'navy': {
          'dark': '#0D1B2A',
          'light': '#1B263B',
        },
        'gold': {
          'DEFAULT': '#F0C419',
          'light': '#F5D547',
          'dark': '#D4A917',
        },
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(135deg, #0D1B2A 0%, #1B263B 100%)',
        'gradient-gold': 'linear-gradient(135deg, #F0C419 0%, #F5D547 100%)',
      },
      boxShadow: {
        'brand': '0 4px 20px rgba(240, 196, 25, 0.2)',
        'brand-lg': '0 10px 40px rgba(240, 196, 25, 0.3)',
      },
    },
  },
  plugins: [],
}

