/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './{accounts,agro_updates,bidding,chatbot,dashboard,disputes,orders,payments,products,reviews,wishlist}/templates/**/*.html',
    './static/js/**/*.js', './chatbot/static/chatbot/**/*.js',
  ],
  safelist: ['ask-message-user', 'ask-message-assistant', 'badge', 'pill'],
  // Semantic CSS supplies the reset, shadows and visible focus. Disabling these
  // plugins prevents Tailwind's literal white/black/blue defaults leaking in.
  corePlugins: {preflight: false, boxShadow: false, ringWidth: false, ringColor: false,
    ringOpacity: false, ringOffsetColor: false, ringOffsetWidth: false},
  theme: {
    colors: {transparent: 'transparent', current: 'currentColor', inherit: 'inherit'},
    extend: {
      colors: {
        c: {900: '#06141B', 800: '#11212D', 700: '#253745', 600: '#4A5C6A', 400: '#9BA8AB', 200: '#CCD0CF'},
        page: 'var(--page)', surface: 'var(--surface)', elevated: 'var(--surface-hover)',
        content: 'var(--text)', muted: 'var(--muted)', subtle: 'var(--muted)',
        line: 'var(--border)', primary: 'var(--primary)', 'on-primary': 'var(--on-primary)',
      },
      fontFamily: {sans: ['Geist', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'ui-monospace', 'SFMono-Regular', 'monospace']},
      borderColor: {DEFAULT: 'var(--border)'},
    },
  },
  plugins: [],
};
