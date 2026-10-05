import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from './card';

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
    ? `${version.major}.${version.minor}.${version.maintenance}${version.postfix ? `-${version.postfix}` : ''}`
    : 'unavailable';

  return (
    <Card className="w-full max-w-xl">
      <CardHeader>
        <CardTitle>{organization.title}</CardTitle>
        <CardDescription className="text-foreground/70">
          {organization.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <dl className="grid gap-4 text-sm">
          <div className="grid grid-cols-[5rem_minmax(0,1fr)] gap-x-4">
            <dt className="font-medium text-foreground/70">Version</dt>
            <dd>{versionText}</dd>
          </div>
          <div className="grid grid-cols-[5rem_minmax(0,1fr)] gap-x-4">
            <dt className="font-medium text-foreground/70">License</dt>
            <dd>{organization.license}</dd>
          </div>
          <div className="grid grid-cols-[5rem_minmax(0,1fr)] gap-x-4">
            <dt className="font-medium text-foreground/70">Source</dt>
            <dd className="min-w-0">
              <a
                className="break-all text-primary underline-offset-4 hover:underline"
                href={organization.repositoryUrl}
              >
                {organization.repositoryUrl}
              </a>
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
