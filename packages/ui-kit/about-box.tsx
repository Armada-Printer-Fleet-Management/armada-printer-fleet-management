export interface AboutBoxProps {
  organization: {
    title: string;
    description: string;
    license: string;
    repositoryUrl: string;
  };
  version?: {
    major: number;
    minor: number;
    maintenance: number;
    postfix?: string;
  };
}

export function AboutBox({ organization, version }: AboutBoxProps) {
  const versionText = version
    ? `${version.major}.${version.minor}.${version.maintenance}${version.postfix ? `-${version.postfix}` : ""}`
    : "unavailable";

  return (
    <section>
      <h2>{organization.title}</h2>
      <p>{organization.description}</p>
      <dl>
        <dt>Version</dt>
        <dd>{versionText}</dd>
        <dt>License</dt>
        <dd>{organization.license}</dd>
        <dt>Source</dt>
        <dd>
          <a href={organization.repositoryUrl}>{organization.repositoryUrl}</a>
        </dd>
      </dl>
    </section>
  );
}