import { requestFailure } from '@armada/api-client';
import type { LegalDocument } from '@armada/api-client/gen/legal/v1/legal_document_pb';
import { OrganizationInfoSchema } from '@armada/api-client/gen/organization/v1/organization_info_pb';
import { read } from '@armada/organization-info';
import { LegalAgreementGate } from '@armada/ui-kit';
import { type ReactNode, useCallback } from 'react';
import texts from 'virtual:legal-documents';

import { apiClient } from '../lib/api';
import { useAuth } from '../lib/auth-context';
import { licenceNotices } from './documents';

const { title } = read(OrganizationInfoSchema);

/**
 * Once someone is signed in, renders the app only after they accept every current legal document
 * that asks for acceptance. Signed out, the app renders as it is.
 */
export function AgreementGate({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <>{children}</>;
  // Keyed by the user, so signing in as someone else checks their agreements afresh.
  return (
    <SignedInGate key={user.profile.sub} subject={user.profile.sub}>
      {children}
    </SignedInGate>
  );
}

// TEMP: the request names its user, here the signed-in user's identity provider ID, until the
// server reads the user from the access token instead.
function SignedInGate({
  subject,
  children,
}: {
  subject: string;
  children: ReactNode;
}) {
  const loadOutstanding = useCallback(async () => {
    const response = await apiClient.agreements.listOutstandingLegalDocuments({
      userId: { value: subject },
    });
    return response.legalDocuments;
  }, [subject]);

  const accept = useCallback(
    async (document: LegalDocument) => {
      await apiClient.agreements.acceptAgreement({
        userId: { value: subject },
        kind: document.kind,
        effectiveDate: document.effectiveDate,
      });
    },
    [subject],
  );

  return (
    <LegalAgreementGate
      applicationTitle={title}
      texts={texts}
      loadOutstanding={loadOutstanding}
      accept={accept}
      notices={licenceNotices}
      classifyFailure={requestFailure}
    >
      {children}
    </LegalAgreementGate>
  );
}
