/**
 * Tailwind CSS v4 configuration.
 *
 * In v4 the framework is CSS-first: most design-token customisation lives in
 * your main CSS file via @theme.  This JS file is only needed if you use JS
 * plugins (like tailwindcss-animate) or need to set non-CSS options.
 *
 * See https://tailwindcss.com/docs/v4-beta
 */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  plugins: [],
}
