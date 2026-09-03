// Every attempt to spend a token gets a line in the compliance audit log
// before the client is allowed to call out to the payments API. In
// production this is a write to the shared ledger service; here it's a
// fixed, small delay standing in for that round trip.
export async function recordAttempt(clientId: string): Promise<void> {
  await new Promise<void>((resolve) => setTimeout(resolve, 5));
}
