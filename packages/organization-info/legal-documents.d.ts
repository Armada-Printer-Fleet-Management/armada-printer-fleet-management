// The module the legalDocuments() Vite plugin provides.
declare module 'virtual:legal-documents' {
  /** Each legal document's text, keyed by the SHA-256 organization.json pins it to. */
  const texts: Readonly<Record<string, string>>;
  export default texts;
}
