import { useEffect, useState } from "react";
import { Box, Flex, Spinner, Text } from "@chakra-ui/react";
import { Landing } from "./Landing";
import { BuyerReport } from "./BuyerReport";
import App from "./App";
import { api } from "./api";

const ADMIN_SECRET = import.meta.env.VITE_ADMIN_SECRET ?? "admin";

/** Reset the URL to the bare landing page (drops query params). */
function goHome() {
  window.history.replaceState({}, "", window.location.pathname);
  window.location.reload();
}

/**
 * Top-level router (query-param based, no router dependency):
 *   ?report=<token>   → buyer's full report (or the public sample)
 *   ?session_id=<id>  → verify Stripe payment, then swap to ?report=<token>
 *   ?admin=<secret>   → internal dashboard (gallery + live runs)
 *   (default)         → marketing landing + free teaser
 */
export default function Root() {
  const params = new URLSearchParams(window.location.search);
  const reportToken = params.get("report");
  const sessionId = params.get("session_id");
  const admin = params.get("admin");

  const [verifyError, setVerifyError] = useState<string | null>(null);

  // After Stripe redirect: exchange the session for a report grant, then
  // rewrite the URL to the durable ?report=<token> link.
  useEffect(() => {
    if (!sessionId) return;
    api
      .verifyCheckout(sessionId)
      .then(({ token }) => {
        window.location.replace(`${window.location.pathname}?report=${token}`);
      })
      .catch((e) => setVerifyError(String(e instanceof Error ? e.message : e)));
  }, [sessionId]);

  if (sessionId) {
    return (
      <Flex direction="column" align="center" justify="center" minH="100vh" gap={4}>
        {verifyError ? (
          <Box textAlign="center" px={6}>
            <Text fontSize="lg" fontWeight="bold" mb={2}>
              We couldn't confirm your payment.
            </Text>
            <Text color="gray.600">{verifyError}</Text>
            <Text mt={4} as="button" color="blue.500" onClick={goHome}>
              ← Back to home
            </Text>
          </Box>
        ) : (
          <>
            <Spinner size="xl" color="blue.500" />
            <Text color="gray.600">Confirming your payment and unlocking your report…</Text>
          </>
        )}
      </Flex>
    );
  }

  if (reportToken) {
    return <BuyerReport token={reportToken} onHome={goHome} />;
  }

  if (admin && admin === ADMIN_SECRET) {
    return <App onHome={goHome} />;
  }

  return (
    <Landing
      onSample={() => {
        window.location.assign(`${window.location.pathname}?report=sample`);
      }}
    />
  );
}
