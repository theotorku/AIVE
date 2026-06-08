import { Box, Flex, Heading, Text, Badge, Button, HStack, Stat, StatLabel, StatNumber } from "@chakra-ui/react";
import { GRADE_COLOR, GRADE_MEANING, type SiteDetail } from "../api";

function CrawlStatus({ site }: { site: SiteDetail }) {
  const cov = site.coverage;
  const pages = cov?.final_page_count ?? cov?.meaningful_pages_found ?? site.profile.source_pages?.length ?? 0;
  const incomplete = !!cov?.low_coverage;
  return (
    <Badge
      colorScheme={incomplete ? "orange" : "green"}
      variant="subtle"
      fontSize="sm"
      px={2}
      py={1}
      rounded="md"
    >
      {incomplete ? "⚠ Partial crawl" : "✓ Full crawl"} · {pages} page{pages === 1 ? "" : "s"} analyzed
    </Badge>
  );
}

export function ScoreHero({ site, reportHref }: { site: SiteDetail; reportHref: string }) {
  const score = site.abi_score;
  const profile = site.profile;
  if (!score) return null;
  const color = GRADE_COLOR[score.grade] ?? "gray.500";
  const conf = site.confidence?.average_confidence;

  return (
    <Box bg="white" borderWidth="1px" borderColor="gray.200" rounded="xl" p={6} shadow="sm">
      <Flex justify="space-between" align="flex-start" gap={6} wrap="wrap">
        <Box flex="1" minW="240px">
          <Heading size="lg">{profile.business_name || site.domain}</Heading>
          <Text color="gray.500" mt={1}>
            {site.domain} · {profile.industry || "industry n/a"}
          </Text>
          <Text mt={3} fontSize="md" fontWeight="medium" color="gray.800">
            {GRADE_MEANING[score.grade] ?? score.grade_label}
          </Text>
          <HStack mt={3} spacing={3} wrap="wrap">
            <CrawlStatus site={site} />
            <Button as="a" href={reportHref} colorScheme="blue" size="sm">
              Download report
            </Button>
          </HStack>
        </Box>

        <Flex direction="column" align="center" bg={color} color="white" rounded="lg" px={8} py={5} minW="150px">
          <Text fontSize="6xl" fontWeight="extrabold" lineHeight="1">
            {score.grade}
          </Text>
          <Text fontSize="lg" fontWeight="semibold">
            ABI {score.overall}
          </Text>
          <Text fontSize="sm" opacity={0.9}>
            {score.grade_label}
          </Text>
        </Flex>
      </Flex>

      <HStack mt={5} spacing={8} divider={<Box borderLeftWidth="1px" borderColor="gray.200" h="32px" />} wrap="wrap">
        <Stat>
          <StatLabel color="gray.500">Services</StatLabel>
          <StatNumber fontSize="xl">{profile.services?.length ?? 0}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel color="gray.500">FAQs</StatLabel>
          <StatNumber fontSize="xl">{profile.faqs?.length ?? 0}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel color="gray.500">Trust signals</StatLabel>
          <StatNumber fontSize="xl">{profile.trust_signals?.length ?? 0}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel color="gray.500">schema.org</StatLabel>
          <StatNumber fontSize="xl">
            <Badge colorScheme={profile.structured_data?.schema_org_detected ? "green" : "gray"}>
              {profile.structured_data?.schema_org_detected ? "yes" : "no"}
            </Badge>
          </StatNumber>
        </Stat>
        {conf != null && (
          <Stat>
            <StatLabel color="gray.500">Extraction confidence</StatLabel>
            <StatNumber fontSize="xl">{conf}</StatNumber>
          </Stat>
        )}
      </HStack>
    </Box>
  );
}
