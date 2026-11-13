import { UserManager } from 'oidc-client-ts';

export const userManager = new UserManager({
  authority: `${window.location.origin}/auth/realms/armada`,
  client_id: 'armada-web',
  redirect_uri: `${window.location.origin}/signin-callback`,
  post_logout_redirect_uri: window.location.origin,
});
