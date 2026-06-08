import { useEffect, useState } from "react";
import {
  Box, Container, Grid, GridItem, Heading, Text, VStack, Flex, Spinner, Alert, AlertIcon,
  AlertTitle, AlertDescription,
} from "@chakra-ui/react";
import { api, type SiteSummary, type SiteDetail, type Benchmark } from "./api";
import { RunPanel } from "./components/RunPanel";
import { SitesGallery } from "./components/SitesGallery";
import { ScoreHero } from "./components/ScoreHero";
import { DimensionCards } from "./components/DimensionCards";
import { Recommendations } from "./components/Recommendations";
import { EvidenceView } from "./components/EvidenceView";
import { BenchmarkBar } from "./components/BenchmarkBar";

export default function App({
  initialUrl,
  initialDomain,
  onHome,
}: {
  initialUrl?: string;
  initialDomain?: string;
  onHome?: () => void;
} = {}) {
  const [sites, setSites] = useState<SiteSummary[]>([]);
  const [benchmark, setBenchmark] = useState<Benchmark | null>(null);
  const [selected, setSelected] = useState<string | null>(initialDomain ?? null);
  const [detail, setDetail] = useState<SiteDetail | null>(null);
  const [activeDim, setActiveDim] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshSites = async () => {
    const s = await api.sites();
    setSites(s);
    return s;
  };

  useEffect(() => {
    refreshSites().catch((e) => setError(String(e)));
    api.benchmark().then(setBenchmark).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    setError(null);
    api
      .site(selected)
      .then((d) => {
        setDetail(d);
        const dims = d.abi_score ? Object.keys(d.abi_score.dimensions) : [];
        setActiveDim(dims[0] ?? null);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [selected]);

  const onRunComplete = async (domain: string) => {
    await refreshSites();
    setSelected(domain);
  };

  return (
    <Box minH="100vh">
      <Box bg="gray.900" color="white" py={5} px={6} mb={6}>
        <Container maxW="7xl">
          <Flex justify="space-between" align="center" gap={4}>
            <Box>
              <Heading
                size="lg"
                cursor={onHome ? "pointer" : undefined}
                onClick={onHome}
              >
                AIVE · Agent Business Index
              </Heading>
              <Text color="gray.300" fontSize="sm">
                How understandable is a business to AI? Enter a URL or pick a scored site.
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

      <Container maxW="7xl" pb={16}>
        <Grid templateColumns={{ base: "1fr", lg: "320px 1fr" }} gap={6}>
          <GridItem>
            <VStack align="stretch" spacing={4}>
              <RunPanel onComplete={onRunComplete} initialUrl={initialUrl} />
              <SitesGallery sites={sites} selected={selected} onSelect={setSelected} />
            </VStack>
          </GridItem>

          <GridItem>
            <VStack align="stretch" spacing={5}>
              {benchmark && <BenchmarkBar bench={benchmark} />}

              {error && (
                <Alert status="error" rounded="md">
                  <AlertIcon />
                  {error}
                </Alert>
              )}

              {loading && (
                <Flex justify="center" py={20}>
                  <Spinner size="xl" color="blue.500" />
                </Flex>
              )}

              {!loading && !detail && (
                <Flex
                  direction="column"
                  align="center"
                  justify="center"
                  py={24}
                  bg="white"
                  rounded="xl"
                  borderWidth="1px"
                  borderColor="gray.200"
                  color="gray.500"
                >
                  <Text fontSize="lg">Select a site or run a new URL to see its ABI report.</Text>
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
                  <ScoreHero site={detail} reportHref={api.reportUrl(detail.domain)} />
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
                  This site has a profile but no ABI score yet.
                </Alert>
              )}
            </VStack>
          </GridItem>
        </Grid>
      </Container>
    </Box>
  );
}
