import { routePaths } from '../routes';

export function HelpPage() {
  return <h1 className="p-8 text-3xl font-bold">{routePaths.help.label}</h1>;
}
