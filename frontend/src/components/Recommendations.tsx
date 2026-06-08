import { Box, Heading, Flex, Text, VStack } from "@chakra-ui/react";
import type { Recommendation } from "../api";

export function Recommendations({ recs }: { recs: Recommendation[] }) {
  const top3 = recs.slice(0, 3);
  return (
    <Box bg="white" borderWidth="1px" borderColor="gray.200" rounded="xl" p={5} shadow="sm">
      <Heading size="md" mb={1}>
        Your top 3 fixes
      </Heading>
      <Text color="gray.500" fontSize="sm" mb={4}>
        Do these first — they raise your ABI score the most.
      </Text>
      {top3.length === 0 ? (
        <Text color="gray.500">No high-impact gaps remain. 🎉</Text>
      ) : (
        <VStack align="stretch" spacing={3}>
          {top3.map((r) => (
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
                <Text fontSize="sm" color="gray.800">
                  {r.recommendation}
                </Text>
                <Text fontSize="xs" color="green.600" fontWeight="semibold" mt={1}>
                  +{r.impact} ABI points
                </Text>
              </Box>
            </Flex>
          ))}
        </VStack>
      )}
    </Box>
  );
}
