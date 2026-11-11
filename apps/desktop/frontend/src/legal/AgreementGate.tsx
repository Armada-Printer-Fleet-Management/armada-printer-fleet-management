import { read } from '@armada/organization-info';
import { LegalAgreementGate } from '@armada/ui-kit';
import { type ReactNode } from 'react';
import texts from 'virtual:legal-documents';

import type { LegalDocument } from '../gen/common/v1/legal_document_pb';
import { OrganizationInfoSchema } from '../gen/common/v1/organization_info_pb';
import { acceptAgreement, outstandingLegalDocuments } from '../ipc/legal';

const { title } = read(OrganizationInfoSchema);

async function loadOutstanding() {
  return (await outstandingLegalDocuments()).legalDocuments;
}

async function accept(document: LegalDocument) {
  await acceptAgreement({
    kind: document.kind,
    effectiveDate: document.effectiveDate,
  });
}

/** Renders the app once its user has accepted every current legal document. */
export function AgreementGate({ children }: { children: ReactNode }) {
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
