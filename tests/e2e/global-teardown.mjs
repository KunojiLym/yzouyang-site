import { stopE2EServer } from "./server-lifecycle.mjs";

export default async function globalTeardown() {
  await stopE2EServer();
}
