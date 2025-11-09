import Keycloak from 'keycloak-js';
import { getAuthService, getKeycloakClientId, getKeycloakRealm } from '@/config';

const keycloakConfig = {
  url: `https://${getAuthService()}`, // NOTE: for internal testing switch to http
  realm: getKeycloakRealm(),
  clientId: getKeycloakClientId(),
};

const keycloak = new Keycloak(keycloakConfig);

export default keycloak;