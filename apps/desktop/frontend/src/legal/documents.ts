import { read } from '@armada/organization-info';
import type { AboutLegalDocument } from '@armada/ui-kit';
import texts from 'virtual:legal-documents';

import {
  type LegalDocument,
  LegalDocumentKind,
} from '../gen/legal/v1/legal_document_pb';
import { OrganizationInfoSchema } from '../gen/organization/v1/organization_info_pb';

const LABELS: Record<LegalDocumentKind, string> = {
  [LegalDocumentKind.UNSPECIFIED]: 'Legal document',
  [LegalDocumentKind.LICENSE]: 'Licence',
  [LegalDocumentKind.TERMS_OF_SERVICE]: 'Terms of Service',
  [LegalDocumentKind.PRIVACY_POLICY]: 'Privacy Policy',
};

const { legalDocuments } = read(OrganizationInfoSchema);

/** Every legal document, labelled by kind and with its text, as the about box lists them. */
export const aboutLegalDocuments: AboutLegalDocument[] = legalDocuments.map(
  (document) => ({
    label: LABELS[document.kind],
    title: document.title,
    effectiveDate: document.effectiveDate,
    text: texts[document.sha256],
  }),
);

/** The licences, which the gate lists as notices beside the documents to accept. */
export const licenceNotices: LegalDocument[] = legalDocuments.filter(
  (document) => document.kind === LegalDocumentKind.LICENSE,
);
