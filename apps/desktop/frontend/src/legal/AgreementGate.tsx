import { read } from '@armada/organization-info';
import { LegalAgreementGate } from '@armada/ui-kit';
import { type ReactNode } from 'react';
import texts from 'virtual:legal-documents';

import type { LegalDocument } from '../gen/legal/v1/legal_document_pb';
import { OrganizationInfoSchema } from '../gen/organization/v1/organization_info_pb';
import { acceptAgreement, outstandingLegalDocuments } from '../ipc/legal';
import { licenceNotices } from './documents';

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

/** Renders the app once its user has accepted every current legal document that asks for it. */
export function AgreementGate({ children }: { children: ReactNode }) {
  return (
    <LegalAgreementGate
      applicationTitle={title}
      texts={texts}
      loadOutstanding={loadOutstanding}
      accept={accept}
      notices={licenceNotices}
    >
      {children}
    </LegalAgreementGate>
  );
}
