import { Box, Flex, Text, HStack, Stat, StatLabel, StatNumber, Badge } from "@chakra-ui/react";
import type { Benchmark } from "../api";

export function BenchmarkBar({ bench }: { bench: Benchmark }) {
  const b = bench.benchmark;
  return (
    <Box bg="white" borderWidth="1px" borderColor="gray.200" rounded="xl" p={4} shadow="sm">
      <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
        <HStack spacing={6} wrap="wrap">
          <Stat>
            <StatLabel color="gray.500" fontSize="xs">Industry avg ABI ({bench.sites_scored} sites)</StatLabel>
            <StatNumber fontSize="2xl">{b.average_abi}</StatNumber>
          </Stat>
          <Stat>
            <StatLabel color="gray.500" fontSize="xs">Range</StatLabel>
            <StatNumber fontSize="lg">{b.lowest_abi}–{b.highest_abi}</StatNumber>
          </Stat>
        </HStack>
        <HStack spacing={2}>
          {Object.entries(b.grade_distribution).map(([g, n]) => (
            <Badge key={g} colorScheme={g === "A" || g === "B" ? "green" : g === "C" ? "yellow" : g === "D" ? "orange" : "red"}>
              {g}: {n}
            </Badge>
          ))}
        </HStack>
      </Flex>
      <Text fontSize="xs" color="gray.500" mt={3}>
        Most common gaps:{" "}
        {b.common_weaknesses.slice(0, 3).map(([c, n]) => `${c} (${n})`).join(" · ")}
      </Text>
    </Box>
  );
}
