import { startE2EServer } from "./server-lifecycle.mjs";

export default async function globalSetup() {
  await startE2EServer();
}
