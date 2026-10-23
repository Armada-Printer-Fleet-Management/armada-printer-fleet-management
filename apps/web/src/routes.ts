export const routePaths = {
  integration: {
    path: '/integration',
    label: 'Integration test',
    showInNav: true,
  },
  printSubmission: {
    path: '/prints/new',
    label: 'Submit a print',
    showInNav: true,
  },
  printJobStatus: {
    path: '/prints/:printJobId',
    label: 'Print job status',
    showInNav: false,
  },
} as const;
