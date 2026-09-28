import { useEffect, useState } from "react";
import {
  Box, Container, Grid, Heading, Text, VStack, Flex, Spinner, Alert, AlertIcon,
  AlertTitle, AlertDescription,
} from "@chakra-ui/react";
import { api, type SiteDetail } from "./api";
import { ScoreHero } from "./components/ScoreHero";
import { DimensionCards } from "./components/DimensionCards";
import { Recommendations } from "./components/Recommendations";
import { EvidenceView } from "./components/EvidenceView";

/**
 * The paid deliverable: one customer's full AI Visibility report, unlocked by
 * their purchase grant (token in the URL). Same detail view as the internal
 * dashboard, minus the all-sites gallery and the live-run panel.
 */
export function BuyerReport({ token, onHome }: { token: string; onHome?: () => void }) {
  const [detail, setDetail] = useState<SiteDetail | null>(null);
  const [activeDim, setActiveDim] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .reportByToken(token)
      .then((d) => {
        setDetail(d);
        const dims = d.abi_score ? Object.keys(d.abi_score.dimensions) : [];
        setActiveDim(dims[0] ?? null);
      })
      .catch((e) => setError(String(e instanceof Error ? e.message : e)))
      .finally(() => setLoading(false));
  }, [token]);

  const isSample = token === "sample";

  return (
    <Box minH="100vh">
      <Box bg="gray.900" color="white" py={5} px={6} mb={6}>
        <Container maxW="5xl">
          <Flex justify="space-between" align="center" gap={4}>
            <Box>
              <Heading size="lg" cursor={onHome ? "pointer" : undefined} onClick={onHome}>
                AI Visibility Report
              </Heading>
              <Text color="gray.300" fontSize="sm">
                {isSample
                  ? "Sample report — this is what your full audit looks like."
                  : "Your full audit: scores, evidence, and prioritized fixes."}
              </Text>
            </Box>
            {onHome && (
              <Box
                as="button"
                onClick={onHome}
                color="gray.300"
                fontSize="sm"
                _hover={{ color: "white" }}
                whiteSpace="nowrap"
              >
                ← Back to home
              </Box>
            )}
          </Flex>
        </Container>
      </Box>

      <Container maxW="5xl" pb={16}>
        <VStack align="stretch" spacing={5}>
          {isSample && (
            <Alert status="info" rounded="md">
              <AlertIcon />
              This is a sample report. Run your own site from the home page to get your grade.
            </Alert>
          )}

          {error && (
            <Alert status="error" rounded="md" alignItems="flex-start">
              <AlertIcon />
              <Box>
                <AlertTitle>Report unavailable</AlertTitle>
                <AlertDescription fontSize="sm">{error}</AlertDescription>
              </Box>
            </Alert>
          )}

          {loading && (
            <Flex justify="center" py={20}>
              <Spinner size="xl" color="blue.500" />
            </Flex>
          )}

          {!loading && detail?.coverage?.low_coverage && detail.coverage.warning && (
            <Alert status="warning" rounded="md" alignItems="flex-start">
              <AlertIcon />
              <Box>
                <AlertTitle>Low crawl coverage</AlertTitle>
                <AlertDescription fontSize="sm">
                  {detail.coverage.warning} Scores below may understate this business.
                </AlertDescription>
              </Box>
            </Alert>
          )}

          {!loading && detail && detail.abi_score && (
            <>
              <ScoreHero site={detail} reportHref={api.reportDownloadUrl(token)} />
              <DimensionCards score={detail.abi_score} selected={activeDim} onSelect={setActiveDim} />
              <Grid templateColumns={{ base: "1fr", xl: "1fr 1fr" }} gap={5}>
                <Recommendations recs={detail.abi_score.top_recommendations} />
                {activeDim && detail.abi_score.dimensions[activeDim] && (
                  <EvidenceView dimension={detail.abi_score.dimensions[activeDim]} dimKey={activeDim} />
                )}
              </Grid>
            </>
          )}

          {!loading && detail && !detail.abi_score && (
            <Alert status="warning" rounded="md">
              <AlertIcon />
              This report has a profile but no ABI score yet.
            </Alert>
          )}
        </VStack>
      </Container>
    </Box>
  );
}
