import Keycloak from 'keycloak-js';
import { getAuthService, getKeycloakClientId, getKeycloakRealm } from '@/config';

const keycloakConfig = {
  url: `http://${getAuthService()}`,
  realm: getKeycloakRealm(),
  clientId: getKeycloakClientId(),
};

const keycloak = new Keycloak(keycloakConfig);

export default keycloak;