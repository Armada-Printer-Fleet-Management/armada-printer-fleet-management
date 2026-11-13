import type { MessageInitShape } from '@bufbuild/protobuf';
import type { Client } from '@connectrpc/connect';
import {
  AcceptAgreementRequestSchema,
  AgreementService,
  ListOutstandingLegalDocumentsRequestSchema,
} from './gen/server/v1/agreement_service_pb';

type AgreementRpcClient = Pick<
  Client<typeof AgreementService>,
  'listOutstandingLegalDocuments' | 'acceptAgreement'
>;

export function createAgreementApi(client: AgreementRpcClient) {
  return {
    listOutstandingLegalDocuments: (
      request: MessageInitShape<
        typeof ListOutstandingLegalDocumentsRequestSchema
      >,
    ) => client.listOutstandingLegalDocuments(request),
    acceptAgreement: (
      request: MessageInitShape<typeof AcceptAgreementRequestSchema>,
    ) => client.acceptAgreement(request),
  };
}
