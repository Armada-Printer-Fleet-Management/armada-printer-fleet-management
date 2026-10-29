import { read } from '@armada/organization-info';
import { createApiClient } from '@armada/api-client';
import { OrganizationInfoSchema } from '@armada/api-client/gen/common/v1/organization_info_pb';
import { AboutBox } from '@armada/ui-kit';

import { version } from '../lib/version';
import { TempVerticalSlice } from '../temp/TempVerticalSlice';

const apiClient = createApiClient();

export function TempPage() {
  return (
    <div className="mx-auto grid max-w-2xl gap-6 p-8">
      <AboutBox
        organization={read(OrganizationInfoSchema)}
        version={version()}
      />
      <TempVerticalSlice printJobs={apiClient.printJobs} />
    </div>
  );
}
