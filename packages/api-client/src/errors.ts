export class PrintJobUploadError extends Error {
  constructor(readonly status: number) {
    super(`Print job file upload failed with HTTP ${status}.`);
    this.name = 'PrintJobUploadError';
  }
}
