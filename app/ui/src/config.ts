// eslint-disable-next-line @typescript-eslint/no-explicit-any
let config: any = null;

export async function loadConfig() {
  const response = await fetch('/config.json');
  config = await response.json();
}

export const getAuthService = () => `${config.VITE_AUTH_HOST}:${config.VITE_AUTH_PORT}`;
export const getChatService = () => `${config.VITE_CHAT_HOST}:${config.VITE_CHAT_PORT}`;
export const getUserService = () => `${config.VITE_USER_HOST}:${config.VITE_USER_PORT}`;
export const getKeycloakRealm = () => config.VITE_KEYCLOAK_REALM;
export const getKeycloakClientId = () => config.VITE_KEYCLOAK_CLIENT_ID;