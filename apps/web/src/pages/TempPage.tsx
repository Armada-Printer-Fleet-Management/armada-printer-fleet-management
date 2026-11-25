import { read } from '@armada/organization-info';
import { OrganizationInfoSchema } from '@armada/api-client/gen/organization/v1/organization_info_pb';
import { AboutBox } from '@armada/ui-kit';

import {
  aboutLegalDocuments,
  aboutThirdPartyLicences,
} from '../legal/documents';
import { version } from '../lib/version';
import { TempVerticalSlice } from '../temp/TempVerticalSlice';
import { apiClient } from '../lib/api';

export function TempPage() {
  return (
    <div className="mx-auto grid max-w-2xl gap-6 p-8">
      <AboutBox
        organization={read(OrganizationInfoSchema)}
        legalDocuments={aboutLegalDocuments}
        thirdPartyLicences={aboutThirdPartyLicences}
        version={version()}
      />
      <TempVerticalSlice
        printJobs={apiClient.printJobs}
        printers={apiClient.printers}
        slicerConfiguration={apiClient.slicerConfiguration}
      />
    </div>
  );
}
