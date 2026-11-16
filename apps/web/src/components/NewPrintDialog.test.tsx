import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import {
  FileDetails,
  NewPrintDialog,
  SubmissionFeedback,
} from './NewPrintDialog';

describe('new print form', () => {
  it('provides labeled file and notes controls and shows file details', () => {
    const form = renderToStaticMarkup(
      <NewPrintDialog open onClose={() => {}} />,
    );
    expect(form).toContain('id="print-file-label"');
    expect(form).toContain('aria-labelledby="print-file-label"');
    expect(form).toContain('id="print-file"');
    expect(form).toContain('for="print-notes"');
    expect(form).toContain('id="print-notes"');

    const details = renderToStaticMarkup(
      <FileDetails file={new File(['abc'], 'part.gcode')} />,
    );
    expect(details).toContain('part.gcode');
    expect(details).toContain('3 bytes');
  });

  it('exposes progress and errors to assistive technology', () => {
    const progress = renderToStaticMarkup(
      <SubmissionFeedback state={{ phase: 'uploading' }} />,
    );
    const error = renderToStaticMarkup(
      <SubmissionFeedback
        state={{ phase: 'failed-upload', message: 'Upload failed' }}
      />,
    );
    expect(progress).toContain('role="status"');
    expect(progress).toContain('Uploading');
    expect(error).toContain('role="alert"');
    expect(error).toContain('Upload failed');
  });
});
