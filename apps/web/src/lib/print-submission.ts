import {
  PrintJobStatus,
  PrintJobUploadError,
  type createApiClient,
} from '@armada/api-client';
import { FileType } from '@armada/api-client/gen/content_asset/v1/file_pb';
import type { PrintJobId } from '@armada/api-client/gen/id/v1/print_job_id_pb';

type PrintJobsApi = ReturnType<typeof createApiClient>['printJobs'];

export type SubmissionState =
  | {
      phase:
        | 'ready'
        | 'hashing'
        | 'creating'
        | 'slot'
        | 'uploading'
        | 'submitting'
        | 'checking';
    }
  | {
      phase:
        | 'failed-preparation'
        | 'failed-upload'
        | 'failed-submit'
        | 'unknown'
        | 'unknown-create';
      message: string;
    }
  | { phase: 'success' };

export function fileType(filename: string): FileType | undefined {
  if (/\.gcode$/i.test(filename)) return FileType.GCODE;
  if (/\.cgcode$/i.test(filename)) return FileType.CGCODE;
  return undefined;
}

export function validateFile(file: File | null): string | undefined {
  if (!file) return 'Choose a print file before submitting.';

  if (!fileType(file.name))
    return 'File type not supported. Upload a .gcode or .cgcode file.';

  if (file.size === 0) return 'The file is empty. Choose a file with content.';

  if (file.name.length > 255)
    return 'Filename is too long. Keep it under 255 characters.';

  if (/[<>:"/\\|?*]/.test(file.name))
    return 'Filename contains unsupported characters. Remove <>:"/\\|?* and try again.';

  if (Array.from(file.name).some((character) => character.charCodeAt(0) < 32))
    return 'Filename contains invalid characters. Use only standard letters, numbers, and symbols.';

  if (/[. ]$/.test(file.name))
    return 'Filename cannot end with a space or period.';

  if (
    /^(con|prn|aux|nul|com[1-9\u00b9\u00b2\u00b3]|lpt[1-9\u00b9\u00b2\u00b3])(\.|$)/i.test(
      file.name,
    )
  )
    return 'This filename is reserved by the system. Choose a different name.';

  return undefined;
}

function rpcMessage(error: unknown): string {
  if (!(error instanceof Error)) return 'An unexpected error occurred.';
  return error.message.replace(/https?:\/\/\S+/gi, '[address hidden]');
}

async function sha256(file: File): Promise<string> {
  if (!globalThis.crypto?.subtle) {
    throw new Error('File verification requires a secure connection (HTTPS).');
  }
  const digest = await globalThis.crypto.subtle.digest(
    'SHA-256',
    await file.arrayBuffer(),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('');
}

export class PrintSubmission {
  private state: SubmissionState = { phase: 'ready' };
  private jobId: PrintJobId | undefined;
  private digest = '';

  constructor(
    private readonly api: PrintJobsApi,
    private readonly file: File,
    private readonly notes: string,
    private readonly onChange: (state: SubmissionState) => void,
  ) {}

  private setState(state: SubmissionState): void {
    this.state = state;
    this.onChange(state);
  }

  async start(): Promise<void> {
    if (
      this.state.phase !== 'ready' &&
      this.state.phase !== 'failed-preparation'
    )
      return;
    this.setState({ phase: 'hashing' });
    try {
      this.digest = await sha256(this.file);
    } catch (error) {
      this.setState({
        phase: 'failed-preparation',
        message: rpcMessage(error),
      });
      return;
    }

    this.setState({ phase: 'creating' });
    try {
      const response = await this.api.createPrintJob({ userNotes: this.notes });
      if (!response.printJob?.id?.value)
        throw new Error('The server did not return a job ID.');
      this.jobId = response.printJob.id;
    } catch (error) {
      // The server may have created the draft even when its response was lost.
      this.setState({ phase: 'unknown-create', message: rpcMessage(error) });
      return;
    }
    await this.upload();
  }

  async retry(): Promise<void> {
    if (this.state.phase === 'failed-upload') await this.upload();
    else if (this.state.phase === 'failed-submit') await this.submit();
    else if (this.state.phase === 'unknown') await this.checkStatus();
  }

  private async upload(): Promise<void> {
    const jobId = this.jobId;
    const type = fileType(this.file.name);
    if (!jobId || !type)
      throw new Error('A draft and supported file are required.');
    this.setState({ phase: 'slot' });
    try {
      const response = await this.api.createPrintJobUpload({
        printJobId: jobId,
        metadata: {
          filename: this.file.name,
          sizeBytes: BigInt(this.file.size),
          sha256: this.digest,
          fileType: type,
        },
      });
      if (!response.slot?.uploadUrl)
        throw new Error('The server did not return an upload slot.');
      this.setState({ phase: 'uploading' });
      await this.api.uploadPrintJobFile(response.slot, this.file);
    } catch (error) {
      const detail =
        this.state.phase === 'uploading'
          ? error instanceof PrintJobUploadError
            ? error.message
            : 'The file upload could not be completed. Check your connection.'
          : rpcMessage(error);
      this.setState({ phase: 'failed-upload', message: detail });
      return;
    }
    await this.submit();
  }

  private async submit(): Promise<void> {
    const jobId = this.jobId;
    if (!jobId) throw new Error('A draft is required.');
    this.setState({ phase: 'submitting' });
    try {
      const { printJob } = await this.api.submitPrintJob({ printJobId: jobId });
      if (
        printJob?.id?.value !== jobId.value ||
        printJob.status !== PrintJobStatus.SUBMITTED
      ) {
        throw new Error('The server did not confirm the submitted job.');
      }
      this.setState({ phase: 'success' });
    } catch (error) {
      await this.checkStatus(rpcMessage(error));
    }
  }

  private async checkStatus(submitError?: string): Promise<void> {
    const jobId = this.jobId;
    if (!jobId) throw new Error('A draft is required.');
    this.setState({ phase: 'checking' });
    try {
      const { printJob } = await this.api.getPrintJob({ printJobId: jobId });
      if (
        !printJob ||
        !printJob.id?.value ||
        printJob.id.value !== jobId.value
      ) {
        throw new Error('The server did not return the expected job.');
      }
      if (printJob.status === PrintJobStatus.DRAFT) {
        this.setState({
          phase: 'failed-submit',
          message: submitError ?? 'The job is still a draft.',
        });
      } else if (
        printJob.status === PrintJobStatus.SUBMITTED ||
        printJob.status === PrintJobStatus.UNDER_REVIEW ||
        printJob.status === PrintJobStatus.APPROVED ||
        printJob.status === PrintJobStatus.REJECTED ||
        printJob.status === PrintJobStatus.ASSIGNED ||
        printJob.status === PrintJobStatus.PRINTING ||
        printJob.status === PrintJobStatus.FINISHED ||
        printJob.status === PrintJobStatus.COMPLETED ||
        printJob.status === PrintJobStatus.FAILED ||
        printJob.status === PrintJobStatus.CANCELLED
      ) {
        this.setState({ phase: 'success' });
      } else {
        throw new Error('The server returned an unexpected job status.');
      }
    } catch (error) {
      this.setState({ phase: 'unknown', message: rpcMessage(error) });
    }
  }
}
