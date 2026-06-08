import { SimpleGrid, Box, Flex, Text, Progress, Badge, Heading } from "@chakra-ui/react";
import { GRADE_COLOR, DIMENSION_PLAIN, type AbiScore } from "../api";

const PROGRESS_SCHEME: Record<string, string> = {
  A: "green", B: "green", C: "yellow", D: "orange", F: "red",
};

export function DimensionCards({
  score,
  selected,
  onSelect,
}: {
  score: AbiScore;
  selected: string | null;
  onSelect: (key: string) => void;
}) {
  const entries = Object.entries(score.dimensions);
  return (
    <Box>
      <Heading size="sm" color="gray.700" mb={1}>
        Why this grade — the 5 things AI looks for
      </Heading>
      <Text fontSize="xs" color="gray.500" mb={3}>
        Each area below explains part of your score. Tap any card to see the proof behind it.
      </Text>
      <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 5 }} spacing={3}>
        {entries.map(([key, dim]) => {
          const active = selected === key;
          const plain = DIMENSION_PLAIN[key];
          return (
            <Box
              key={key}
              bg="white"
              borderWidth="2px"
              borderColor={active ? GRADE_COLOR[dim.grade] ?? "blue.400" : "gray.200"}
              rounded="lg"
              p={4}
              cursor="pointer"
              transition="all .15s"
              _hover={{ shadow: "md", transform: "translateY(-2px)" }}
              onClick={() => onSelect(key)}
            >
              <Text fontSize="sm" fontWeight="bold" color="gray.800" noOfLines={1}>
                {plain?.short ?? dim.label}
              </Text>
              <Text fontSize="xs" color="gray.500" minH="32px" noOfLines={2}>
                {plain?.question ?? dim.label}
              </Text>
              <Flex align="baseline" gap={2} mt={1}>
                <Text fontSize="2xl" fontWeight="bold">
                  {dim.score}
                </Text>
                <Badge colorScheme={PROGRESS_SCHEME[dim.grade] ?? "gray"}>{dim.grade}</Badge>
              </Flex>
              <Progress
                value={dim.score}
                size="sm"
                rounded="full"
                mt={2}
                colorScheme={PROGRESS_SCHEME[dim.grade] ?? "gray"}
              />
              <Text fontSize="xs" color="gray.400" mt={1}>
                tap for the evidence →
              </Text>
            </Box>
          );
        })}
      </SimpleGrid>
    </Box>
  );
}
