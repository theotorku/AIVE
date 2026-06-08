import { Box, Heading, Flex, Text, Badge, VStack, UnorderedList, ListItem } from "@chakra-ui/react";
import { GRADE_COLOR, DIMENSION_PLAIN, type Dimension } from "../api";

export function EvidenceView({ dimension, dimKey }: { dimension: Dimension; dimKey?: string }) {
  const plain = dimKey ? DIMENSION_PLAIN[dimKey] : undefined;
  return (
    <Box bg="white" borderWidth="1px" borderColor="gray.200" rounded="xl" p={5} shadow="sm">
      <Flex justify="space-between" align="baseline" mb={1}>
        <Heading size="md">{plain?.short ?? dimension.label} — the proof</Heading>
        <Text fontWeight="bold" color={GRADE_COLOR[dimension.grade] ?? "gray.600"}>
          {dimension.score}/100 · {dimension.grade}
        </Text>
      </Flex>
      <Text fontSize="sm" color="gray.500" mb={3}>
        {plain?.question ?? "What the score is based on, with the evidence we found."}
      </Text>
      <VStack align="stretch" spacing={0} divider={<Box borderTopWidth="1px" borderColor="gray.100" />}>
        {dimension.criteria.map((c) => {
          const full = c.ratio >= 1;
          return (
            <Box key={c.name} py={3}>
              <Flex justify="space-between" align="center">
                <Text fontWeight="semibold" fontSize="sm">
                  {c.name}
                </Text>
                <Badge colorScheme={full ? "green" : c.ratio > 0 ? "yellow" : "red"}>
                  {c.earned}/{c.max}
                </Badge>
              </Flex>
              <Text fontSize="sm" color="gray.600" mt={1}>
                {c.rationale}
              </Text>
              {c.evidence?.length > 0 && (
                <UnorderedList fontSize="xs" color="gray.500" mt={1} spacing={0}>
                  {c.evidence.map((e, i) => (
                    <ListItem key={i}>{e}</ListItem>
                  ))}
                </UnorderedList>
              )}
              {c.recommendation && (
                <Text fontSize="sm" color="blue.600" mt={1}>
                  ▸ {c.recommendation}
                </Text>
              )}
            </Box>
          );
        })}
      </VStack>
    </Box>
  );
}
