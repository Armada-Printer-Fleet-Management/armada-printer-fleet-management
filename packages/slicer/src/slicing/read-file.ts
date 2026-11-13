/**
 * Reads a file served beside the app, on the page or in a worker. fetch() refuses file:// URLs,
 * which the desktop app loads from, so it falls back to XMLHttpRequest, which still reads them.
 */
export async function readText(url: string): Promise<string> {
  return new TextDecoder().decode(await readBytes(url));
}

export async function readBytes(url: string): Promise<Uint8Array> {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    return new Uint8Array(await response.arrayBuffer());
  } catch {
    return new Promise((resolve, reject) => {
      const request = new XMLHttpRequest();
      request.open('GET', url);
      request.responseType = 'arraybuffer';
      request.onload = () =>
        // A file:// read reports status 0 on success.
        request.status === 0 || request.status === 200
          ? resolve(new Uint8Array(request.response as ArrayBuffer))
          : reject(new Error(`Could not read ${url}: ${request.status}`));
      request.onerror = () => reject(new Error(`Could not read ${url}`));
      request.send();
    });
  }
}
