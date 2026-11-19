import { createApiClient, type AccessToken } from '@armada/api-client';
import { userManager } from './auth';

const accessToken: AccessToken = async () => {
  const user = await userManager.getUser();
  return user && !user.expired ? user.access_token : undefined;
};

export const apiClient = createApiClient({ accessToken });
