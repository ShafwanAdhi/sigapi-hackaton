// Public presentation stays clean. Local simulation controls are opt-in for developers.
export const showDevelopmentDetails = import.meta.env.DEV && new URLSearchParams(window.location.search).get('dev') === '1';
