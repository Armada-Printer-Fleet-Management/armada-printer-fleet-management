import { createApiClient } from '@armada/api-client';
import type { LegalDocument } from '@armada/api-client/gen/common/v1/legal_document_pb';
import { OrganizationInfoSchema } from '@armada/api-client/gen/common/v1/organization_info_pb';
import { read } from '@armada/organization-info';
import { LegalAgreementGate } from '@armada/ui-kit';
import { type ReactNode, useCallback } from 'react';
import texts from 'virtual:legal-documents';

import { tempUserId } from './temp-user-id';

const { agreements } = createApiClient();
const { title } = read(OrganizationInfoSchema);

/** Renders the app once the user has accepted every current legal document. */
export function AgreementGate({ children }: { children: ReactNode }) {
  const loadOutstanding = useCallback(async () => {
    const response = await agreements.listOutstandingLegalDocuments({
      userId: { value: tempUserId() },
    });
    return response.legalDocuments;
  }, []);

  const accept = useCallback(async (document: LegalDocument) => {
    await agreements.acceptAgreement({
      userId: { value: tempUserId() },
      kind: document.kind,
      effectiveDate: document.effectiveDate,
    });
  }, []);

  return (
    <LegalAgreementGate
      applicationTitle={title}
      texts={texts}
      loadOutstanding={loadOutstanding}
      accept={accept}
    >
      {children}
    </LegalAgreementGate>
  );
}
