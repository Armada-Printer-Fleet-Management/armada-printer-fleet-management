import {
  type JsonValue,
  type MessageInitShape,
  create,
  fromJson,
  toJson,
} from '@bufbuild/protobuf';
import {
  AcceptAgreementRequestSchema,
  AcceptAgreementResponseSchema,
  ListOutstandingLegalDocumentsResponseSchema,
} from '../gen/server/v1/agreement_service_pb';
import { waitForPywebviewIpc } from './pywebview';

declare global {
  interface PywebviewIpc {
    legal: {
      outstanding_legal_documents(): Promise<JsonValue>;
      accept_agreement(request: JsonValue): Promise<JsonValue>;
    };
  }
}

/** The legal documents this app's user has not accepted yet. */
export async function outstandingLegalDocuments() {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.legal.outstanding_legal_documents();
  return fromJson(ListOutstandingLegalDocumentsResponseSchema, raw);
}

/** Records the acceptance. The backend supplies the user, so user_id is left empty. */
export async function acceptAgreement(
  request: MessageInitShape<typeof AcceptAgreementRequestSchema>,
) {
  const ipc = await waitForPywebviewIpc();
  const raw = await ipc.legal.accept_agreement(
    toJson(
      AcceptAgreementRequestSchema,
      create(AcceptAgreementRequestSchema, request),
    ),
  );
  return fromJson(AcceptAgreementResponseSchema, raw);
}
