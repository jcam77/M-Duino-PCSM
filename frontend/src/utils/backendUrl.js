/* global __MDUINO_DEFAULT_BACKEND_HOST__, __MDUINO_DEFAULT_BACKEND_PORT__ */
export const DEFAULT_BACKEND_HOST =
  typeof __MDUINO_DEFAULT_BACKEND_HOST__ !== 'undefined' ? __MDUINO_DEFAULT_BACKEND_HOST__ : '';
export const DEFAULT_BACKEND_PORT =
  typeof __MDUINO_DEFAULT_BACKEND_PORT__ !== 'undefined' ? __MDUINO_DEFAULT_BACKEND_PORT__ : '';

export const getBackendPort = () => {
  if (typeof window === 'undefined') return DEFAULT_BACKEND_PORT;
  const params = new URLSearchParams(window.location.search || '');
  return params.get('backendPort') || DEFAULT_BACKEND_PORT;
};

export const getBackendBaseUrl = () => `http://${DEFAULT_BACKEND_HOST}:${getBackendPort()}`;
