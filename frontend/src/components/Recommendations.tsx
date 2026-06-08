import { Box, Heading, Flex, Text, VStack } from "@chakra-ui/react";
import type { Recommendation } from "../api";

export function Recommendations({ recs }: { recs: Recommendation[] }) {
  return (
    <Box bg="white" borderWidth="1px" borderColor="gray.200" rounded="xl" p={5} shadow="sm">
      <Heading size="md" mb={1}>
        Priority recommendations
      </Heading>
      <Text color="gray.500" fontSize="sm" mb={4}>
        Ranked by ABI impact — the highest-leverage fixes first.
      </Text>
      {recs.length === 0 ? (
        <Text color="gray.500">No high-impact gaps remain. 🎉</Text>
      ) : (
        <VStack align="stretch" spacing={3}>
          {recs.map((r) => (
            <Flex key={r.priority} gap={3} align="flex-start">
              <Flex
                flex="0 0 28px"
                h="28px"
                rounded="full"
                bg="blue.500"
                color="white"
                align="center"
                justify="center"
                fontWeight="bold"
                fontSize="sm"
              >
                {r.priority}
              </Flex>
              <Box>
                <Text fontWeight="semibold" fontSize="sm">
                  {r.dimension_label} · {r.criterion}
                </Text>
                <Text fontSize="sm" color="gray.700">
                  {r.recommendation}
                </Text>
                <Text fontSize="xs" color="green.600" fontWeight="semibold" mt={1}>
                  ABI impact +{r.impact}
                </Text>
              </Box>
            </Flex>
          ))}
        </VStack>
      )}
    </Box>
  );
}
